from mtcnn import MTCNN
from PIL import Image
import numpy as np

class FaceDetector:
    def __init__(self):
        self.detector = MTCNN()

    def detect(self, img):
        img_np = np.array(img)
        detections = self.detector.detect_faces(img_np)

        boxes, probs, faces = [], [], []

        for det in detections:
            x, y, w, h = det["box"]
            x1, y1 = max(0, x), max(0, y)
            x2, y2 = x1 + w, y1 + h

            boxes.append([x1, y1, x2, y2])
            probs.append(det.get("confidence", 1.0))

            face = img.crop((x1, y1, x2, y2))
            face = face.resize((112, 112))  # ArcFace standard
            faces.append(face)

        return boxes, probs, faces
