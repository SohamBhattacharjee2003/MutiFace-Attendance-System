"""
api.py
Flask REST API — web backend for the PresenceAI frontend.

Pipeline:  RetinaFace (detect every face) -> ArcFace (512-d embedding) ->
           nearest-centroid match -> four gates -> temporal vote -> attendance CSV.

Artifacts it reads:
    models/arcface_centroids.pkl      one 512-d signature per enrolled student
    models/arcface_label_encoder.pkl  the list of enrolled names
    models/arcface_thresholds.json    cosine + margin, calibrated on impostors
    processed_dataset/<name>/         enrolment images (Register/Update write here)
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
import time
import base64
import shutil
import threading
from collections import defaultdict, deque
from functools import wraps
from datetime import datetime

import numpy as np
import joblib
import liveness
from PIL import Image
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

# ── Config (mirrors scripts/attendance.py) ────────────────────────────────────
MODELS_DIR           = "models"
ARCFACE_LE_FILE      = os.path.join(MODELS_DIR, "arcface_label_encoder.pkl")
ARCFACE_CENTROIDS    = os.path.join(MODELS_DIR, "arcface_centroids.pkl")
ARCFACE_THRESHOLDS   = os.path.join(MODELS_DIR, "arcface_thresholds.json")

# Recognition gates. cos_threshold / margin are calibrated against the impostor cohort
# at training time (models/arcface_thresholds.json); these are only the fallbacks.
ARCFACE_COS_THRESHOLD = 0.32   # cosine to the best centroid; below → "Unknown"
ARCFACE_MARGIN        = 0.05   # top1 must beat top2 by this → guards against lookalikes
# Measured, not guessed (scripts/evaluate.py): accuracy collapses below ~24px (63.9%)
# and is fully recovered by 40px (88.9%, same as full resolution). 60px was a guess and
# was rejecting faces that recognize perfectly well.
MIN_FACE_PX           = 40     # a face narrower than this is too far away to trust
# InsightFace already drops detections below its own internal threshold (~0.5), so this
# is a backstop, not the primary gate. Keep it low: real, well-lit, front-facing students
# come back around 0.57–0.8, so anything near 0.6 here would reject genuine faces.
MIN_DET_SCORE         = 0.50

# Temporal voting: a face must be confidently recognized in VOTE_MIN of the last
# VOTE_WINDOW seconds' predictions before it is written to the attendance log. One
# lucky frame should not be able to mark a student present for the whole day.
VOTE_MIN              = 3
VOTE_WINDOW           = 15.0

# Liveness: a recognized face must also blink before attendance is committed. Without
# this, holding up a printed photo marks that person present — the exact proxy attendance
# the system claims to prevent. Set LIVENESS=0 in the environment to measure the
# attack-success baseline (see scripts/test_spoof.py).
LIVENESS_REQUIRED     = os.getenv("LIVENESS", "1") != "0"
DATASET_DIR          = "processed_dataset"   # generate_encodings.py reads this
LOGS_DIR             = "logs"
DATA_DIR             = "data"
USERS_FILE           = os.path.join(DATA_DIR, "users.json")
CONFIDENCE_THRESHOLD = 0.75                   # below this → "Unknown" / not logged
RECOGNITION_MODEL    = "hog"                  # "hog" (CPU) or "cnn" (GPU)
TOKEN_MAX_AGE        = 60 * 60 * 24 * 7       # 7 days

# Auth tokens are signed with this key. The old hardcoded default meant anyone who read the
# public repo could forge an admin token, silently undoing the auth on every route.
#
# Precedence: $SECRET_KEY (production) → data/secret.key (generated once, gitignored) → a
# freshly generated key persisted there. Persisting matters: a key regenerated on every
# start invalidates every session on every restart, which would log you out mid-demo.
SECRET_KEY_FILE = os.path.join("data", "secret.key")
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    os.makedirs("data", exist_ok=True)
    if os.path.exists(SECRET_KEY_FILE):
        with open(SECRET_KEY_FILE) as f:
            SECRET_KEY = f.read().strip()
    if not SECRET_KEY:
        import secrets
        SECRET_KEY = secrets.token_urlsafe(32)
        with open(SECRET_KEY_FILE, "w") as f:
            f.write(SECRET_KEY)
        os.chmod(SECRET_KEY_FILE, 0o600)
        print(f"🔑 Generated a signing key → {SECRET_KEY_FILE} (keep it out of git)")

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
CORS(app)

_log_lock = threading.Lock()
_users_lock = threading.Lock()
_serializer = URLSafeTimedSerializer(SECRET_KEY, salt="auth-token")

# ── Load the model at startup ─────────────────────────────────────────────────
# There is no classifier. ArcFace has already organised the embedding space, so
# identifying a face is "which stored centroid is nearest, and is it near enough?" —
# a matrix multiply. That is also why enrolling a student is an append rather than a
# retrain, and why the system is able to answer "nobody", which a softmax cannot.
arcface_le = arcface_centroids = None
arcface_thresholds = {"cos_threshold": ARCFACE_COS_THRESHOLD,
                      "margin": ARCFACE_MARGIN, "calibrated": False}
try:
    arcface_le = joblib.load(ARCFACE_LE_FILE)
    arcface_centroids = joblib.load(ARCFACE_CENTROIDS)
    print(f"✅ Model loaded — {len(arcface_le.classes_)} enrolled students")
    try:
        import json as _json
        with open(ARCFACE_THRESHOLDS) as f:
            arcface_thresholds = _json.load(f)
        print(f"   gates: cos≥{arcface_thresholds['cos_threshold']} "
              f"margin≥{arcface_thresholds['margin']} "
              f"({'calibrated' if arcface_thresholds.get('calibrated') else 'defaults'})")
    except Exception:             # noqa: BLE001 — pre-calibration models keep the defaults
        print("   gates: using defaults (retrain to calibrate)")
except Exception as e:            # noqa: BLE001
    print(f"ℹ️  No model yet ({e}). Register a student, or run scripts/evaluate.py")

MODEL_READY = arcface_centroids is not None
_engine = None                    # lazily-initialised ArcFace engine


def get_engine():
    global _engine
    if _engine is None:
        from arcface_engine import ArcFaceEngine
        _engine = ArcFaceEngine.get()
    return _engine


# ── Auto-retrain (registration → model, with no restart) ──────────────────────
# Registering a student only writes images to disk; until the classifier is refit
# they are not a class it can output, so they always come back "Unknown". A
# background worker refits after every registration and swaps the new model into
# the globals above, so the running process picks it up without a restart.
_train_lock = threading.Lock()          # only one training run at a time
_train_state = {"status": "idle", "message": "", "identities": None,
                "started_at": None, "finished_at": None, "pending": False}


def _set_train_state(**kw):
    _train_state.update(kw)


def _training_worker():
    global arcface_le, arcface_centroids, arcface_thresholds, MODEL_READY

    while True:
        _set_train_state(status="training", message="Starting…", pending=False,
                         started_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                         finished_at=None)
        try:
            import trainer
            summary = trainer.retrain(
                dataset=DATASET_DIR,
                progress=lambda m: _set_train_state(message=m),
            )
            le, centroids, thresholds = summary.pop("_model")

            # hot-swap: /predict reads these globals on the next request
            arcface_le, arcface_centroids = le, centroids
            arcface_thresholds = thresholds
            MODEL_READY = True

            msg = (f"{summary['identities']} identities "
                   f"({summary['newly_embedded']} new images embedded, "
                   f"{summary['from_cache']} from cache)")
            for s in summary["skipped"]:
                print(f"⚠️  Skipped '{s['name']}': {s['reason']}")
            _set_train_state(status="done", message=msg,
                             identities=summary["identities"],
                             skipped=summary["skipped"],
                             finished_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            print(f"✅ Model retrained — {msg}")
        except Exception as e:              # noqa: BLE001 — keep serving the old model
            _set_train_state(status="error", message=str(e),
                             finished_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            print(f"❌ Retrain failed ({e}). Still serving the previous model.")

        # a registration that landed mid-run needs another pass to be included
        with _train_lock:
            if not _train_state["pending"]:
                _train_state["running"] = False
                return


def trigger_retrain():
    """Kick off a retrain in the background; coalesce if one is already running."""
    with _train_lock:
        if _train_state.get("running"):
            _train_state["pending"] = True      # fold into a follow-up run
            return "queued"
        _train_state["running"] = True
    threading.Thread(target=_training_worker, daemon=True).start()
    return "started"


# ── Helpers ───────────────────────────────────────────────────────────────────
def decode_base64_image(img_b64):
    """Data-URL or bare base64 → RGB numpy array."""
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


# ── Temporal voting ───────────────────────────────────────────────────────────
# Attendance is written once per student per day, so a single misrecognized frame
# marks the wrong person present permanently. Video gives us many looks at the same
# face — require several agreeing sightings inside a short window before committing.
_votes = defaultdict(deque)      # name -> timestamps of recent confident sightings
_vote_lock = threading.Lock()


def _vote_and_log(student_id, confidence, camera="Web"):
    """Record a sighting; log attendance only once it clears the voting threshold."""
    now = time.time()
    with _vote_lock:
        seen = _votes[student_id]
        seen.append(now)
        while seen and now - seen[0] > VOTE_WINDOW:
            seen.popleft()
        confirmed = len(seen) >= VOTE_MIN
    if confirmed:
        log_attendance(student_id, confidence, camera)
        return True
    return False


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


def require_auth(fn):
    """
    Gate an endpoint behind a valid Bearer token.

    Attendance is exactly the thing people have an incentive to cheat, and until now
    every route below was open: anyone on the same network could mark themselves
    present, delete a student, or wipe the log with a single curl. Login existed but
    nothing enforced it.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if user_from_request() is None:
            return jsonify({"error": "Authentication required"}), 401
        return fn(*args, **kwargs)
    return wrapper


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
@require_auth
def predict():
    if not MODEL_READY:
        return jsonify({"error": "No students enrolled yet. Register one first."}), 500

    data = request.get_json(silent=True) or {}
    img_b64 = data.get("image")
    if not img_b64:
        return jsonify({"error": "No image received"}), 400

    rgb = decode_base64_image(img_b64)

    return jsonify({"results": _predict_arcface(rgb)})


