import os
import json
import base64
import io
from flask import Blueprint, request, jsonify
from PIL import Image
import numpy as np

from face_recognition.detector import FaceDetector
from face_recognition.embedder import Embedder

register_bp = Blueprint("register", __name__)

detector = FaceDetector()
embedder = Embedder()

EMBED_PATH = "embeddings/"
os.makedirs(EMBED_PATH, exist_ok=True)

@register_bp.route("/register-student", methods=["POST"])
def register_student():
    data = request.get_json()
    name = data.get("name")
    images = data.get("images")

    if not name or not images or len(images) < 5:
        return jsonify({"error": "Name & at least 5 images required"}), 400

    embeddings_list = []

    for img64 in images:
        try:
            header, encoded = img64.split(",", 1)
            img_bytes = base64.b64decode(encoded)
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

            boxes, probs, faces = detector.detect(img)
            if len(faces) == 0:
                continue

            face_np = faces[0]
            emb = embedder.get_embedding(face_np)

            if emb is not None:
                embeddings_list.append(emb.tolist())

        except Exception as e:
            print("Registration error:", e)
            continue

    if len(embeddings_list) == 0:
        return jsonify({"error": "No valid face detected"}), 400

    json.dump({"name": name, "embeddings": embeddings_list},
              open(os.path.join(EMBED_PATH, f"{name}.json"), "w"))

    return jsonify({"status": "success",
                    "message": f"{name} registered with {len(embeddings_list)} samples"})
