import os
import json
import base64
import io
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify
from PIL import Image
from pymongo import MongoClient
from dotenv import load_dotenv

from face_recognition.detector import FaceDetector
from face_recognition.embedder import Embedder

load_dotenv()

register_bp = Blueprint(
    "register",
    __name__
)

detector = FaceDetector()
embedder = Embedder()

EMBED_PATH = "embeddings"
os.makedirs(EMBED_PATH, exist_ok=True)

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client["attendance_db"]
    students_col = db["students"]
    print("✅ MongoDB connected in register route")
except Exception as e:
    print(f"❌ MongoDB connection failed in register route: {e}")
    client = None
    students_col = None

@register_bp.route("/register", methods=["POST"])
def register_student():
    data = request.get_json(force=True)

    name = data.get("name")
    images = data.get("images")

    if not name:
        return jsonify({"error": "Name is required"}), 400
    
    if not images or len(images) < 5:
        return jsonify({"error": "At least 5 images are required"}), 400

    embeddings_list = []
    failed_images = 0

    for idx, img64 in enumerate(images):
        try:
            header, encoded = img64.split(",", 1)
            img_bytes = base64.b64decode(encoded)
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

            boxes, probs, faces = detector.detect(img)
            if not faces:
                print(f"⚠️ No face detected in image {idx + 1}")
                failed_images += 1
                continue

            emb = embedder.get_embedding(faces[0])
            if emb is not None:
                embeddings_list.append(emb.tolist())
                print(f"✅ Processed image {idx + 1}/{len(images)}")
            else:
                print(f"⚠️ Failed to get embedding for image {idx + 1}")
                failed_images += 1

        except Exception as e:
            print(f"❌ Error processing image {idx + 1}: {e}")
            failed_images += 1

    if not embeddings_list:
        return jsonify({"error": "No valid face detected in any image"}), 400
    
    if len(embeddings_list) < 3:
        return jsonify({"error": f"Only {len(embeddings_list)} valid faces detected. Need at least 3."}), 400

    # Save to JSON file (for embeddings)
    with open(os.path.join(EMBED_PATH, f"{name}.json"), "w") as f:
        json.dump(
            {"name": name, "embeddings": embeddings_list},
            f
        )

    # Save to MongoDB (for student records)
    if students_col is not None:
        try:
            # Check if student already exists
            existing = students_col.find_one({"name": name})
            
            if existing:
                # Update existing student
                students_col.update_one(
                    {"name": name},
                    {
                        "$set": {
                            "samples": len(embeddings_list),
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )
                print(f"✅ Updated student in MongoDB: {name}")
            else:
                # Insert new student
                students_col.insert_one({
                    "name": name,
                    "samples": len(embeddings_list),
                    "registered_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                })
                print(f"✅ Added new student to MongoDB: {name}")
        except Exception as e:
            print(f"❌ Failed to save student to MongoDB: {e}")

    return jsonify({
        "status": "success",
        "message": f"{name} registered with {len(embeddings_list)} samples"
    })
