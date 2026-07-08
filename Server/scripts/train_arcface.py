"""
train_arcface.py
Train + evaluate the ArcFace face-recognition pipeline and emit research-paper
metrics (identification + verification).

Pipeline:  image → MTCNN/RetinaFace detect+align → ArcFace-R50 512-d embedding
           → linear SVM classifier  (embeddings are L2-normalized, so a linear
           SVM is equivalent to cosine-margin classification).

Outputs (under results/):
    arcface_metrics.json              all scalar metrics
    arcface_classification_report.csv per-class precision/recall/F1
    arcface_confusion_matrix.png      confusion matrix heatmap
    arcface_roc_curve.png             verification ROC curve
And the trained model under models/:
    arcface_classifier.pkl, arcface_label_encoder.pkl

Usage:
    python scripts/train_arcface.py                     # sensible defaults
    python scripts/train_arcface.py --max-per-class 40 --test-size 0.3
"""

import os
import sys
import json
import argparse
import numpy as np
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # Server/ on path

import cv2
import joblib
from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import (accuracy_score, precision_recall_fscore_support,
                             classification_report, confusion_matrix, roc_auc_score,
                             roc_curve)

from arcface_engine import ArcFaceEngine

DATASET_DIR   = "processed_dataset"
MODELS_DIR    = "models"
RESULTS_DIR   = "results"
CLF_OUT       = os.path.join(MODELS_DIR, "arcface_classifier.pkl")
LE_OUT        = os.path.join(MODELS_DIR, "arcface_label_encoder.pkl")
CENTROIDS_OUT = os.path.join(MODELS_DIR, "arcface_centroids.pkl")

IMG_EXT = (".jpg", ".jpeg", ".png", ".bmp")


def is_precropped(name):
    """VGGFace2 identities (n000xxx) are already MTCNN-cropped → skip detection."""
    return name.lower().startswith("n0")


def build_embeddings(engine, dataset, max_per_class, min_per_class, seed):
    rng = np.random.default_rng(seed)
    X, y = [], []
    identities = sorted(d for d in os.listdir(dataset)
                        if os.path.isdir(os.path.join(dataset, d)))

    for name in tqdm(identities, desc="Embedding identities"):
        d = os.path.join(dataset, name)
        files = [f for f in os.listdir(d) if f.lower().endswith(IMG_EXT)]
        if len(files) < min_per_class:
            continue
        if len(files) > max_per_class:
            files = list(rng.choice(files, size=max_per_class, replace=False))

        # pre-cropped dataset faces → fast recogniser-only path;
        # real registrations (webcam frames) → full detect+align.
        embed = engine.embed_precropped if is_precropped(name) else engine.embed_training_image

        got = 0
        for f in files:
            img = cv2.imread(os.path.join(d, f))
            if img is None:
                continue
            emb = embed(img)
            if emb is not None:
                X.append(emb); y.append(name); got += 1
        if got < min_per_class:                     # drop identities we couldn't embed
            keep = [i for i, lab in enumerate(y) if lab != name]
            X = [X[i] for i in keep]; y = [y[i] for i in keep]

    return np.array(X, dtype=np.float32), np.array(y)


