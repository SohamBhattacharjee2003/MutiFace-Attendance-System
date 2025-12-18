import io
import os
import json
import base64
from datetime import datetime, timezone

from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
from pymongo import MongoClient
from dotenv import load_dotenv

from face_recognition.detector import FaceDetector
from face_recognition.embedder import Embedder
from face_recognition.recognizer import recognize

from routes.register import register_bp
from routes.auth import auth_bp

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()

app = Flask(__name__)

# Allow CORS from local frontend (localhost and 127.0.0.1)
CORS(
    app,
    resources={r"/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}},
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)

# Increase request size (base64 images can be large)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB

# Health check to validate connectivity from frontend
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

# Register blueprints
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(register_bp)

# -----------------------------
# Initialize models
# -----------------------------
print("🔄 Initializing face detection and embedding models...")
try:
    detector = FaceDetector()
    print("✅ Face detector initialized")
except Exception as e:
    print(f"❌ Failed to initialize face detector: {e}")
    detector = None

try:
    embedder = Embedder()
    print("✅ Face embedder initialized")
except Exception as e:
    print(f"❌ Failed to initialize face embedder: {e}")
    embedder = None

# Embeddings directory
EMBED_PATH = "embeddings"
os.makedirs(EMBED_PATH, exist_ok=True)
print(f"📁 Embeddings directory: {EMBED_PATH}")

# -----------------------------
# MongoDB Connection
# -----------------------------
MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
print(f"Connecting to MongoDB: {MONGO_URI[:30]}...")  # Log connection (hide credentials)

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # Test the connection
    client.admin.command('ping')
    print("✅ MongoDB connection successful!")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    
db = client["attendance_db"]
attendance_col = db["attendance"]

# -----------------------------
# Predict Route
# -----------------------------
@app.route("/predict", methods=["POST"])
def predict():
    # Check if models are initialized
    if detector is None or embedder is None:
        return jsonify({"error": "Face recognition models not initialized"}), 500
    
    data = request.get_json(silent=True) or {}
    img_b64 = data.get("image")

    if not img_b64:
        return jsonify({"error": "No image provided"}), 400

    try:
        # Decode base64 image
        header, encoded = img_b64.split(",", 1)
        img_bytes = base64.b64decode(encoded)
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    except Exception as e:
        print(f"❌ Error decoding image: {e}")
        return jsonify({"error": "Invalid image data"}), 400

    try:
        boxes, probs, faces = detector.detect(img)
    except Exception as e:
        print(f"❌ Error detecting faces: {e}")
        return jsonify({"error": "Face detection failed"}), 500
    
    results = []

    for i, face in enumerate(faces):
        try:
            emb = embedder.get_embedding(face)
            if emb is None:
                continue
        except Exception as e:
            print(f"❌ Error getting embedding: {e}")
            continue

        name, dist = recognize(emb)
        confidence = max(0, (1.05 - dist) / 1.05)

        x1, y1, x2, y2 = boxes[i]

        # Remove confidence threshold - save all detections except "Unknown"
        is_known = name != "Unknown"

        results.append({
            "name": name,
            "distance": float(dist),
            "confidence": round(float(confidence), 2),
            "box": [int(x1), int(y1), int(x2), int(y2)],
            "isKnown": is_known
        })

        # Save attendance for all recognized names (no confidence threshold)
        if is_known:
            try:
                # Check if attendance already marked today
                today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
                existing = attendance_col.find_one({
                    "name": name,
                    "time": {"$gte": today_start}
                })
                
                if not existing:
                    result = attendance_col.insert_one({
                        "name": name,
                        "time": datetime.now(timezone.utc),
                        "confidence": float(confidence)
                    })
                    print(f"✅ Attendance saved: {name} (confidence: {confidence:.2f}) - ID: {result.inserted_id}")
            except Exception as e:
                print(f"❌ Failed to save attendance: {e}")

    return jsonify({"results": results})

# -----------------------------
# Attendance Records Route
# -----------------------------
@app.route("/attendance", methods=["GET"])
def get_attendance():
    try:
        records = list(attendance_col.find({}, {"_id": 0}))
        print(f"✅ Fetched {len(records)} attendance records")
        # Convert datetime to string for JSON serialization
        for record in records:
            if 'time' in record and hasattr(record['time'], 'isoformat'):
                record['time'] = record['time'].isoformat()
        return jsonify(records)
    except Exception as e:
        print(f"❌ Error fetching attendance: {e}")
        return jsonify([]), 200

# -----------------------------
# Clear Attendance Records
# -----------------------------
@app.route("/attendance/clear", methods=["DELETE"])
def clear_attendance():
    """
    Clear all attendance records from the database.
    """
    try:
        result = attendance_col.delete_many({})
        print(f"🗑️ Cleared {result.deleted_count} attendance records")
        return jsonify({
            "status": "success",
            "message": f"Cleared {result.deleted_count} records"
        }), 200
    except Exception as e:
        print(f"❌ Error clearing attendance: {e}")
        return jsonify({"error": str(e)}), 500

# -----------------------------
# Get Attendance by Date
# -----------------------------
@app.route("/attendance/date/<date>", methods=["GET"])
def get_attendance_by_date(date):
    """
    Get attendance records for a specific date (YYYY-MM-DD format).
    """
    try:
        # Parse the date
        target_date = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        next_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_after = datetime(target_date.year, target_date.month, target_date.day + 1 if target_date.day < 31 else 1).replace(tzinfo=timezone.utc)
        
        records = list(attendance_col.find({
            "time": {
                "$gte": next_day,
                "$lt": day_after
            }
        }, {"_id": 0}))
        
        # Convert datetime to string
        for record in records:
            if 'time' in record and hasattr(record['time'], 'isoformat'):
                record['time'] = record['time'].isoformat()
        
        print(f"✅ Fetched {len(records)} records for {date}")
        return jsonify(records)
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    except Exception as e:
        print(f"❌ Error fetching attendance by date: {e}")
        return jsonify({"error": str(e)}), 500

# -----------------------------
# Students List Route
# -----------------------------
@app.route("/students", methods=["GET"])
def get_students():
    try:
        # Try to get from MongoDB first
        students_col = db["students"]
        students_from_db = list(students_col.find({}, {"_id": 0, "name": 1, "samples": 1}))
        
        if students_from_db:
            return jsonify(students_from_db)
    except Exception as e:
        print(f"⚠️ Could not fetch from MongoDB: {e}")
    
    # Fallback to JSON files
    students = []
    embeddings_dir = "embeddings"
    if not os.path.exists(embeddings_dir):
        return jsonify([])

    for file in os.listdir(embeddings_dir):
        if not file.endswith(".json"):
            continue

        path = os.path.join(embeddings_dir, file)

        with open(path, "r") as f:
            data = json.load(f)

        students.append({
            "name": data.get("name"),
            "samples": len(data.get("embeddings", []))
        })

    return jsonify(students)

# -----------------------------
# Update Student (Add More Images) Route
# -----------------------------
@app.route("/update-student", methods=["POST"])
def update_student():
    """
    Add more images to an existing student's embeddings.
    Appends new embeddings to the existing JSON file.
    """
    data = request.get_json(force=True)
    
    name = data.get("name")
    images = data.get("images")
    
    if not name or not images:
        return jsonify({"error": "Name and images are required"}), 400
    
    # Check if student exists
    json_path = os.path.join(EMBED_PATH, f"{name}.json")
    if not os.path.exists(json_path):
        return jsonify({"error": f"Student '{name}' not found. Please register first."}), 404
    
    # Load existing embeddings
    try:
        with open(json_path, "r") as f:
            student_data = json.load(f)
        existing_embeddings = student_data.get("embeddings", [])
    except Exception as e:
        return jsonify({"error": f"Failed to load student data: {str(e)}"}), 500
    
    # Process new images and extract embeddings
    new_embeddings = []
    for img64 in images:
        try:
            # Decode base64 image
            header, encoded = img64.split(",", 1)
            img_bytes = base64.b64decode(encoded)
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            
            # Detect faces
            boxes, probs, faces = detector.detect(img)
            if not faces:
                print(f"⚠️ No face detected in image")
                continue
            
            # Get embedding for the first face
            emb = embedder.get_embedding(faces[0])
            if emb is not None:
                new_embeddings.append(emb.tolist())
            else:
                print(f"⚠️ Failed to extract embedding")
                
        except Exception as e:
            print(f"❌ Error processing image: {e}")
            continue
    
    if not new_embeddings:
        return jsonify({"error": "No valid faces detected in the provided images"}), 400
    
    # Append new embeddings to existing ones
    updated_embeddings = existing_embeddings + new_embeddings
    
    # Save updated embeddings to JSON file
    try:
        with open(json_path, "w") as f:
            json.dump(
                {"name": name, "embeddings": updated_embeddings},
                f
            )
        print(f"✅ Added {len(new_embeddings)} new embeddings for {name}")
    except Exception as e:
        return jsonify({"error": f"Failed to save embeddings: {str(e)}"}), 500
    
    # Update MongoDB record
    try:
        students_col = db["students"]
        students_col.update_one(
            {"name": name},
            {
                "$set": {
                    "samples": len(updated_embeddings),
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        print(f"✅ Updated MongoDB record for {name}")
    except Exception as e:
        print(f"⚠️ Failed to update MongoDB: {e}")
    
    return jsonify({
        "status": "success",
        "message": f"Successfully added {len(new_embeddings)} new image(s)",
        "new_samples": len(new_embeddings),
        "total_samples": len(updated_embeddings)
    }), 200

# -----------------------------
# Delete Student Route
# -----------------------------
@app.route("/students/<name>", methods=["DELETE"])
def delete_student(name):
    """
    Delete a student from the database and remove their embeddings file.
    """
    try:
        # Delete from MongoDB
        students_col = db["students"]
        result = students_col.delete_one({"name": name})
        
        # Delete embeddings file
        json_path = os.path.join(EMBED_PATH, f"{name}.json")
        if os.path.exists(json_path):
            os.remove(json_path)
        
        # Delete attendance records
        attendance_col.delete_many({"name": name})
        
        if result.deleted_count > 0 or os.path.exists(json_path):
            print(f"🗑️ Deleted student: {name}")
            return jsonify({"status": "success", "message": f"Student {name} deleted"}), 200
        else:
            return jsonify({"error": "Student not found"}), 404
    except Exception as e:
        print(f"❌ Error deleting student: {e}")
        return jsonify({"error": str(e)}), 500

# -----------------------------
# Get valid student names (with embeddings)
# -----------------------------
@app.route("/students/valid-names", methods=["GET"])
def get_valid_student_names():
    """
    Returns a list of student names that have embedding files.
    This helps the frontend filter out students without embeddings.
    """
    try:
        valid_names = []
        if os.path.exists(EMBED_PATH):
            for f in os.listdir(EMBED_PATH):
                if f.endswith(".json"):
                    valid_names.append(os.path.splitext(f)[0])
        
        return jsonify({"valid_names": valid_names}), 200
    except Exception as e:
        print(f"❌ Error getting valid student names: {e}")
        return jsonify({"valid_names": []}), 200

# -----------------------------
# Delete students missing embeddings
# -----------------------------
@app.route("/students/delete-missing", methods=["POST"])
def delete_missing_students():
    """
    Delete students from the database whose embedding JSON file is not present
    in the `embeddings` directory. Also removes attendance records for those
    students. Returns a summary of deleted student names and counts.
    """
    try:
        students_col = db["students"]
    except Exception as e:
        print(f"❌ Could not access students collection: {e}")
        return jsonify({"error": "database unavailable"}), 500

    try:
        # Get list of student names from the DB
        db_students = list(students_col.find({}, {"_id": 0, "name": 1}))
        db_names = [s.get("name") for s in db_students if s.get("name")]

        # Get list of embedding files
        embed_files = set()
        if os.path.exists(EMBED_PATH):
            for f in os.listdir(EMBED_PATH):
                if f.endswith(".json"):
                    embed_files.add(os.path.splitext(f)[0])

        # Find names present in DB but missing embedding file
        missing = [n for n in db_names if n not in embed_files]

        if not missing:
            return jsonify({"deleted": [], "message": "No missing students found"}), 200

        # Delete students from students collection
        del_result = students_col.delete_many({"name": {"$in": missing}})

        # Also delete any attendance records for these names
        att_del_result = attendance_col.delete_many({"name": {"$in": missing}})

        summary = {
            "deleted_students": missing,
            "students_deleted_count": del_result.deleted_count,
            "attendance_deleted_count": att_del_result.deleted_count
        }

        print(f"🗑️ Deleted missing students: {missing}")
        return jsonify(summary), 200
    except Exception as e:
        print(f"❌ Error deleting missing students: {e}")
        return jsonify({"error": str(e)}), 500

# -----------------------------
# Run Server
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
