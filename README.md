# Presence AI — Multi-Face Attendance System

A face-recognition attendance system with a **Python/dlib backend** (the original
CLI pipeline) and the **PresenceAI React web frontend** (from the repo's `main`
branch), merged into a single app.

The backend is the existing `face_recognition` (dlib, 128-d encodings) pipeline.
A Flask API (`Server/api.py`) exposes it to the web frontend, and the same
models / dataset / logs are shared by both the CLI scripts and the web app.

```
Major/
├── Server/                     # Python backend (dlib face_recognition)
│   ├── api.py                  # Flask REST API — serves the frontend
│   ├── data/users.json         # web app accounts (created on first signup)
│   ├── scripts/
│   │   ├── dataset.py          # download VGGFace2 via kagglehub
│   │   ├── preprocess.py       # MTCNN crop → processed_dataset/
│   │   ├── collect_student.py  # capture faces from webcam (CLI)
│   │   ├── generate_encodings.py  # images → encodings/encodings.pkl (128-d)
│   │   ├── train_classifier.py    # encodings → models/classifier.pkl (SVM/KNN)
│   │   └── attendance.py       # live multi-camera attendance (CLI/OpenCV)
│   ├── processed_dataset/      # training images, one folder per student
│   ├── encodings/encodings.pkl
│   ├── models/classifier.pkl, label_encoder.pkl
│   └── logs/attendance_*.csv   # attendance records (shared by CLI + web)
└── frontend/                   # React + Vite + Tailwind (PresenceAI, main branch)
    └── src/
        ├── pages/              # Login · Dashboard · RegisterStudent ·
        │                       #   LiveAttendance · Attendance · StudentList ·
        │                       #   Attendance_Records
        └── utils/api.js        # all backend calls (base URL: localhost:5000)
```

## API contract (`Server/api.py`)

| Method | Route                     | Body                     | Returns |
|--------|---------------------------|--------------------------|---------|
| POST   | `/api/auth/signup`        | `{name, email, password}`| `{token, user}` |
| POST   | `/api/auth/login`         | `{email, password}`      | `{token, user}` |
| GET    | `/api/auth/verify`        | Bearer token             | `{valid, user}` |
| GET    | `/api/auth/me`            | Bearer token             | `{user}` |
| POST   | `/predict`                | `{image}` (data-URL)     | `{results:[{name, confidence, isKnown, box:[x1,y1,x2,y2]}]}` — logs present students |
| POST   | `/register`               | `{name, images[]}`       | saves to `processed_dataset/<name>/`, `{status, samples}` |
| POST   | `/update-student`         | `{name, images[]}`       | appends images, `{status, total_samples}` |
| GET    | `/students`               | –                        | `[{name, samples}]` |
| GET    | `/students/valid-names`   | –                        | `{valid_names:[...]}` (names in the trained model) |
| DELETE | `/students/<name>`        | –                        | `{status}` (removes the folder) |
| GET    | `/attendance`             | –                        | `[{name, time, confidence, camera}]` from `logs/*.csv` |
| DELETE | `/attendance/clear`       | –                        | `{status, cleared}` |
| GET    | `/health`                 | –                        | `{status, model_loaded}` |

**Auth** is file-based: users live in `Server/data/users.json` (passwords hashed
with Werkzeug), and tokens are signed with `itsdangerous` (ships with Flask —
no extra dependency). Set `SECRET_KEY` in the environment for production.

> **Note on the merge:** the cloned repo's original `Backend/` used a different,
> incompatible stack (facenet-pytorch 512-d embeddings + MongoDB). Per the chosen
> design, the **dlib CLI Server is the base**, so that Flask backend was *not*
> imported — `Server/api.py` is a new wrapper over the existing 128-d pipeline.
> Accounts and attendance are stored in files (JSON + CSV), not MongoDB.

## Backend setup

```bash
cd Server
python -m venv venv && source venv/bin/activate     # optional
pip install -r requirements.txt                     # needs cmake/dlib toolchain

# One-time: build the model (skip steps you've already run)
python scripts/dataset.py            # or bring your own images
python scripts/preprocess.py         # -> processed_dataset/
python scripts/generate_encodings.py # -> encodings/encodings.pkl
python scripts/train_classifier.py   # -> models/classifier.pkl

# Run the web API (serves the frontend)
python api.py                        # http://127.0.0.1:5000
```

> If `face_recognition` fails to load `shape_predictor_68_face_landmarks.dat`,
> the model file is missing from the `face_recognition_models` package. Fetch it:
> ```bash
> cd venv/lib/python*/site-packages/face_recognition_models/models
> curl -LO http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
> bunzip2 shape_predictor_68_face_landmarks.dat.bz2
> ```

You can still run the CLI live view: `python scripts/attendance.py --cameras 0`.

## Frontend setup

```bash
cd frontend
npm install    # installs react, framer-motion, recharts, lucide-react, react-icons, ...
npm run dev    # http://localhost:5173
```

The frontend calls the backend at `http://localhost:5000` (see `frontend/src/utils/api.js`).

## Typical flow

1. **Sign up / log in** on the landing page.
2. **Register** a student (captures webcam images → `processed_dataset/<name>/`).
3. Retrain: `python scripts/generate_encodings.py && python scripts/train_classifier.py`.
4. Restart `api.py` so it loads the new model (adds the student to `valid-names`).
5. **Attendance / Live** recognizes faces and logs them; **Dashboard** and
   **Records** show the counts and log (auto-refreshing every 5s).
