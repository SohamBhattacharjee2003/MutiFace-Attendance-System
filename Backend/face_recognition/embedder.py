import numpy as np
from insightface.app import FaceAnalysis

class Embedder:
    def __init__(self):
        self.model = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        self.model.prepare(ctx_id=0, det_size=(224, 224))

    def get_embedding(self, face_img):
        # PIL → numpy
        img = np.array(face_img)

        # RGB → BGR
        img = img[:, :, ::-1]

        faces = self.model.get(img)
        if len(faces) == 0:
            return None

        emb = faces[0].embedding

        # L2 normalize
        emb = emb / np.linalg.norm(emb)

        return emb
