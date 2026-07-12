"""
evaluate.py
Produces the paper's results section: an ablation of every recognition guard, plus the
small-face degradation curve.

PROTOCOL (no human subjects needed — a simulated classroom drawn from VGGFace2)

    97 VGGFace2 identities
      ├── 30  ENROLLED  "students"
      │      ├── 70% of their images → enrollment (build the centroid)
      │      └── 30% of their images → GENUINE PROBES (never seen in enrollment)
      └── 67  STRANGERS (never enrolled; must always be rejected)
             ├── half → CALIBRATION (choose the threshold)
             └── half → IMPOSTOR PROBES (measure the false-accept rate)

The two splits that matter, and why:
  * enrollment vs probe images — scoring a face against a centroid built from that same
    face is measuring on training data. It always looks perfect and means nothing.
  * calibration vs impostor probes — a threshold chosen on the same strangers you then
    report FAR against is tuned to that sample. The reported FAR would be optimistic.

Usage:
    python scripts/evaluate.py                 # full ablation + curves
    python scripts/evaluate.py --students 30
"""

import os
import sys
import json
import argparse
from collections import defaultdict

import numpy as np
import cv2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import trainer
from arcface_engine import ArcFaceEngine

RESULTS_DIR = "results"
BASELINE_THRESHOLD = 0.32      # the hand-picked value the system originally shipped
SIZES = [16, 24, 32, 40, 48, 64, 80, 96, 112]   # simulated face width in pixels
MIN_FACE_PX = 60               # the size gate under test
SESSION_FRAMES = 5             # frames a person is seen for in one attendance session
VOTE_MIN = 3                   # sightings needed before attendance is written


# ── model built from enrollment images only ───────────────────────────────────
def build_centroids(X, y):
    cent = {}
    for name in np.unique(y):
        v = X[y == name].mean(axis=0)
        cent[name] = (v / np.linalg.norm(v)).astype(np.float32)
    return cent


def score(E, M):
    """(top1, top2, predicted_index) for each embedding against every centroid."""
    S = E @ M.T
    order = np.argsort(S, axis=1)[:, ::-1]
    idx = np.arange(len(E))
    top1 = S[idx, order[:, 0]]
    top2 = S[idx, order[:, 1]] if M.shape[0] > 1 else np.full(len(E), -1.0)
    return top1, top2, order[:, 0]


def decide(top1, top2, pred_i, names, threshold, margin):
    """Apply the rejection rules → predicted name or None (rejected)."""
    out = []
    for t1, t2, pi in zip(top1, top2, pred_i):
        if t1 < threshold:
            out.append(None)
        elif margin is not None and (t1 - t2) < margin:
            out.append(None)                      # too close to call between two students
        else:
            out.append(names[pi])
    return out


