#!/bin/sh
# Prepare the mounted volume, then run the server.
#
# The volume starts EMPTY on a fresh deploy. Seed it with the calibrated thresholds so the
# first enrolment does not fall back to the hand-picked defaults — those numbers came from
# 2,880 impostor faces and are not something a running server can re-derive, because the
# impostor cohort is deliberately not shipped.
set -e

mkdir -p /data/models /data/data /data/logs /data/processed_dataset

if [ ! -f /data/models/arcface_thresholds.json ]; then
  echo "▸ First run — seeding calibrated gates into the volume"
  cp /srv/seed/arcface_thresholds.json /data/models/
fi

echo "▸ PresenceAI on :${PORT}"
echo "  state: /data  ($(du -sh /data 2>/dev/null | cut -f1))"

# One worker, on purpose. Liveness state, the vote counters and the hot-swapped model all
# live in this process's memory. With several workers the frames of a single face would be
# round-robined between them, and liveness and voting would silently never reach quorum.
exec gunicorn api:app \
  --bind "0.0.0.0:${PORT}" \
  --workers 1 \
  --threads 8 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
