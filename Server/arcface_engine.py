"""
arcface_engine.py
Modern face-recognition engine: MTCNN/RetinaFace detection + ArcFace embeddings.

Backbone: InsightFace `buffalo_l`
    - detector    : det_10g (RetinaFace / SCRFD family, 5-point aligned)
    - recognition : w600k_r50  →  ArcFace ResNet-50, 512-d L2-normalized embeddings
      (Deng et al., "ArcFace: Additive Angular Margin Loss for Deep Face
       Recognition", CVPR 2019)

Two embedding paths:
    embed_faces(img)        full frame → detect + align + embed every face  (live/predict)
    embed_training_image(img)  one face image → single embedding, with a
                            detection-bypass fallback for pre-cropped datasets.

All embeddings are unit-L2-normalized so a linear SVM / cosine similarity is
directly meaningful.
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import cv2

_APP = None          # shared FaceAnalysis singleton (models load once)


def _normalize(v):
    v = np.asarray(v, dtype=np.float32).ravel()
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


class ArcFaceEngine:
    _instance = None

    def __init__(self, det_size=(640, 640)):
        from insightface.app import FaceAnalysis
        # only detection + recognition → faster (skip age/gender/landmark nets)
        self.app = FaceAnalysis(name="buffalo_l",
                                allowed_modules=["detection", "recognition"],
                                providers=["CPUExecutionProvider"])
        self.app.prepare(ctx_id=-1, det_size=det_size)
        self.rec = self.app.models["recognition"]      # ArcFaceONNX
        self.dim = 512

    # ── singleton accessor (so API + scripts share one loaded model) ─────────
    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = ArcFaceEngine()
        return cls._instance

    # ── live / predict: detect every face in a full frame ────────────────────
    def embed_faces(self, bgr):
        """
        Returns list of dicts: {box:[x1,y1,x2,y2], embedding:(512,), det_score}
        sorted left→right, for every detected face.
        """
        faces = self.app.get(bgr)
        out = []
        for f in faces:
            x1, y1, x2, y2 = f.bbox.astype(int).tolist()
            out.append({
                "box": [x1, y1, x2, y2],
                "embedding": _normalize(f.normed_embedding),
                "det_score": float(f.det_score),
            })
        out.sort(key=lambda d: d["box"][0])
        return out

    # ── training: one embedding per image (robust to pre-cropped faces) ──────
    def embed_training_image(self, bgr):
        """
        Best-quality path: detect + align the largest face.
        Fallback (pre-cropped datasets where detection fails): run the ArcFace
        recogniser directly on the 112×112-resized crop. Returns (512,) or None.
        """
        faces = self.app.get(bgr)
        if faces:
            f = max(faces, key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]))
            return _normalize(f.normed_embedding)
        return self.embed_precropped(bgr)

    def embed_precropped(self, bgr):
        """
        Fast path for images that are ALREADY tight face crops (e.g. VGGFace2):
        skip detection, run the ArcFace recogniser directly on the 112×112 resize.
        ~20× faster than the detect+align path. Returns (512,) or None.
        """
        try:
            aligned = cv2.resize(bgr, (112, 112))
            return _normalize(self.rec.get_feat(aligned))
        except Exception:
            return None
