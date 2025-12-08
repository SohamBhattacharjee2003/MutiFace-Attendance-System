# embedder.py
import torch
import numpy as np
from facenet_pytorch import InceptionResnetV1

class Embedder:
    def __init__(self):
        # load pretrained FaceNet model
        self.model = InceptionResnetV1(pretrained='vggface2').eval()

    def get_embedding(self, face_np):
        """
        face_np: numpy image (H,W,3)
        Returns: 512-d embedding
        """
        if face_np.ndim != 3:
            raise ValueError("Face must be HWC")

        # convert to tensor
        img = np.transpose(face_np, (2, 0, 1)) / 255.0  # CHW
        img_tensor = torch.tensor(img, dtype=torch.float32).unsqueeze(0)

        with torch.no_grad():
            embedding = self.model(img_tensor)

        return embedding.squeeze().numpy()