def verification_metrics(X_test, y_test, seed, max_pairs=20000):
    """Cosine-similarity verification (1:1). Returns AUC, EER, acc@EER, ROC pts."""
    rng = np.random.default_rng(seed)
    n = len(X_test)
    idx = np.arange(n)
    a = rng.choice(idx, size=min(max_pairs, n * 4), replace=True)
    b = rng.choice(idx, size=len(a), replace=True)
    mask = a != b
    a, b = a[mask], b[mask]
    sims = np.sum(X_test[a] * X_test[b], axis=1)        # cosine (unit vectors)
    labels = (y_test[a] == y_test[b]).astype(int)
    if labels.sum() == 0 or labels.sum() == len(labels):
        return None
    auc = roc_auc_score(labels, sims)
    fpr, tpr, thr = roc_curve(labels, sims)
    fnr = 1 - tpr
    eer_i = np.nanargmin(np.abs(fnr - fpr))
    eer = float((fpr[eer_i] + fnr[eer_i]) / 2)
    thr_eer = float(thr[eer_i])
    acc = float(((sims >= thr_eer).astype(int) == labels).mean())
    return {"auc": float(auc), "eer": eer, "threshold_at_eer": thr_eer,
            "verification_accuracy": acc, "n_pairs": int(len(labels)),
            "positive_pairs": int(labels.sum()),
            "_roc": (fpr.tolist(), tpr.tolist())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default=DATASET_DIR)
    ap.add_argument("--max-per-class", type=int, default=30)
    ap.add_argument("--min-per-class", type=int, default=8)
    ap.add_argument("--test-size", type=float, default=0.3)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)

    print("Loading ArcFace engine (buffalo_l)…")
    engine = ArcFaceEngine.get()

    print(f"\nEmbedding dataset '{args.dataset}' "
          f"(≤{args.max_per_class}/identity, ≥{args.min_per_class} to keep)…")
    X, y = build_embeddings(engine, args.dataset,
                            args.max_per_class, args.min_per_class, args.seed)
    classes = np.unique(y)
    print(f"\n  Embeddings : {X.shape}")
    print(f"  Identities : {len(classes)}")

    if len(classes) < 2:
        print("Need ≥2 identities with enough images. Aborting."); return

    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    # per-identity centroid (mean, L2-normalized) → used for cosine confidence
    centroids = {}
    for name in classes:
        v = X[y == name].mean(axis=0)
        centroids[name] = (v / np.linalg.norm(v)).astype(np.float32)
    joblib.dump(centroids, CENTROIDS_OUT)

    Xtr, Xte, ytr, yte = train_test_split(
        X, y_enc, test_size=args.test_size, random_state=args.seed, stratify=y_enc)
    print(f"  Train/Test : {len(Xtr)} / {len(Xte)}")

    print("\nTraining linear SVM on ArcFace embeddings…")
    clf = SVC(kernel="linear", probability=True, C=1.0)
    clf.fit(Xtr, ytr)

    # ── Identification (closed-set) metrics ──────────────────────────────────
    ypred = clf.predict(Xte)
    acc = accuracy_score(yte, ypred)
    p_macro, r_macro, f_macro, _ = precision_recall_fscore_support(
        yte, ypred, average="macro", zero_division=0)
    p_w, r_w, f_w, _ = precision_recall_fscore_support(
        yte, ypred, average="weighted", zero_division=0)

    report = classification_report(yte, ypred, target_names=le.classes_,
                                   output_dict=True, zero_division=0)

    # ── Verification (1:1) metrics ───────────────────────────────────────────
    ver = verification_metrics(Xte, yte, args.seed)

    metrics = {
        "model": "ArcFace R50 (buffalo_l) + linear SVM",
        "embedding_dim": int(X.shape[1]),
        "identities": int(len(classes)),
        "images_embedded": int(len(X)),
        "train_size": int(len(Xtr)), "test_size": int(len(Xte)),
        "identification": {
            "accuracy": float(acc),
            "precision_macro": float(p_macro), "recall_macro": float(r_macro),
            "f1_macro": float(f_macro),
            "precision_weighted": float(p_w), "recall_weighted": float(r_w),
            "f1_weighted": float(f_w),
        },
        "verification": {k: v for k, v in (ver or {}).items() if not k.startswith("_")},
    }
    with open(os.path.join(RESULTS_DIR, "arcface_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    # per-class CSV
    import csv
    with open(os.path.join(RESULTS_DIR, "arcface_classification_report.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["identity", "precision", "recall", "f1", "support"])
        for k, v in report.items():
            if isinstance(v, dict) and "precision" in v:
                w.writerow([k, f"{v['precision']:.4f}", f"{v['recall']:.4f}",
                            f"{v['f1-score']:.4f}", int(v['support'])])

    # plots
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        cm = confusion_matrix(yte, ypred)
        plt.figure(figsize=(10, 9))
        plt.imshow(cm, cmap="viridis")
        plt.title(f"ArcFace Confusion Matrix ({len(classes)} identities)")
        plt.xlabel("Predicted"); plt.ylabel("True"); plt.colorbar()
        plt.tight_layout()
        plt.savefig(os.path.join(RESULTS_DIR, "arcface_confusion_matrix.png"), dpi=150)
        plt.close()

        if ver:
            fpr, tpr = ver["_roc"]
            plt.figure(figsize=(6, 6))
            plt.plot(fpr, tpr, label=f"AUC = {ver['auc']:.4f}")
            plt.plot([0, 1], [0, 1], "--", color="gray")
            plt.title("ArcFace Verification ROC"); plt.xlabel("False Positive Rate")
            plt.ylabel("True Positive Rate"); plt.legend(loc="lower right")
            plt.tight_layout()
            plt.savefig(os.path.join(RESULTS_DIR, "arcface_roc_curve.png"), dpi=150)
            plt.close()
    except Exception as e:            # noqa: BLE001
        print("  (plotting skipped:", e, ")")

    # save model
    joblib.dump(clf, CLF_OUT)
    joblib.dump(le, LE_OUT)

    # ── paper-ready summary ──────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  RESULTS  —  ArcFace R50 + linear SVM")
    print("=" * 60)
    print(f"  Identities (classes) : {len(classes)}")
    print(f"  Images embedded      : {len(X)}   (train {len(Xtr)} / test {len(Xte)})")
    print(f"  Embedding dimension  : {X.shape[1]}")
    print("  ── Identification (closed-set) ──")
    print(f"    Accuracy           : {acc*100:.2f}%")
    print(f"    Precision (macro)  : {p_macro*100:.2f}%")
    print(f"    Recall    (macro)  : {r_macro*100:.2f}%")
    print(f"    F1-score  (macro)  : {f_macro*100:.2f}%")
    print(f"    F1-score  (weighted): {f_w*100:.2f}%")
    if ver:
        print("  ── Verification (1:1, cosine) ──")
        print(f"    ROC-AUC            : {ver['auc']:.4f}")
        print(f"    EER                : {ver['eer']*100:.2f}%")
        print(f"    Acc @ EER thresh   : {ver['verification_accuracy']*100:.2f}%")
    print("=" * 60)
    print(f"  Saved model  → {CLF_OUT}")
    print(f"  Saved metrics→ {RESULTS_DIR}/arcface_metrics.json (+ plots, CSV)")
    print("=" * 60)


if __name__ == "__main__":
    main()