def _predict_arcface(rgb):
    """
    RetinaFace detect + ArcFace 512-d embedding, then three gates before we are
    willing to put a name on a face:

      1. size/quality — a face only ~30px wide is upscaled to 112px before embedding,
         which invents no detail. The SVM has no "none of the above" option and will
         still emit a confident-looking class, so small faces must be rejected up
         front rather than guessed at.
      2. absolute    — cosine to the best centroid must clear the calibrated threshold
         (open-set rejection: is this anyone we know?).
      3. margin      — the best centroid must beat the runner-up by a margin. Two
         students who look alike both score high against each other; the absolute
         threshold cannot separate them, but the gap between them can.

    Unlike the previous version, cosine is computed against EVERY centroid rather than
    only the SVM's pick, so we can see the runner-up at all.
    """
    import cv2
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

    names = sorted(arcface_centroids) if arcface_centroids else []
    M = np.stack([arcface_centroids[n] for n in names]) if names else None
    cos_thresh = arcface_thresholds.get("cos_threshold", ARCFACE_COS_THRESHOLD)
    margin_min = arcface_thresholds.get("margin", ARCFACE_MARGIN)

    results = []
    for face in get_engine().embed_faces(bgr):
        x1, y1, x2, y2 = face["box"]
        width = x2 - x1
        emb = np.asarray(face["embedding"], dtype=np.float32)

        base = {"box": face["box"], "det_score": round(face["det_score"], 3),
                "faceWidth": int(width)}

        # gate 1 — too far away, or too weak a detection, to identify reliably.
        # Distinct reasons: "too small" and "poorly detected" need different user-facing
        # advice (step closer vs. face the camera / fix the lighting).
        if width < MIN_FACE_PX:
            results.append({**base, "name": "Move closer", "confidence": 0.0,
                            "isKnown": False, "reason": "face_too_small"})
            continue
        if face["det_score"] < MIN_DET_SCORE:
            results.append({**base, "name": "Face the camera", "confidence": 0.0,
                            "isKnown": False, "reason": "low_detection_quality"})
            continue

        if M is None:
            results.append({**base, "name": "Unknown", "confidence": 0.0, "isKnown": False})
            continue

        sims = M @ emb
        order = np.argsort(sims)[::-1]
        top1 = float(sims[order[0]])
        top2 = float(sims[order[1]]) if len(order) > 1 else -1.0
        margin = top1 - top2
        candidate = names[order[0]]

        # gate 2 — nobody we know
        if top1 < cos_thresh:
            results.append({**base, "name": "Unknown", "confidence": top1,
                            "isKnown": False, "reason": "below_threshold"})
            continue

        # gate 3 — two identities too close to call
        if margin < margin_min:
            results.append({**base, "name": "Uncertain", "confidence": top1,
                            "isKnown": False, "reason": "ambiguous",
                            "candidates": [candidate, names[order[1]]],
                            "margin": round(margin, 4)})
            continue

        # gate 4 — liveness. Recognition cannot distinguish a person from a photo of that
        # person, so being recognized must not be sufficient to be marked present.
        # A live face blinks; a printed photo or a still phone screen does not.
        is_live, ear, live_state = liveness.update(candidate, face.get("landmarks"))
        if LIVENESS_REQUIRED and not is_live:
            results.append({**base, "name": candidate, "confidence": top1,
                            "isKnown": True, "logged": False, "live": False,
                            "ear": round(ear, 3) if ear else None,
                            "reason": live_state,          # "blink_required"
                            "margin": round(margin, 4)})
            continue

        logged = _vote_and_log(candidate, top1)
        results.append({**base, "name": candidate, "confidence": top1, "isKnown": True,
                        "margin": round(margin, 4), "logged": logged, "live": True,
                        "ear": round(ear, 3) if ear else None})
    return results


