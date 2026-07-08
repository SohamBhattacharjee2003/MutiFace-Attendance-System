"""
api.py
Flask REST API — web backend for the Presence AI frontend, wrapping the existing
dlib `face_recognition` (128-d) pipeline.

It reuses the *same* artifacts the CLI scripts produce:
    models/classifier.pkl        (SVM/KNN pipeline from train_classifier.py)
    models/label_encoder.pkl
    processed_dataset/<name>/     (training images — Register/Update write here)
    logs/attendance_YYYY-MM-DD.csv
    data/users.json              (web app accounts — created on first signup)

Endpoints (contract expected by the React frontend on :5173):

    Auth
    POST   /api/auth/signup      {name,email,password}  -> {token, user}
    POST   /api/auth/login       {email,password}       -> {token, user}
    GET    /api/auth/verify      (Bearer)               -> {valid, user}
    GET    /api/auth/me          (Bearer)               -> {user}

    Face / students
    POST   /predict             {image}                 -> {results:[{name,confidence,box,isKnown}]}
    POST   /register            {name,images}           -> {status, samples}
    POST   /update-student      {name,images}           -> {status, total_samples}
    GET    /students                                    -> [{name, samples}]
    GET    /students/valid-names                        -> {valid_names:[...]}
    DELETE /students/<name>                             -> {status}

    Attendance
    GET    /attendance                                  -> [{name, time, confidence, camera}]
    DELETE /attendance/clear                            -> {status}

    GET    /health                                      -> {status, model_loaded}

Run (from the Server/ directory):
    python api.py                     # http://127.0.0.1:5000
"""

import io
import os
import csv
import glob
import base64
import shutil
import threading
from datetime import datetime

import numpy as np
import joblib
import face_recognition
from PIL import Image
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

# ── Config (mirrors scripts/attendance.py) ────────────────────────────────────
MODELS_DIR           = "models"
CLASSIFIER_FILE      = os.path.join(MODELS_DIR, "classifier.pkl")          # dlib (legacy)
LABEL_ENC_FILE       = os.path.join(MODELS_DIR, "label_encoder.pkl")
ARCFACE_CLF_FILE     = os.path.join(MODELS_DIR, "arcface_classifier.pkl")  # ArcFace (primary)
ARCFACE_LE_FILE      = os.path.join(MODELS_DIR, "arcface_label_encoder.pkl")
ARCFACE_CENTROIDS    = os.path.join(MODELS_DIR, "arcface_centroids.pkl")
ARCFACE_COS_THRESHOLD = 0.32   # cosine sim to identity centroid; below → "Unknown"
DATASET_DIR          = "processed_dataset"   # generate_encodings.py reads this
LOGS_DIR             = "logs"
DATA_DIR             = "data"
USERS_FILE           = os.path.join(DATA_DIR, "users.json")
CONFIDENCE_THRESHOLD = 0.75                   # below this → "Unknown" / not logged
RECOGNITION_MODEL    = "hog"                  # "hog" (CPU) or "cnn" (GPU)
SECRET_KEY           = os.getenv("SECRET_KEY", "presence-ai-dev-secret-change-me")
TOKEN_MAX_AGE        = 60 * 60 * 24 * 7       # 7 days

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
CORS(app)

_log_lock = threading.Lock()
_users_lock = threading.Lock()
_serializer = URLSafeTimedSerializer(SECRET_KEY, salt="auth-token")

# ── Load classifiers at startup ───────────────────────────────────────────────
# Primary engine: ArcFace (buffalo_l) + linear SVM. Falls back to the legacy
# dlib pipeline only if the ArcFace model hasn't been trained yet.
arcface_clf = arcface_le = arcface_centroids = None
try:
    arcface_clf = joblib.load(ARCFACE_CLF_FILE)
    arcface_le = joblib.load(ARCFACE_LE_FILE)
    arcface_centroids = joblib.load(ARCFACE_CENTROIDS)
    print(f"✅ ArcFace classifier loaded ({len(arcface_le.classes_)} identities)")
