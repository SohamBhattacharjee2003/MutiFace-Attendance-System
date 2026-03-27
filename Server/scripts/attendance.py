"""
attendance.py
Live multi-camera attendance system.
Recognises faces using the trained SVM classifier and logs attendance to logs/.

Usage:
    python scripts/attendance.py --cameras 0
    python scripts/attendance.py --cameras 0 1
"""

import cv2
import os
import csv
import argparse
import threading
import face_recognition
import numpy as np
import joblib
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
MODELS_DIR           = "models"
CLASSIFIER_FILE      = os.path.join(MODELS_DIR, "classifier.pkl")
LABEL_ENC_FILE       = os.path.join(MODELS_DIR, "label_encoder.pkl")
LOGS_DIR             = "logs"
CONFIDENCE_THRESHOLD = 0.55   # below this → "Unknown"
RECOGNITION_MODEL    = "hog"  # "hog" (fast) or "cnn" (accurate)
FRAME_SKIP           = 3      # process every Nth frame to save CPU


def get_log_path():
    os.makedirs(LOGS_DIR, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(LOGS_DIR, f"attendance_{date_str}.csv")


def log_attendance(student_id, cam_idx, log_path, logged_set, lock):
    with lock:
        if student_id in logged_set:
            return
        logged_set.add(student_id)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with lock:
        file_exists = os.path.exists(log_path)
        with open(log_path, "a", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["StudentID", "Timestamp", "Camera"])
            writer.writerow([student_id, timestamp, f"Camera_{cam_idx}"])

    print(f"[✅ Attendance] {student_id} marked PRESENT at {timestamp} via Camera {cam_idx}")


def camera_thread(cam_idx, pipeline, le, log_path, logged_set, log_lock, stop_event):
    cap = cv2.VideoCapture(cam_idx)
    if not cap.isOpened():
        print(f"[Camera {cam_idx}] ⚠ Could not open. Skipping.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    frame_count       = 0
    face_names        = []
    face_locs_display = []

    print(f"[Camera {cam_idx}] Started. Press 'q' to quit.")

    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            continue

        frame_count += 1

        if frame_count % FRAME_SKIP == 0:
            small     = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

            face_locs_display = face_recognition.face_locations(rgb_small, model=RECOGNITION_MODEL)
            face_encodings    = face_recognition.face_encodings(rgb_small, face_locs_display)

            face_names = []
            for enc in face_encodings:
                proba     = pipeline.predict_proba(enc.reshape(1, -1))[0]
                best_idx  = int(np.argmax(proba))
                best_conf = proba[best_idx]

                if best_conf >= CONFIDENCE_THRESHOLD:
                    student_id = le.inverse_transform([best_idx])[0]
                    label      = f"{student_id} ({best_conf*100:.1f}%)"
                    log_attendance(student_id, cam_idx, log_path, logged_set, log_lock)
                else:
                    label = "Unknown"

                face_names.append(label)

        # Draw bounding boxes
        for (top, right, bottom, left), name in zip(face_locs_display, face_names):
            top *= 4; right *= 4; bottom *= 4; left *= 4
            color = (0, 220, 0) if "Unknown" not in name else (0, 0, 220)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.rectangle(frame, (left, bottom - 30), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, name, (left + 4, bottom - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

        cv2.imshow(f"Camera {cam_idx} — Attendance", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            stop_event.set()

    cap.release()
    cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cameras", nargs="+", type=int, default=[0])
    args = parser.parse_args()

    pipeline   = joblib.load(CLASSIFIER_FILE)
    le         = joblib.load(LABEL_ENC_FILE)
    log_path   = get_log_path()
    logged_set = set()
    log_lock   = threading.Lock()
    stop_event = threading.Event()

    threads = [
        threading.Thread(
            target=camera_thread,
            args=(cam_idx, pipeline, le, log_path, logged_set, log_lock, stop_event),
            daemon=True
        )
        for cam_idx in args.cameras
    ]

    for t in threads: t.start()
    for t in threads: t.join()

    print(f"\nSession ended. Attendance log: {log_path}")


if __name__ == "__main__":
    main()
