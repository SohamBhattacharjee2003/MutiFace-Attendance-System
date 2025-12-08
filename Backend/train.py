# train.py
import os
import numpy as np
from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
from tqdm import tqdm
import joblib
from PIL import Image

from model.detector import FaceDetector
from model.embedder import Embedder

TRAIN_DIR = "dataset_small/train"
VAL_DIR = "dataset_small/val"

CLASSIFIER_PATH = "model/face_classifier.pkl"
LABEL_ENCODER_PATH = "model/label_encoder.pkl"

detector = FaceDetector()
embedder = Embedder()


def extract_embedding(img_path):
    try:
        img = Image.open(img_path).convert("RGB")

        # detect face
        boxes, probs, faces = detector.detect_faces(img)

        if faces is None or len(faces) == 0:
            print("❌ No face in:", img_path)
            return None

        face = faces[0].resize((160, 160))
        face_np = np.array(face)

        if face_np.ndim != 3 or face_np.shape[2] != 3:
            print("❌ Invalid face shape:", face_np.shape)
            return None

        emb = embedder.get_embedding(face_np)
        return emb

    except Exception as e:
        print("⚠️ Error:", img_path, "->", e)
        return None


def load_dataset(folder):
    X, y = [], []

    if not os.path.exists(folder):
        print("⚠️ Directory missing:", folder)
        return np.array([]), np.array([])

    persons = os.listdir(folder)

    for person in persons:
        p_dir = os.path.join(folder, person)
        if not os.path.isdir(p_dir):
            continue

        print(f"\n📁 Processing: {person}")

        for img_name in tqdm(os.listdir(p_dir), desc=f"Images of {person}"):
            img_path = os.path.join(p_dir, img_name)

            emb = extract_embedding(img_path)
            if emb is not None:
                X.append(emb)
                y.append(person)

    return np.array(X), np.array(y)


def train_model():
    print("\n🔍 Loading training images...")
    X, y = load_dataset(TRAIN_DIR)

    if len(X) == 0:
        raise ValueError("❌ No training data found!")

    print(f"\n📌 Total Training Samples: {len(X)}")

    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    print("\n🧠 Training SVM...")
    clf = SVC(kernel="linear", probability=True)
    clf.fit(X, y_enc)

    joblib.dump(clf, CLASSIFIER_PATH)
    joblib.dump(le, LABEL_ENCODER_PATH)

    print("\n✅ Model saved!")
    return clf, le


def evaluate(clf, le):
    print("\n📊 Loading validation images...")
    X_val, y_val = load_dataset(VAL_DIR)

    if len(X_val) == 0:
        print("⚠️ No validation set, skipping.")
        return

    y_val_enc = le.transform(y_val)

    preds = clf.predict(X_val)
    acc = accuracy_score(y_val_enc, preds)

    print(f"\n🎯 Validation Accuracy: {acc * 100:.2f}%")


if __name__ == "__main__":
    clf, le = train_model()
    evaluate(clf, le)
