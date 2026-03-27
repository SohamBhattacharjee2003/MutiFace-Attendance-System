"""
train_classifier.py
Trains an SVM (or KNN) on 128-d face encodings from encodings/encodings.pkl.
Runs cross-validation, prints evaluation report, saves model to models/.

Usage:
    python scripts/train_classifier.py --classifier svm
    python scripts/train_classifier.py --classifier knn
"""

import os
import pickle
import argparse
import numpy as np

from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix
import joblib

# ── Config ────────────────────────────────────────────────────────────────────
ENCODINGS_FILE = "encodings/encodings.pkl"
MODELS_DIR     = "models"
MODEL_OUT      = os.path.join(MODELS_DIR, "classifier.pkl")
LABEL_ENC_OUT  = os.path.join(MODELS_DIR, "label_encoder.pkl")


def load_encodings():
    with open(ENCODINGS_FILE, "rb") as f:
        data = pickle.load(f)
    X = np.array(data["encodings"])
    y = np.array(data["labels"])
    return X, y


def build_svm():
    return Pipeline([
        ("scaler", StandardScaler()),
        ("clf", SVC(kernel="rbf", C=1.0, gamma="scale",
                    probability=True, class_weight="balanced"))
    ])


def build_knn(n):
    return Pipeline([
        ("scaler", StandardScaler()),
        ("clf", KNeighborsClassifier(n_neighbors=n,
                                     metric="euclidean",
                                     weights="distance"))
    ])


def train(classifier_type):
    os.makedirs(MODELS_DIR, exist_ok=True)

    print(f"Loading encodings from {ENCODINGS_FILE} …")
    X, y_str = load_encodings()
    print(f"  Samples  : {X.shape[0]}")
    print(f"  Classes  : {np.unique(y_str)}\n")

    # Encode string labels → integers
    le = LabelEncoder()
    y  = le.fit_transform(y_str)

    # Train/test split (stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"Train: {len(X_train)}  |  Test: {len(X_test)}\n")

    # Build pipeline
    if classifier_type == "svm":
        pipeline = build_svm()
        print("Classifier: SVM (RBF kernel)")
    else:
        k = max(1, min(5, len(X_train) // len(np.unique(y_train))))
        pipeline = build_knn(k)
        print(f"Classifier: KNN (k={k})")

    # Cross-validation
    n_splits = min(5, len(np.unique(y_train)))
    cv       = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=cv, scoring="accuracy")
    print(f"CV Accuracy : {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    print(f"Per-fold    : {np.round(cv_scores, 4)}\n")

    # Final fit
    pipeline.fit(X_train, y_train)

    # Evaluate
    y_pred   = pipeline.predict(X_test)
    accuracy = (y_pred == y_test).mean()
    print(f"Test Accuracy: {accuracy * 100:.2f}%\n")
    print("Classification Report:")
    print(classification_report(y_test, y_pred, target_names=le.classes_))
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    # Save
    joblib.dump(pipeline, MODEL_OUT)
    joblib.dump(le, LABEL_ENC_OUT)
    print(f"\n✅ Model saved      → {MODEL_OUT}")
    print(f"✅ LabelEncoder     → {LABEL_ENC_OUT}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--classifier", choices=["svm", "knn"], default="svm")
    args = parser.parse_args()
    train(args.classifier)
