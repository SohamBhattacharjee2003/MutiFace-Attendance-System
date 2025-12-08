import io
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import numpy as np
from datetime import datetime
import joblib
from pymongo import MongoClient
import os

from model.detector import FaceDetector
from model.embedder import Embedder

app = Flask(__name__)
CORS(app)

# -------------------------------
# LOAD MODELS
# -------------------------------
detector = FaceDetector()
embedder = Embedder()

CLASSIFIER_PATH = "model/face_classifier.pkl"
LABEL_ENCODER_PATH = "model/label_encoder.pkl"

try:
    clf = joblib.load(CLASSIFIER_PATH)
    le = joblib.load(LABEL_ENCODER_PATH)
    print("✅ Classifier + Label Encoder loaded")
except Exception as e:
    print("❌ Classifier not found. Train first.", e)
    clf, le = None, None


# -------------------------------
# DATABASE
# -------------------------------
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["attendance_db"]
attendance_col = db["attendance"]
users_col = db["users"]


# -------------------------------
# IMAGE DECODER
# -------------------------------
def decode_base64_image(img_b64):
    header, encoded = img_b64.split(",", 1) if "," in img_b64 else (None, img_b64)
    img_bytes = base64.b64decode(encoded)
    return Image.open(io.BytesIO(img_bytes)).convert("RGB")


# -------------------------------
# FACE RECOGNITION
# -------------------------------
@app.route("/predict", methods=["POST"])
def predict():
    global clf, le

    if clf is None:
        return jsonify({"error": "Classifier not loaded. Train model first!"}), 500

    data = request.get_json()
    img_b64 = data.get("image")

    if img_b64 is None:
        return jsonify({"error": "No image received"}), 400

    img = decode_base64_image(img_b64)

    # Use detector wrapper
    boxes, probs, faces = detector.detect_faces(img)

    if boxes is None:
        return jsonify({"results": []})

    results = []

    for i, face_img in enumerate(faces):
        face_np = np.array(face_img.resize((160, 160)))  # Resize for FaceNet
        embedding = embedder.get_embedding(face_np)

        # Predict
        pred = clf.predict([embedding])[0]
        name = le.inverse_transform([pred])[0]
        confidence = float(np.max(clf.predict_proba([embedding])[0]))

        x1, y1, x2, y2 = map(int, boxes[i])

        results.append({
            "name": name,
            "confidence": confidence,
            "box": [x1, y1, x2, y2]
        })

        # Save attendance
        if confidence > 0.60:
            attendance_col.insert_one({
                "name": name,
                "time": datetime.utcnow(),
                "confidence": confidence
            })

    return jsonify({"results": results})


# -------------------------------
# REGISTER A NEW STUDENT
# -------------------------------
@app.route("/register-student", methods=["POST"])
def register_student():
    data = request.get_json()
    name = data.get("name")
    images = data.get("images", [])

    if not name or len(images) == 0:
        return jsonify({"error": "Name and at least 1 image required"}), 400

    folder = f"dataset_small/train/{name}"
    os.makedirs(folder, exist_ok=True)

    for i, img64 in enumerate(images):
        img = decode_base64_image(img64)
        img.save(f"{folder}/{i+1}.jpg")

    users_col.insert_one({"name": name})
    return jsonify({"status": "success", "message": f"{name} registered. Please train model."})


# -------------------------------
# GET ATTENDANCE LOGS
# -------------------------------
@app.route("/attendance", methods=["GET"])
def get_attendance():
    records = list(attendance_col.find({}, {"_id": 0}))
    return jsonify(records)


# -------------------------------
# MAIN
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)