# ── Students ──────────────────────────────────────────────────────────────────
@app.route("/register", methods=["POST"])
@app.route("/register-student", methods=["POST"])   # backwards-compatible alias
@require_auth
def register_student():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    images = data.get("images", [])
    if not name or not images:
        return jsonify({"error": "Name and at least 1 image required"}), 400

    _, total = save_images(name, images)
    training = trigger_retrain()
    return jsonify({
        "status": "success",
        "samples": total,
        "training": training,
        "message": (f"{name} registered with {len(images)} image(s). "
                    f"Model is retraining now — they'll be recognized in a few seconds."),
    })


@app.route("/update-student", methods=["POST"])
@require_auth
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
    training = trigger_retrain()
    return jsonify({
        "status": "success",
        "total_samples": total,
        "training": training,
        "message": f"Added {len(images)} image(s) for {name}. Model is retraining now.",
    })


def is_real_student(name):
    """
    The VGGFace2 identities (n000xxx) in processed_dataset are a research cohort — an
    impostor set used to calibrate the rejection threshold — not people who enrolled.
    Counting them as "registered students" made the dashboard read "98 students
    registered, 2 trained", which looks broken and is simply untrue.
    """
    import trainer
    return not trainer.is_impostor(name)


@app.route("/students", methods=["GET"])
@require_auth
def get_students():
    students = []
    if os.path.isdir(DATASET_DIR):
        for name in sorted(os.listdir(DATASET_DIR)):
            d = os.path.join(DATASET_DIR, name)
            if os.path.isdir(d) and is_real_student(name):
                samples = len([f for f in os.listdir(d)
                               if f.lower().endswith((".jpg", ".jpeg", ".png"))])
                students.append({"name": name, "samples": samples})
    return jsonify(students)


