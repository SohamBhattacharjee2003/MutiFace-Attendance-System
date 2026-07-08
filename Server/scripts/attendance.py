"""
attendance.py
Live multi-camera attendance system — macOS compatible.

Fix: cv2.imshow() MUST be called from the main thread on macOS (Cocoa constraint).
     Background threads do capture + recognition only, and write annotated frames
     into a shared frame_buffer. The main thread handles all display.

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
CONFIDENCE_THRESHOLD = 0.75   # below this → "Unknown" (raised to reduce false positives)
RECOGNITION_MODEL    = "hog"  # "hog" (fast/CPU) or "cnn" (accurate/GPU)
FRAME_SKIP           = 3      # run face recognition every Nth frame


def get_log_path():
    os.makedirs(LOGS_DIR, exist_ok=True)
    return os.path.join(LOGS_DIR, f"attendance_{datetime.now().strftime('%Y-%m-%d')}.csv")


def log_attendance(student_id, cam_idx, confidence, log_path, logged_set, lock):
    """Mark a student present — thread-safe, logs only once per session."""
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
                writer.writerow(["StudentID", "Timestamp", "Camera", "Confidence"])
            writer.writerow([student_id, timestamp, f"Camera_{cam_idx}", f"{confidence:.4f}"])

    print(f"[✅ Attendance] {student_id} marked PRESENT at {timestamp} via Camera {cam_idx}")


def capture_thread(cam_idx, pipeline, le, log_path,
                   logged_set, log_lock, frame_buffer, buf_lock, stop_event):
    """
    Background thread: captures frames, runs face recognition,
    draws annotations, and stores the result in frame_buffer[cam_idx].
    Does NOT call cv2.imshow (macOS would crash here).
    """
    cap = cv2.VideoCapture(cam_idx)
    if not cap.isOpened():
        print(f"[Camera {cam_idx}] ⚠ Could not open camera.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    print(f"[Camera {cam_idx}] Capture started.")

    frame_count       = 0
    face_names        = []
    face_locs_display = []

    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            continue

        frame_count += 1

        # Run face recognition every FRAME_SKIP frames
        if frame_count % FRAME_SKIP == 0:
            # Shrink frame 4× for faster detection
            small     = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

            face_locs_display = face_recognition.face_locations(
                rgb_small, model=RECOGNITION_MODEL
            )
            face_encodings = face_recognition.face_encodings(
                rgb_small, face_locs_display
            )

            face_names = []
            for enc in face_encodings:
                proba     = pipeline.predict_proba(enc.reshape(1, -1))[0]
                best_idx  = int(np.argmax(proba))
                best_conf = proba[best_idx]

                if best_conf >= CONFIDENCE_THRESHOLD:
                    student_id = le.inverse_transform([best_idx])[0]
                    label      = f"{student_id} ({best_conf * 100:.1f}%)"
                    log_attendance(student_id, cam_idx, best_conf, log_path,
                                   logged_set, log_lock)
                else:
                    label = "Unknown"

                face_names.append(label)

        # Draw bounding boxes onto the frame (scale back from 1/4 size)
        annotated = frame.copy()
        for (top, right, bottom, left), name in zip(face_locs_display, face_names):
            top    *= 4; right *= 4; bottom *= 4; left *= 4
            color   = (0, 220, 0) if "Unknown" not in name else (0, 0, 220)
            cv2.rectangle(annotated, (left, top), (right, bottom), color, 2)
            cv2.rectangle(annotated, (left, bottom - 30), (right, bottom), color, cv2.FILLED)
            cv2.putText(annotated, name, (left + 4, bottom - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

        # Status overlay
        cv2.putText(annotated, f"Cam {cam_idx} | Press Q to quit",
                    (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        # Write annotated frame to shared buffer (main thread will display it)
        with buf_lock:
            frame_buffer[cam_idx] = annotated

    cap.release()
    print(f"[Camera {cam_idx}] Stopped.")


def main():
    parser = argparse.ArgumentParser(description="Multi-camera attendance system")
    parser.add_argument("--cameras", nargs="+", type=int, default=[0],
                        help="Camera indices e.g. --cameras 0 1")
    args = parser.parse_args()

    pipeline   = joblib.load(CLASSIFIER_FILE)
    le         = joblib.load(LABEL_ENC_FILE)
    log_path   = get_log_path()
    logged_set = set()
    log_lock   = threading.Lock()
    stop_event = threading.Event()

    # Shared frame buffer: {cam_idx: annotated_frame}
    frame_buffer = {}
    buf_lock     = threading.Lock()

    # Start one capture thread per camera
    threads = [
        threading.Thread(
            target=capture_thread,
            args=(cam_idx, pipeline, le, log_path,
                  logged_set, log_lock, frame_buffer, buf_lock, stop_event),
            daemon=True
        )
        for cam_idx in args.cameras
    ]

    for t in threads:
        t.start()

    print("Attendance system running. Press 'Q' in any window to quit.\n")

    # ── MAIN THREAD: all cv2.imshow calls happen here (macOS requirement) ──
    while not stop_event.is_set():
        with buf_lock:
            frames = dict(frame_buffer)   # snapshot to avoid holding lock during imshow

        for cam_idx, frame in frames.items():
            cv2.imshow(f"Camera {cam_idx} - Attendance", frame)

        # waitKey must also be in main thread; 'q' or 'Q' quits
        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), ord("Q")):
            stop_event.set()

    cv2.destroyAllWindows()

    for t in threads:
        t.join(timeout=3)

    print(f"\nSession ended. Attendance log → {log_path}")


if __name__ == "__main__":
    main()