# ── temporal voting: does it stop one bad frame from logging a stranger? ───────
def false_log_rate(decisions, n_frames, vote_min, rng):
    """
    Group a person's frames into sessions. Without voting, ONE accepted frame writes
    attendance. With voting, vote_min frames must agree on the same name.
    Returns the fraction of sessions that wrote a name.
    """
    sessions, logged = 0, 0
    for i in range(0, len(decisions) - n_frames + 1, n_frames):
        window = decisions[i:i + n_frames]
        sessions += 1
        if vote_min <= 1:
            if any(d is not None for d in window):
                logged += 1
        else:
            counts = defaultdict(int)
            for d in window:
                if d is not None:
                    counts[d] += 1
            if counts and max(counts.values()) >= vote_min:
                logged += 1
    return logged / max(sessions, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--students", type=int, default=30)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    os.makedirs(RESULTS_DIR, exist_ok=True)

    print("Embedding dataset (cached)…")
    X, y, _ = trainer.embed_dataset(progress=None)

    # only the VGGFace2 pool — the 2 real webcam users are the deployment case study,
    # not the experiment (N=2 cannot support a quantitative claim)
    pool = np.array([trainer.is_impostor(n) for n in y])
    X, y = X[pool], y[pool]
    idents = np.unique(y)
    print(f"  pool: {len(idents)} identities, {len(X)} embeddings")

    # ── split identities: students vs strangers ──────────────────────────────
    shuffled = rng.permutation(idents)
    students = np.array(sorted(shuffled[:args.students]))
    strangers = np.array(sorted(shuffled[args.students:]))
    half = len(strangers) // 2
    calib_ids, test_ids = strangers[:half], strangers[half:]

    # ── split each student's images: enrollment vs genuine probes ────────────
    enrol_X, enrol_y, probe_X, probe_y = [], [], [], []
    for s in students:
        E = X[y == s]
        idx = rng.permutation(len(E))
        cut = int(0.7 * len(E))
        enrol_X.append(E[idx[:cut]]); enrol_y += [s] * cut
        probe_X.append(E[idx[cut:]]); probe_y += [s] * (len(E) - cut)
    enrol_X = np.vstack(enrol_X); enrol_y = np.array(enrol_y)
    probe_X = np.vstack(probe_X); probe_y = np.array(probe_y)

    calib_X = X[np.isin(y, calib_ids)]
    imp_X = X[np.isin(y, test_ids)]

    print(f"  students  : {len(students)}  (enrol {len(enrol_X)} / probe {len(probe_X)})")
    print(f"  strangers : {len(strangers)}  (calib {len(calib_X)} / test {len(imp_X)})")

    centroids = build_centroids(enrol_X, enrol_y)
    names = sorted(centroids)
    M = np.stack([centroids[n] for n in names])

    # ── calibrate the threshold on the CALIBRATION strangers only ────────────
    c_top1, _, _ = score(calib_X, M)
    calibrated = float(np.quantile(c_top1, 1.0 - trainer.TARGET_FAR))

    g_top1, g_top2, g_pred = score(probe_X, M)
    i_top1, i_top2, i_pred = score(imp_X, M)

    # margin = 5th percentile of genuine gaps, clamped (same rule the trainer uses)
    correct_mask = np.array([names[pi] == t for pi, t in zip(g_pred, probe_y)])
    margins_correct = (g_top1 - g_top2)[correct_mask]
    margin = float(np.clip(np.quantile(margins_correct, 0.05),
                           trainer.MIN_MARGIN, trainer.MAX_MARGIN))

    print(f"\n  calibrated threshold : {calibrated:.4f}  (baseline was {BASELINE_THRESHOLD})")
    print(f"  calibrated margin    : {margin:.4f}")

    # ── ablation ─────────────────────────────────────────────────────────────
    configs = [
        ("baseline (fixed 0.32, no guards)", BASELINE_THRESHOLD, None, False),
        ("+ calibrated threshold",            calibrated,         None, False),
        ("+ top-2 margin",                    calibrated,         margin, False),
        ("+ temporal voting",                 calibrated,         margin, True),
    ]

    rows = []
    print(f"\n{'configuration':<34} {'accuracy':>9} {'TAR':>7} {'FAR':>7} {'false-log':>10}")
    print("-" * 72)
    for label, thr, mrg, voting in configs:
        g_dec = decide(g_top1, g_top2, g_pred, names, thr, mrg)
        i_dec = decide(i_top1, i_top2, i_pred, names, thr, mrg)

        accepted = [d is not None for d in g_dec]
        correct = [d == t for d, t in zip(g_dec, probe_y)]
        tar = float(np.mean(accepted))
        acc = float(np.mean(correct))                      # accepted AND right name
        far = float(np.mean([d is not None for d in i_dec]))

        vm = VOTE_MIN if voting else 1
        flr = false_log_rate(list(i_dec), SESSION_FRAMES, vm, rng)

        rows.append({"config": label, "threshold": round(thr, 4),
                     "margin": round(mrg, 4) if mrg else None, "voting": voting,
                     "accuracy": round(acc, 4), "tar": round(tar, 4),
                     "far": round(far, 4), "false_log_rate": round(flr, 4)})
        print(f"{label:<34} {acc*100:>8.2f}% {tar*100:>6.1f}% {far*100:>6.2f}% {flr*100:>9.2f}%")

    # ── small-face degradation (needs no subjects at all) ────────────────────
    print(f"\nSmall-face degradation (size gate rejects < {MIN_FACE_PX}px)")
    print(f"{'face px':>8} {'mean cos':>9} {'accuracy':>9}  {'gate':>10}")
    print("-" * 42)
    engine = ArcFaceEngine.get()
    # re-embed a subset of probe images at each simulated distance
    probe_files = []
    for s in students[:12]:
        d = os.path.join(trainer.DATASET_DIR, str(s))
        fs = sorted(f for f in os.listdir(d) if f.lower().endswith(trainer.IMG_EXT))
        probe_files += [(str(s), os.path.join(d, f)) for f in fs[-3:]]

    curve = []
    for px in SIZES:
        cos, ok = [], []
        for name, path in probe_files:
            img = cv2.imread(path)
            if img is None:
                continue
            small = cv2.resize(img, (px, px), interpolation=cv2.INTER_AREA)
            back = cv2.resize(small, (112, 112), interpolation=cv2.INTER_LINEAR)
            e = engine.embed_precropped(back)
            if e is None:
                continue
            sims = M @ e
            cos.append(float(sims.max()))
            ok.append(names[int(np.argmax(sims))] == name)
        if not cos:
            continue
        gated = "REJECT" if px < MIN_FACE_PX else "accept"
        curve.append({"face_px": px, "mean_cos": round(float(np.mean(cos)), 4),
                      "accuracy": round(float(np.mean(ok)), 4), "gated": gated})
        print(f"{px:>8} {np.mean(cos):>9.3f} {np.mean(ok)*100:>8.1f}%  {gated:>10}")

    out = {
        "protocol": {
            "students": int(len(students)), "strangers": int(len(strangers)),
            "enrollment_images": int(len(enrol_X)), "genuine_probes": int(len(probe_X)),
            "calibration_impostors": int(len(calib_X)), "test_impostors": int(len(imp_X)),
            "seed": args.seed,
        },
        "calibrated_threshold": round(calibrated, 4),
        "calibrated_margin": round(margin, 4),
        "ablation": rows,
        "degradation": curve,
    }
    with open(os.path.join(RESULTS_DIR, "evaluation.json"), "w") as f:
        json.dump(out, f, indent=2)

    import csv
    with open(os.path.join(RESULTS_DIR, "ablation.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

    print(f"\nSaved → {RESULTS_DIR}/evaluation.json, {RESULTS_DIR}/ablation.csv")


if __name__ == "__main__":
    main()