except Exception as e:            # noqa: BLE001
    print(f"ℹ️  ArcFace model not found yet ({e}). Train: python scripts/train_arcface.py")

try:
    pipeline = joblib.load(CLASSIFIER_FILE)
    label_encoder = joblib.load(LABEL_ENC_FILE)
    print("✅ Legacy dlib classifier loaded (fallback)")
except Exception:                 # noqa: BLE001
    pipeline, label_encoder = None, None

USE_ARCFACE = arcface_clf is not None
_engine = None                    # lazily-initialised ArcFace engine


def get_engine():
    global _engine
    if _engine is None:
        from arcface_engine import ArcFaceEngine
        _engine = ArcFaceEngine.get()
    return _engine


# ── Helpers ───────────────────────────────────────────────────────────────────
def decode_base64_image(img_b64):
    """Data-URL or bare base64 → RGB numpy array (what face_recognition wants)."""
    _, encoded = img_b64.split(",", 1) if "," in img_b64 else (None, img_b64)
    pil = Image.open(io.BytesIO(base64.b64decode(encoded))).convert("RGB")
    return np.array(pil)


def safe_student_dir(name):
    """Sanitized processed_dataset/<name> path (prevents path traversal)."""
    slug = secure_filename(name.strip()) or "unnamed"
    return os.path.join(DATASET_DIR, slug), slug


def save_images(name, images):
    """Save base64 images into processed_dataset/<name>/, return (dir, total)."""
    save_dir, _ = safe_student_dir(name)
    os.makedirs(save_dir, exist_ok=True)
    existing = len([f for f in os.listdir(save_dir) if f.lower().endswith(".jpg")])
    for i, img64 in enumerate(images, start=existing + 1):
        Image.fromarray(decode_base64_image(img64)).save(
            os.path.join(save_dir, f"{i:04d}.jpg")
        )
    total = len([f for f in os.listdir(save_dir) if f.lower().endswith(".jpg")])
    return save_dir, total


# ── Attendance logging (shared CSV format with the CLI) ───────────────────────
def today_log_path():
    os.makedirs(LOGS_DIR, exist_ok=True)
    return os.path.join(LOGS_DIR, f"attendance_{datetime.now().strftime('%Y-%m-%d')}.csv")


def already_logged_today(student_id, log_path):
    if not os.path.exists(log_path):
        return False
    with open(log_path, newline="") as f:
        return any(row and row[0] == student_id for row in csv.reader(f))


def log_attendance(student_id, confidence, camera="Web"):
    """Append to today's CSV — once per student per day."""
    log_path = today_log_path()
    with _log_lock:
        if already_logged_today(student_id, log_path):
            return
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_exists = os.path.exists(log_path)
        with open(log_path, "a", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["StudentID", "Timestamp", "Camera", "Confidence"])
            writer.writerow([student_id, timestamp, camera, f"{confidence:.4f}"])
    print(f"[✅ Attendance] {student_id} ({confidence*100:.1f}%) via {camera}")


# ── Auth helpers (file-based users + signed tokens) ───────────────────────────
def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    import json
    with open(USERS_FILE) as f:
        return json.load(f)


def save_users(users):
    import json
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def find_user(email):
    email = (email or "").strip().lower()
    return next((u for u in load_users() if u["email"] == email), None)


def public_user(user):
    return {"name": user["name"], "email": user["email"]}


def issue_token(email):
    return _serializer.dumps(email.strip().lower())


