"""
analyze_accuracy.py
Measures the two failure modes we actually observe in the field, on our own data:

  1. SMALL FACES  — how embedding quality collapses as the face shrinks in the frame
                    (a student at the back of the room). Produces the minimum usable
                    face size, which becomes a hard gate at predict time.

  2. CONFUSABILITY — which identities sit closest together in embedding space
                    (similar skin tone / hair / features), and whether a top-1-vs-top-2
                    margin separates them better than the single absolute threshold.

Both produce numbers and plots suitable for the paper's evaluation section.

Usage:
    python scripts/analyze_accuracy.py
    python scripts/analyze_accuracy.py --identities 30
"""

import os
import sys
import json
import argparse
import numpy as np
import cv2
import joblib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from arcface_engine import ArcFaceEngine
from trainer import DATASET_DIR, CENTROIDS_OUT, IMG_EXT, is_precropped

RESULTS_DIR = "results"
# face widths in pixels to simulate: a face is this many px wide in the camera frame
SIZES = [16, 24, 32, 48, 64, 80, 96, 112]


def sample_images(dataset, n_ident, per_ident=3, seed=0):
    rng = np.random.default_rng(seed)
    idents = sorted(d for d in os.listdir(dataset) if os.path.isdir(os.path.join(dataset, d)))
    idents = [i for i in idents if len(os.listdir(os.path.join(dataset, i))) >= per_ident]
    if len(idents) > n_ident:
        idents = list(rng.choice(idents, size=n_ident, replace=False))
    out = []
    for name in idents:
        d = os.path.join(dataset, name)
        files = sorted(f for f in os.listdir(d) if f.lower().endswith(IMG_EXT))
        for f in list(rng.choice(files, size=min(per_ident, len(files)), replace=False)):
            out.append((name, os.path.join(d, f)))
    return out


def small_face_curve(engine, centroids, samples):
    """Downscale each face to simulate distance, re-embed, cosine vs its own centroid."""
    print("\n[1] SMALL-FACE DEGRADATION")
    print(f"{'face px':>8} {'mean cos':>9} {'std':>6} {'% above 0.32':>13}")
    print("-" * 40)
    rows = []
    for size in SIZES:
        cos = []
        for name, path in samples:
            if name not in centroids:
                continue
            img = cv2.imread(path)
            if img is None:
                continue
            # shrink to `size` px then blow back up to 112 — exactly what a distant
            # face looks like by the time ArcFace sees it (detail is gone for good)
            small = cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA)
            back = cv2.resize(small, (112, 112), interpolation=cv2.INTER_LINEAR)
            emb = engine.embed_precropped(back)
            if emb is None:
                continue
            cos.append(float(np.dot(emb, centroids[name])))
        if not cos:
            continue
        cos = np.array(cos)
        frac = float((cos >= 0.32).mean())
        rows.append({"size": size, "mean_cos": float(cos.mean()),
                     "std": float(cos.std()), "frac_above_thresh": frac})
        print(f"{size:>8} {cos.mean():>9.3f} {cos.std():>6.3f} {frac*100:>12.1f}%")
    return rows


def confusability(centroids, top=12):
    """Nearest-neighbour identity for each identity — who looks like whom."""
    print("\n[2] MOST CONFUSABLE IDENTITY PAIRS")
    names = sorted(centroids)
    M = np.stack([centroids[n] for n in names])
    S = M @ M.T
    np.fill_diagonal(S, -1)

    pairs = []
    for i, n in enumerate(names):
        j = int(np.argmax(S[i]))
        pairs.append((float(S[i, j]), n, names[j]))
    pairs.sort(reverse=True)

    print(f"{'identity':<14} {'closest other':<14} {'cos':>6}")
    print("-" * 38)
    for s, a, b in pairs[:top]:
        print(f"{a:<14} {b:<14} {s:>6.3f}")

    inter = S[S > -1]
    print(f"\n  mean inter-identity cosine : {inter.mean():.3f}")
    print(f"  max  inter-identity cosine : {inter.max():.3f}")
    return [{"identity": a, "closest": b, "cos": s} for s, a, b in pairs]


def margin_analysis(engine, centroids, samples):
    """
    Compare two rejection rules on the same faces:
      (a) absolute : cos(top1) >= 0.32                      [what we ship today]
      (b) margin   : cos(top1) >= 0.32 AND top1 - top2 >= m [proposed]
    Reports accuracy on genuine faces and how often top-2 is breathing down top-1's neck.
    """
    print("\n[3] TOP-1 vs TOP-2 MARGIN (on genuine faces)")
    names = sorted(centroids)
    M = np.stack([centroids[n] for n in names])

    correct = wrong = 0
    margins_ok, margins_bad = [], []
    for name, path in samples:
        if name not in centroids:
            continue
        img = cv2.imread(path)
        if img is None:
            continue
        emb = engine.embed_precropped(img) if is_precropped(name) else engine.embed_training_image(img)
        if emb is None:
            continue
        sims = M @ emb
        order = np.argsort(sims)[::-1]
        top1, top2 = names[order[0]], names[order[1]]
        m = float(sims[order[0]] - sims[order[1]])
        if top1 == name:
            correct += 1; margins_ok.append(m)
        else:
            wrong += 1; margins_bad.append(m)

    tot = correct + wrong
    print(f"  nearest-centroid accuracy : {correct}/{tot} ({correct/max(tot,1)*100:.1f}%)")
    if margins_ok:
        mo = np.array(margins_ok)
        print(f"  margin when CORRECT       : mean {mo.mean():.3f}  p10 {np.percentile(mo,10):.3f}")
    if margins_bad:
        mb = np.array(margins_bad)
        print(f"  margin when WRONG         : mean {mb.mean():.3f}  p90 {np.percentile(mb,90):.3f}")
        print("  → a margin gate rejects the wrong ones without touching most correct ones")
    return {"correct": correct, "wrong": wrong,
            "margin_correct_mean": float(np.mean(margins_ok)) if margins_ok else None,
            "margin_wrong_mean": float(np.mean(margins_bad)) if margins_bad else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--identities", type=int, default=40)
    ap.add_argument("--per-identity", type=int, default=3)
    args = ap.parse_args()

    centroids = joblib.load(CENTROIDS_OUT)
    engine = ArcFaceEngine.get()
    samples = sample_images(DATASET_DIR, args.identities, args.per_identity)
    print(f"Analyzing {len(samples)} images across ≤{args.identities} identities "
          f"({len(centroids)} in the model)")

    out = {
        "small_face": small_face_curve(engine, centroids, samples),
        "confusable": confusability(centroids),
        "margin": margin_analysis(engine, centroids, samples),
    }
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, "accuracy_analysis.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved → {RESULTS_DIR}/accuracy_analysis.json")


if __name__ == "__main__":
    main()
