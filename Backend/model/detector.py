# detector.py
from facenet_pytorch import MTCNN
from PIL import Image

class FaceDetector:
    def __init__(self):
        # detect multiple faces
        self.mtcnn = MTCNN(keep_all=True)

    def detect_faces(self, img):
        """
        Input: PIL image
        Output: boxes, probs, faces(list of PIL crops)
        """
        boxes, probs = self.mtcnn.detect(img)

        if boxes is None:
            return None, None, None

        faces = []
        for box in boxes:
            x1, y1, x2, y2 = map(int, box)
            face = img.crop((x1, y1, x2, y2))
            faces.append(face)

        return boxes, probs, faces

    def extract_face(self, img_path, required_size=(160, 160)):
        """Used only during training (single face expected)."""
        img = Image.open(img_path).convert("RGB")
        boxes, probs = self.mtcnn.detect(img)

        if boxes is None or len(boxes) == 0:
            return None

        x1, y1, x2, y2 = map(int, boxes[0])
        face = img.crop((x1, y1, x2, y2))
        face = face.resize(required_size)

        return face
