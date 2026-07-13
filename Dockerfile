# PresenceAI — one image, one origin.
#
# Flask serves BOTH the API and the built React app, so the whole product is a single
# container on a single port. Two origins would mean CORS, two deploys, and a frontend
# calling "localhost", which on a student's phone means their own phone.
#
#   docker build -t presenceai .
#   docker run -p 8000:8000 -v presence-data:/data presenceai
#
# Everything that must survive a restart — enrolled students, the trained centroids,
# attendance CSVs, teacher accounts — lives under /data, which is a MOUNTED VOLUME. The
# image itself is disposable.

# ── 1. build the React app ───────────────────────────────────────────────────
FROM node:20-slim AS frontend
WORKDIR /app
COPY Frontend/package*.json ./
RUN npm ci --no-audit --no-fund
COPY Frontend/ ./
RUN npm run build


# ── 2. the server ────────────────────────────────────────────────────────────
FROM python:3.12-slim

# opencv needs libGL even in headless builds; curl is for the healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 libglib2.0-0 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv

COPY Server/requirements.txt .
# opencv-python pulls a GUI stack we cannot use on a server; the headless build is the
# same library without it.
RUN sed -i 's/^opencv-python==/opencv-python-headless==/' requirements.txt \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir "uvicorn==0.38.0" "a2wsgi==1.10.10" "gunicorn==23.0.0"

# Bake the ArcFace + RetinaFace weights (~325 MB) INTO the image. Otherwise the container
# downloads them on every cold start, which turns a restart into a two-minute outage.
RUN python -c "\
from insightface.app import FaceAnalysis; \
FaceAnalysis(name='buffalo_l', allowed_modules=['detection','recognition','landmark_2d_106'], \
             providers=['CPUExecutionProvider']).prepare(ctx_id=-1, det_size=(640,640))"

COPY Server/api.py Server/arcface_engine.py Server/liveness.py Server/trainer.py \
     Server/classes.py Server/report.py ./
COPY --from=frontend /app/dist ./static

# The calibrated gates ship with the image. They were derived from 2,880 impostor faces —
# a research cohort of ~300 MB that production has no reason to carry, since the only thing
# it was ever needed for is choosing these two numbers.
COPY Server/models/arcface_thresholds.json ./seed/

ENV FRONTEND_DIST=/srv/static \
    STATE_DIR=/data \
    PORT=8000 \
    HOST=0.0.0.0 \
    PYTHONUNBUFFERED=1 \
    # ONNX Runtime grabs every core it can see; on a small VM that starves everything else
    OMP_NUM_THREADS=2 \
    ORT_NUM_THREADS=2

COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

VOLUME ["/data"]
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD curl -fsS http://localhost:8000/api/health || exit 1

ENTRYPOINT ["docker-entrypoint.sh"]
