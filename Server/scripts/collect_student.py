"""
collect_student.py
Captures face images from your webcam for a given student name/ID.
Saves cropped face images to processed_dataset/<student_id>/
Then you re-run generate_encodings.py and train_classifier.py to include them.

Usage:
    python scripts/collect_student.py --name "Soham"
    python scripts/collect_student.py --name "STU001" --count 80
"""

import cv2
import os
import argparse
import time

# ── Config ────────────────────────────────────────────────────────────────────
OUTPUT_DIR   = "processed_dataset"   # same folder generate_encodings.py reads
IMAGE_SIZE   = (160, 160)            # match what preprocess.py outputs
CAPTURE_DELAY = 0.15                 # seconds between auto-captures

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def collect(student_id: str, target_count: int):
    save_dir = os.path.join(OUTPUT_DIR, student_id)
    os.makedirs(save_dir, exist_ok=True)

    # Count images already in the folder (allows resuming)
    existing = [f for f in os.listdir(save_dir) if f.endswith(".jpg")]
    img_count = len(existing)

    if img_count >= target_count:
        print(f"Already have {img_count} images for '{student_id}'. Nothing to do.")
        return

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Could not open camera.")
        print("Make sure Terminal has camera permission in:")
        print("  System Settings → Privacy & Security → Camera")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print(f"\nCollecting faces for: '{student_id}'")
    print(f"Target: {target_count} images  |  Already saved: {img_count}")
    print("Controls:")
    print("  [SPACE] — capture one image manually")
    print("  [A]     — toggle auto-capture mode")
    print("  [Q]     — quit\n")

    auto_capture  = False
    last_captured = 0

    while img_count < target_count:
        ret, frame = cap.read()
        if not ret:
            continue

        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80)
        )

        display = frame.copy()
        face_detected = len(faces) > 0

        for (x, y, w, h) in faces:
            cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Status bar overlay
        status = f"Saved: {img_count}/{target_count}"
        mode   = "AUTO" if auto_capture else "MANUAL"
        color  = (0, 200, 0) if face_detected else (0, 0, 220)

        cv2.rectangle(display, (0, 0), (640, 50), (30, 30, 30), -1)
        cv2.putText(display, f"Student: {student_id}  |  {status}  |  Mode: {mode}",
                    (10, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)

        if not face_detected:
            cv2.putText(display, "No face detected — move closer or improve lighting",
                        (80, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 200), 2)

        cv2.imshow(f"Collecting faces — {student_id}", display)

        key = cv2.waitKey(1) & 0xFF

        # Auto-capture every CAPTURE_DELAY seconds if face is visible
        now = time.time()
        should_capture = face_detected and (
            (key == ord(" ")) or
            (auto_capture and (now - last_captured) >= CAPTURE_DELAY)
        )

        if key == ord("a"):
            auto_capture = not auto_capture
            print(f"Auto-capture: {'ON' if auto_capture else 'OFF'}")

        if key == ord("q"):
            print("Quit early.")
            break

        if should_capture:
            # Crop and save the first detected face
            x, y, w, h = faces[0]
            pad = 15
            x1 = max(0, x - pad);  y1 = max(0, y - pad)
            x2 = min(frame.shape[1], x + w + pad)
            y2 = min(frame.shape[0], y + h + pad)

            face_crop = frame[y1:y2, x1:x2]
            if face_crop.size == 0:
                continue

            face_resized = cv2.resize(face_crop, IMAGE_SIZE)
            filename     = os.path.join(save_dir, f"{img_count:04d}.jpg")
            cv2.imwrite(filename, face_resized)
            img_count   += 1
            last_captured = now
            print(f"  Saved {img_count}/{target_count}: {filename}")

    cap.release()
    cv2.destroyAllWindows()

    print(f"\n✅ Done! {img_count} images saved to: {save_dir}")
    print("\nNext steps:")
    print("  python scripts/generate_encodings.py")
    print("  python scripts/train_classifier.py --classifier svm")
    print("  python scripts/attendance.py --cameras 0")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect your own face for the attendance system")
    parser.add_argument("--name",  required=True, help="Your name or student ID, e.g. 'Soham'")
    parser.add_argument("--count", type=int, default=80, help="Number of images to collect (default: 80)")
    args   = parser.parse_args()

    collect(student_id=args.name, target_count=args.count)