@app.route("/students/valid-names", methods=["GET"])
@require_auth
def valid_student_names():
    """Names the active model can actually recognize (are in the classifier)."""
    le = arcface_le
    names = list(map(str, le.classes_)) if le is not None else []
    return jsonify({"valid_names": names})


@app.route("/students/<name>", methods=["DELETE"])
@require_auth
def delete_student(name):
    save_dir, _ = safe_student_dir(name)
    if not os.path.isdir(save_dir):
        return jsonify({"error": f"Student '{name}' not found"}), 404
    shutil.rmtree(save_dir)
    training = trigger_retrain()
    return jsonify({
        "status": "success",
        "training": training,
        "message": f"Deleted {name}. Model is retraining to remove them.",
    })


@app.route("/train", methods=["POST"])
@require_auth
def train():
    """Manually kick off a retrain (registrations already do this automatically)."""
    return jsonify({"status": trigger_retrain(), "state": _train_state})


@app.route("/train/status", methods=["GET"])
@require_auth
def train_status():
    """Poll this after registering: status goes idle → training → done."""
    return jsonify(_train_state)


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
@require_auth
def get_attendance():
    return jsonify(load_attendance_records())


@app.route("/stats", methods=["GET"])
@require_auth
def stats():
    """Live aggregate numbers for the dashboard (single source of truth)."""
    # enrolled students on disk (with ≥1 image) — excludes the VGGFace2 research cohort
    students = 0
    if os.path.isdir(DATASET_DIR):
        for d in os.listdir(DATASET_DIR):
            p = os.path.join(DATASET_DIR, d)
            if os.path.isdir(p) and is_real_student(d) and any(
                    f.lower().endswith((".jpg", ".jpeg", ".png")) for f in os.listdir(p)):
                students += 1

    le = arcface_le
    trained = len(le.classes_) if le is not None else 0

    records = load_attendance_records()
    today = datetime.now().strftime("%Y-%m-%d")
    present_today = sorted({r["name"] for r in records
                            if (r["time"] or "").startswith(today)})

    # Accuracy comes from the held-out evaluation (scripts/evaluate.py), NOT from a
    # training run. The old code reported the training accuracy of a 98-class model that
    # is no longer even deployed — a number nobody could source, on screen during a demo.
    accuracy = None
    try:
        import json
        with open(os.path.join("results", "evaluation.json")) as f:
            ev = json.load(f)
        accuracy = ev["ablation"][-1]["accuracy"]     # the shipped configuration
    except Exception:            # noqa: BLE001 — no evaluation run yet → report nothing
        accuracy = None

    return jsonify({
        "engine": "arcface",
        "students_registered": students,
        "identities_trained": trained,
        "total_records": len(records),
        "present_today": len(present_today),
        "present_today_names": present_today,
        "model_accuracy": accuracy,          # 0–1, or null if not trained
    })


@app.route("/attendance/clear", methods=["DELETE"])
@require_auth
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
        "model_loaded": MODEL_READY,
        "engine": "arcface",
    })


if __name__ == "__main__":
    # debug=True exposes the Werkzeug debugger console. Bound to 0.0.0.0 that is a remote
    # code execution hole for anyone on the same network — strictly worse than the missing
    # auth we just fixed. It must be opt-in and never the default.
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    host = os.getenv("HOST", "127.0.0.1" if not debug else "127.0.0.1")
    app.run(host=host, port=int(os.getenv("PORT", "5000")), debug=debug)
