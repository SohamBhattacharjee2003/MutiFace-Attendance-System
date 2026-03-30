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
import matplotlib.pyplot as plt
import seaborn as sns

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
    report_str = classification_report(y_test, y_pred, target_names=le.classes_)
    report_dict = classification_report(y_test, y_pred, target_names=le.classes_, output_dict=True)
    print(report_str)
    print("Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(cm)

    try:
        # Plotting Confusion Matrix
        plt.figure(figsize=(10, 8))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=le.classes_, yticklabels=le.classes_)
        plt.title(f'{classifier_type.upper()} Confusion Matrix\nTest Accuracy: {accuracy * 100:.2f}%')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.tight_layout()
        cm_path = os.path.join(MODELS_DIR, f"{classifier_type}_confusion_matrix.png")
        plt.savefig(cm_path)
        plt.close()

        # Plotting Classification Report
        classes = list(le.classes_)
        metrics = ['precision', 'recall', 'f1-score']
        data = {metric: [report_dict[cls][metric] for cls in classes] for metric in metrics}
        
        x = np.arange(len(classes))
        width = 0.25
        
        fig, ax = plt.subplots(figsize=(12, 6))
        for i, metric in enumerate(metrics):
            ax.bar(x + i * width, data[metric], width, label=metric)
        
        ax.set_ylabel('Scores (0.0 to 1.0)')
        ax.set_title(f'{classifier_type.upper()} Classification Report Metrics')
        ax.set_xticks(x + width)
        ax.set_xticklabels(classes, rotation=45, ha='right')
        ax.legend()
        plt.ylim(0, 1.1)
        plt.tight_layout()
        cr_path = os.path.join(MODELS_DIR, f"{classifier_type}_classification_report.png")
        plt.savefig(cr_path)
        plt.close()
        print(f"\n✅ Plots saved        → {cm_path}, {cr_path}")
    except Exception as e:
        print(f"\n⚠️ Failed to generate plots: {e}. Please ensure matplotlib and seaborn are installed.")

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
