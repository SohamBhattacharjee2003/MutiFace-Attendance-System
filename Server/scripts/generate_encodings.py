"""
generate_encodings.py
Loads all face images from processed_dataset/, generates 128-d face encodings
using face_recognition (dlib ResNet under the hood), and saves to encodings/encodings.pkl

Usage: python scripts/generate_encodings.py
"""

import os
import pickle
import face_recognition
import numpy as np
from tqdm import tqdm

# ── Config ────────────────────────────────────────────────────────────────────
DATASET_DIR   = "processed_dataset"   # output of preprocess.py
ENCODINGS_DIR = "encodings"
OUTPUT_FILE   = os.path.join(ENCODINGS_DIR, "encodings.pkl")
MODEL         = "hog"                 # "hog" = fast CPU | "cnn" = accurate (GPU)


def generate_encodings():
    os.makedirs(ENCODINGS_DIR, exist_ok=True)

    known_encodings = []
    known_labels    = []

    if not os.path.exists(DATASET_DIR):
        print(f"ERROR: '{DATASET_DIR}' not found. Run preprocess.py first.")
        return

    student_dirs = [
        d for d in os.listdir(DATASET_DIR)
        if os.path.isdir(os.path.join(DATASET_DIR, d))
    ]

    if not student_dirs:
        print(f"No subfolders found in {DATASET_DIR}. Run preprocess.py first.")
        return

    print(f"Found {len(student_dirs)} identities: {student_dirs[:5]} ...\n")

    for student_id in student_dirs:
        student_path = os.path.join(DATASET_DIR, student_id)
        image_files  = [
            f for f in os.listdir(student_path)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ]

        for img_file in tqdm(image_files, desc=student_id, leave=False):
            img_path = os.path.join(student_path, img_file)
            image    = face_recognition.load_image_file(img_path)  # RGB array

            locations = face_recognition.face_locations(image, model=MODEL)

            if not locations:
                continue  # no face detected — skip

            # If multiple faces, pick the largest
            if len(locations) > 1:
                areas     = [(b - t) * (r - l) for (t, r, b, l) in locations]
                locations = [locations[int(np.argmax(areas))]]

            encodings = face_recognition.face_encodings(image, known_face_locations=locations)

            if encodings:
                known_encodings.append(encodings[0])
                known_labels.append(student_id)

    # Save
    data = {"encodings": known_encodings, "labels": known_labels}
    with open(OUTPUT_FILE, "wb") as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

    print(f"\n✅ Done!")
    print(f"   Total encodings : {len(known_encodings)}")
    print(f"   Unique identities: {len(set(known_labels))}")
    print(f"   Saved to        : {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_encodings()
