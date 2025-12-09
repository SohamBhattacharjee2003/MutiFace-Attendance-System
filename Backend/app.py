import io, base64, os
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
from datetime import datetime
import numpy as np
from pymongo import MongoClient
from dotenv import load_dotenv

from face_recognition.detector import FaceDetector
from face_recognition.embedder import Embedder
from face_recognition.recognizer import recognize

from routes.register import register_bp

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()

app = Flask(__name__)
CORS(app)

app.register_blueprint(register_bp)

# -----------------------------
# Initialize models
# -----------------------------
detector = FaceDetector()
embedder = Embedder()

# -----------------------------
# MongoDB Connection (Atlas)
# -----------------------------
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["attendance_db"]
attendance_col = db["attendance"]

# -----------------------------
# Predict Route
# -----------------------------
@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    img_b64 = data.get("image")

    header, encoded = img_b64.split(",", 1)
    img_bytes = base64.b64decode(encoded)
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    boxes, probs, faces = detector.detect(img)
    results = []

    for i, face in enumerate(faces):
        emb = embedder.get_embedding(face)
        if emb is None:
            continue

        name, dist = recognize(emb)
        confidence = max(0, (1.05 - dist) / 1.05)

        x1, y1, x2, y2 = boxes[i]

        results.append({
            "name": name,
            "distance": float(dist),
            "confidence": round(float(confidence), 2),
            "box": [x1, y1, x2, y2]
        })

        if name != "Unknown" and confidence > 0.55:
            attendance_col.insert_one({
                "name": name,
                "time": datetime.utcnow(),
                "confidence": float(confidence)
            })

    return jsonify({"results": results})

# -----------------------------
# Attendance Route (Fixes 404)
# -----------------------------
@app.route("/attendance", methods=["GET"])
def get_attendance():
    records = list(attendance_col.find({}, {"_id": 0}))
    return jsonify(records)

# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