def user_from_request():
    """Return the user dict for a valid Bearer token, else None."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    try:
        email = _serializer.loads(auth[7:], max_age=TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None
    return find_user(email)


# ── Auth routes ───────────────────────────────────────────────────────────────
@app.route("/api/auth/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or not password:
        return jsonify({"error": "Name, email and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    with _users_lock:
        users = load_users()
        if any(u["email"] == email for u in users):
            return jsonify({"error": "An account with this email already exists"}), 400
        user = {"name": name, "email": email,
                "password_hash": generate_password_hash(password)}
        users.append(user)
        save_users(users)

    return jsonify({"token": issue_token(email), "user": public_user(user)}), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = find_user(email)
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify({"token": issue_token(email), "user": public_user(user)})


@app.route("/api/auth/verify", methods=["GET"])
def verify():
    user = user_from_request()
    if not user:
        return jsonify({"error": "Invalid or expired token"}), 401
    return jsonify({"valid": True, "user": public_user(user)})


@app.route("/api/auth/me", methods=["GET"])
def me():
    user = user_from_request()
    if not user:
        return jsonify({"error": "Not authenticated"}), 401
    return jsonify({"user": public_user(user)})


# ── Face recognition ──────────────────────────────────────────────────────────
@app.route("/predict", methods=["POST"])
def predict():
    if not USE_ARCFACE and pipeline is None:
        return jsonify({"error": "No classifier trained. Run python scripts/train_arcface.py"}), 500

    data = request.get_json(silent=True) or {}
    img_b64 = data.get("image")
    if not img_b64:
        return jsonify({"error": "No image received"}), 400

    rgb = decode_base64_image(img_b64)

    if USE_ARCFACE:
        results = _predict_arcface(rgb)
    else:
        results = _predict_dlib(rgb)
    return jsonify({"results": results})


def _predict_arcface(rgb):
    """
    RetinaFace/MTCNN detect + ArcFace 512-d embedding. Label comes from the SVM;
    confidence is the cosine similarity to that identity's centroid (calibrated,
    unlike the 97-class SVM probability which saturates near ~0.2).
    """
    import cv2
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    results = []
    for face in get_engine().embed_faces(bgr):
        emb = np.asarray(face["embedding"], dtype=np.float32)
        best_idx = int(arcface_clf.predict([emb])[0])
        name_pred = str(arcface_le.inverse_transform([best_idx])[0])
        # cosine confidence vs the predicted identity's centroid
        cos = float(np.dot(emb, arcface_centroids[name_pred])) if arcface_centroids else 0.0
        is_known = cos >= ARCFACE_COS_THRESHOLD
        if is_known:
            name = name_pred
            log_attendance(name, cos)
        else:
            name = "Unknown"
        results.append({
            "name": name, "confidence": cos, "isKnown": is_known,
            "box": face["box"], "det_score": round(face["det_score"], 3),
        })
    return results


def _predict_dlib(rgb):
    """Legacy fallback: face_recognition 128-d + SVM."""
    results = []
    face_locations = face_recognition.face_locations(rgb, model=RECOGNITION_MODEL)
    for (top, right, bottom, left), enc in zip(
            face_locations, face_recognition.face_encodings(rgb, face_locations)):
        proba = pipeline.predict_proba(enc.reshape(1, -1))[0]
        best_idx = int(np.argmax(proba))
        confidence = float(proba[best_idx])
        is_known = confidence >= CONFIDENCE_THRESHOLD
        if is_known:
            name = str(label_encoder.inverse_transform([best_idx])[0])
            log_attendance(name, confidence)
        else:
            name = "Unknown"
        results.append({
            "name": name, "confidence": confidence, "isKnown": is_known,
            "box": [left, top, right, bottom],
        })
    return results


# ── Students ──────────────────────────────────────────────────────────────────
@app.route("/register", methods=["POST"])
@app.route("/register-student", methods=["POST"])   # backwards-compatible alias
def register_student():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    images = data.get("images", [])
    if not name or not images:
        return jsonify({"error": "Name and at least 1 image required"}), 400

    _, total = save_images(name, images)
    return jsonify({
        "status": "success",
        "samples": total,
        "message": (f"{name} registered with {len(images)} image(s). Retrain: "
                    "python scripts/generate_encodings.py && "
                    "python scripts/train_classifier.py"),
    })


@app.route("/update-student", methods=["POST"])
def update_student():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    images = data.get("images", [])
    if not name or not images:
        return jsonify({"error": "Name and at least 1 image required"}), 400

    save_dir, _ = safe_student_dir(name)
    if not os.path.isdir(save_dir):
        return jsonify({"error": f"Student '{name}' not found"}), 404

    _, total = save_images(name, images)
    return jsonify({
        "status": "success",
        "total_samples": total,
        "message": f"Added {len(images)} image(s) for {name}. Retrain to apply.",
    })


@app.route("/students", methods=["GET"])
def get_students():
    students = []
    if os.path.isdir(DATASET_DIR):
        for name in sorted(os.listdir(DATASET_DIR)):
            d = os.path.join(DATASET_DIR, name)
            if os.path.isdir(d):
                samples = len([f for f in os.listdir(d)
                               if f.lower().endswith((".jpg", ".jpeg", ".png"))])
                students.append({"name": name, "samples": samples})
    return jsonify(students)


@app.route("/students/valid-names", methods=["GET"])
def valid_student_names():
    """Names the active model can actually recognize (are in the classifier)."""
    le = arcface_le if USE_ARCFACE else label_encoder
    names = list(map(str, le.classes_)) if le is not None else []
    return jsonify({"valid_names": names})


@app.route("/students/<name>", methods=["DELETE"])
def delete_student(name):
    save_dir, _ = safe_student_dir(name)
    if not os.path.isdir(save_dir):
        return jsonify({"error": f"Student '{name}' not found"}), 404
    shutil.rmtree(save_dir)
    return jsonify({
        "status": "success",
        "message": f"Deleted {name}. Retrain to remove them from the model.",
    })


# ── Attendance ────────────────────────────────────────────────────────────────
def load_attendance_records():
    """Aggregate every logs/attendance_*.csv, newest first."""
    records = []
    for path in glob.glob(os.path.join(LOGS_DIR, "attendance_*.csv")):
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                conf = row.get("Confidence")
                try:
                    conf = float(conf) if conf not in (None, "") else None
                except ValueError:
                    conf = None
                records.append({
                    "name": row.get("StudentID"),
                    "time": row.get("Timestamp"),
                    "confidence": conf,
                    "camera": row.get("Camera"),
                })
    records.sort(key=lambda r: r["time"] or "", reverse=True)
    return records


@app.route("/attendance", methods=["GET"])
def get_attendance():
    return jsonify(load_attendance_records())


@app.route("/stats", methods=["GET"])
def stats():
    """Live aggregate numbers for the dashboard (single source of truth)."""
    # students on disk (with ≥1 image)
    students = 0
    if os.path.isdir(DATASET_DIR):
        for d in os.listdir(DATASET_DIR):
            p = os.path.join(DATASET_DIR, d)
            if os.path.isdir(p) and any(
                    f.lower().endswith((".jpg", ".jpeg", ".png")) for f in os.listdir(p)):
                students += 1

    le = arcface_le if USE_ARCFACE else label_encoder
    trained = len(le.classes_) if le is not None else 0

    records = load_attendance_records()
    today = datetime.now().strftime("%Y-%m-%d")
    present_today = sorted({r["name"] for r in records
                            if (r["time"] or "").startswith(today)})

    # real model accuracy from the last training run, if available
    accuracy = None
    try:
        import json
        with open(os.path.join("results", "arcface_metrics.json")) as f:
            accuracy = json.load(f)["identification"]["accuracy"]
    except Exception:            # noqa: BLE001
        accuracy = None

    return jsonify({
        "engine": "arcface" if USE_ARCFACE else ("dlib" if pipeline else "none"),
        "students_registered": students,
        "identities_trained": trained,
        "total_records": len(records),
        "present_today": len(present_today),
        "present_today_names": present_today,
        "model_accuracy": accuracy,          # 0–1, or null if not trained
    })


@app.route("/attendance/clear", methods=["DELETE"])
def clear_attendance():
    removed = 0
    with _log_lock:
        for path in glob.glob(os.path.join(LOGS_DIR, "attendance_*.csv")):
            os.remove(path)
            removed += 1
    return jsonify({"status": "success", "cleared": removed})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "model_loaded": USE_ARCFACE or pipeline is not None,
        "engine": "arcface" if USE_ARCFACE else ("dlib" if pipeline else "none"),
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
