"""
trainer.py
Shared training core for the ArcFace pipeline — used by both scripts/train_arcface.py
(research metrics) and api.py (auto-retrain on registration).

The expensive step is embedding images through ArcFace on CPU (~2400 images takes
minutes). Registering one student should not pay that cost again, so embeddings are
cached on disk keyed by (identity, filename, filesize). A retrain after a new
registration only embeds that student's images and reuses everything else.

    embed_dataset(...)  → (X, y), embedding only cache misses
    fit_and_save(...)   → SVM + label encoder + centroids, written to models/
    retrain(...)        → both of the above; returns a summary dict
"""

import os
import re
import json
import zlib
import numpy as np
import cv2
import joblib
from sklearn.preprocessing import LabelEncoder

from arcface_engine import ArcFaceEngine


# ── Where state lives ────────────────────────────────────────────────────────
# Everything the system must NOT lose on a restart — enrolment images, the trained
# centroids, attendance CSVs, teacher accounts — lives under one root. In development
# that root is the current directory; in a container it is a MOUNTED VOLUME, so a redeploy
# or a crash does not wipe every enrolled student.
#
#     STATE_DIR=/data python api.py
STATE_DIR = os.getenv("STATE_DIR", ".")

DATASET_DIR   = os.path.join(STATE_DIR, "processed_dataset")
MODELS_DIR    = os.path.join(STATE_DIR, "models")
LE_OUT        = os.path.join(MODELS_DIR, "arcface_label_encoder.pkl")
CENTROIDS_OUT = os.path.join(MODELS_DIR, "arcface_centroids.pkl")
CACHE_OUT     = os.path.join(MODELS_DIR, "arcface_embedding_cache.pkl")
THRESH_OUT    = os.path.join(MODELS_DIR, "arcface_thresholds.json")

IMG_EXT       = (".jpg", ".jpeg", ".png", ".bmp")
MAX_PER_CLASS = 30
MIN_PER_CLASS = 8

TARGET_FAR    = 0.01    # accept at most 1% of impostors → sets the cosine threshold
MIN_MARGIN    = 0.02    # floor on the top1−top2 gap, even if genuine data allows less
# Ceiling on the margin. With few enrolled students the genuine top1−top2 gap is huge
# (you score ~0.6 against yourself and ~0.05 against the only other student), so the
# percentile rule would demand a gap that a slightly off-pose genuine face cannot meet.
# The margin exists to break ties between lookalikes, not to act as a second threshold.
MAX_MARGIN    = 0.15

# Fallbacks when there is no impostor cohort to calibrate against.
DEFAULT_THRESHOLDS = {"cos_threshold": 0.32, "margin": 0.05, "calibrated": False}

VGGFACE2_RE = re.compile(r"^n\d{6}$")


def is_precropped(name):
    """VGGFace2 identities (n000xxx) are already MTCNN-cropped → skip detection."""
    return name.lower().startswith("n0")


def is_impostor(name):
    """
    VGGFace2 celebrities are not enrolled students — they will never walk into the
    room. Training them as classes forces the decision boundaries through irrelevant
    regions of embedding space and gives every real student ~96 extra ways to be
    misclassified. They are far more useful as a held-out impostor cohort for
    calibrating the open-set rejection threshold, which is what we use them for.
    """
    return bool(VGGFACE2_RE.match(name))


def load_cache():
    try:
        return joblib.load(CACHE_OUT)
    except Exception:          # noqa: BLE001 — missing or stale cache is not fatal
        return {}


def _cache_key(name, path):
    """Filesize guards against a filename being reused for different image bytes."""
    try:
        return (name, os.path.basename(path), os.path.getsize(path))
    except OSError:
        return (name, os.path.basename(path), -1)


def _sample_files(name, files, max_per_class, seed):
    """
    Deterministically pick ≤max_per_class files for one identity.

    The RNG is seeded per-identity (not from one stream shared across the dataset),
    so an identity's sample depends only on its own name and files. A shared stream
    would make every identity's draw depend on how many draws earlier identities
    consumed — so enrolling one new student would re-roll the sample for everyone
    after them and invalidate their cached embeddings, which is exactly the bug this
    avoids. crc32, not hash(), because hash() is salted per process.
    """
    if len(files) <= max_per_class:
        return files
    rng = np.random.default_rng(seed + zlib.crc32(name.encode()))
    return sorted(rng.choice(files, size=max_per_class, replace=False).tolist())


def embed_dataset(dataset=DATASET_DIR, max_per_class=MAX_PER_CLASS,
                  min_per_class=MIN_PER_CLASS, seed=42, use_cache=True, progress=None):
    """
    Embed every identity folder under `dataset`. Cache hits skip the ArcFace forward
    pass entirely. Returns (X, y, info) where info reports what was skipped and why.
    """
    cache = load_cache() if use_cache else {}
    engine = ArcFaceEngine.get()

    X, y = [], []
    embedded, cached, skipped = 0, 0, []

    identities = sorted(d for d in os.listdir(dataset)
                        if os.path.isdir(os.path.join(dataset, d)))

    for name in identities:
        d = os.path.join(dataset, name)
        files = sorted(f for f in os.listdir(d) if f.lower().endswith(IMG_EXT))

        if len(files) < min_per_class:
            skipped.append({"name": name, "images": len(files),
                            "reason": f"needs ≥{min_per_class} images"})
            continue
        files = _sample_files(name, files, max_per_class, seed)

        if progress:
            progress(f"Embedding {name} ({len(files)} images)…")

        # pre-cropped dataset faces → fast recogniser-only path;
        # real registrations (webcam frames) → full detect+align.
        embed = engine.embed_precropped if is_precropped(name) else engine.embed_training_image

        got = 0
        for f in files:
            path = os.path.join(d, f)
            key = _cache_key(name, path)
            if key in cache:
                X.append(cache[key]); y.append(name); got += 1; cached += 1
                continue
            img = cv2.imread(path)
            if img is None:
                continue
            emb = embed(img)
            if emb is None:
                continue                     # no face found in this image
            cache[key] = emb
            X.append(emb); y.append(name); got += 1; embedded += 1

        if got < min_per_class:              # couldn't embed enough → drop the identity
            keep = [i for i, lab in enumerate(y) if lab != name]
            X = [X[i] for i in keep]; y = [y[i] for i in keep]
            skipped.append({"name": name, "images": len(files),
                            "reason": f"only {got} embeddable face(s), needs ≥{min_per_class}"})

    if use_cache:
        os.makedirs(MODELS_DIR, exist_ok=True)
        joblib.dump(cache, CACHE_OUT)

    info = {"embedded": embedded, "from_cache": cached, "skipped": skipped}
    return np.array(X, dtype=np.float32), np.array(y), info


def _top2(sims):
    """(best, runner-up) cosine from a vector of similarities to every centroid."""
    if len(sims) == 1:
        return float(sims[0]), -1.0
    order = np.argpartition(sims, -2)[-2:]
    a, b = sorted(sims[order], reverse=True)
    return float(a), float(b)


def calibrate(centroids, X_imp, X_gen, y_gen):
    """
    Choose the two decision parameters from data instead of guessing them.

      cos_threshold — the top-1 cosine an impostor must NOT reach. Set at the
                      (1 - TARGET_FAR) percentile of impostor top-1 scores, i.e. the
                      point where only TARGET_FAR of non-students get let in.
      margin        — how far top-1 must beat top-2. Guards against two enrolled
                      students who look alike, where the absolute score is high for
                      both and the absolute threshold alone cannot separate them.

    Also reports TAR@FAR — the fraction of genuine faces still accepted at that
    threshold — which is the headline open-set number for the paper.
    """
    names = sorted(centroids)
    M = np.stack([centroids[n] for n in names])

    if len(X_imp) == 0:
        # No impostor cohort present — which is the normal case in DEPLOYMENT, where the
        # 2,880 VGGFace2 faces are not shipped (they are a research artifact, ~300MB, and
        # only ever needed to CHOOSE the threshold). Reuse the thresholds already
        # calibrated against them rather than silently reverting to the hand-picked
        # defaults, which is what a fresh enrolment on the server would otherwise do.
        if os.path.exists(THRESH_OUT):
            try:
                with open(THRESH_OUT) as f:
                    existing = json.load(f)
                if existing.get("calibrated"):
                    return existing
            except Exception:      # noqa: BLE001 — a corrupt file must not block enrolment
                pass
        return dict(DEFAULT_THRESHOLDS)

    imp_top1 = np.array([_top2(M @ e)[0] for e in X_imp])
    cos_threshold = float(np.quantile(imp_top1, 1.0 - TARGET_FAR))

    # Keep the margin low enough not to reject genuine faces (5th percentile of the genuine
    # top1−top2 gap), but never below the floor.
    #
    # The runner-up must be a DIFFERENT PERSON. A student enrolled in two classes has two
    # centroids for the same face, so their own second centroid sits almost on top of the
    # first — a gap near zero. Counting that as a "genuine margin" collapsed the calibrated
    # margin (we measured it fall to 0.043), which silently disarmed the look-alike guard
    # for everyone. Same roll number = same human, so skip it.
    def _person(label):
        return label.split("__", 1)[1] if "__" in label else label

    gen_margins = []
    gen_top1 = []
    for e, lab in zip(X_gen, y_gen):
        sims = M @ e
        order = np.argsort(sims)[::-1]
        t1 = float(sims[order[0]])
        gen_top1.append(t1)
        if names[order[0]] != lab:
            continue
        rival = next((i for i in order[1:] if _person(names[i]) != _person(lab)), None)
        if rival is not None:
            gen_margins.append(t1 - float(sims[rival]))
    margin = (float(np.clip(np.quantile(gen_margins, 0.05), MIN_MARGIN, MAX_MARGIN))
              if gen_margins else MIN_MARGIN)

    gen_top1 = np.array(gen_top1)
    tar = float((gen_top1 >= cos_threshold).mean()) if len(gen_top1) else 0.0

    return {
        "cos_threshold": round(cos_threshold, 4),
        "margin": round(margin, 4),
        "calibrated": True,
        "target_far": TARGET_FAR,
        "tar_at_far": round(tar, 4),          # genuine faces still accepted
        "impostor_embeddings": int(len(X_imp)),
        "impostor_top1_mean": round(float(imp_top1.mean()), 4),
        "impostor_top1_max": round(float(imp_top1.max()), 4),
    }


def fit_and_save(X, y, X_imp=None):
    """
    Build one centroid per student, calibrate the gates, write the artifacts.

    There is no classifier. ArcFace was trained to push different people apart and pull
    the same person together, so the embedding space is ALREADY separated — identifying a
    face is "which centroid is nearest?", a matrix multiply, not a learned boundary.

    Dropping the SVM is not just simpler, it is required by the design:
      * a softmax MUST name one of its classes; it cannot answer "nobody", which is the
        whole point of an open-set attendance system
      * we need the RUNNER-UP score for the margin gate, and an SVM only returns its winner
      * a new student becomes one more row, not a retrain — which is why enrolment is 1.4s
    """
    classes = np.unique(y)
    if len(classes) < 1:
        raise ValueError("no enrolled students to build a model from")

    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    # per-identity centroid (mean embedding, re-normalized) → cosine confidence at predict time
    centroids = {}
    for name in classes:
        v = X[y == name].mean(axis=0)
        centroids[name] = (v / np.linalg.norm(v)).astype(np.float32)

    thresholds = calibrate(centroids, X_imp if X_imp is not None else np.empty((0, X.shape[1])), X, y)

    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(le, LE_OUT)
    joblib.dump(centroids, CENTROIDS_OUT)
    with open(THRESH_OUT, "w") as f:
        json.dump(thresholds, f, indent=2)

    return le, centroids, thresholds


def retrain(dataset=DATASET_DIR, students_only=True, progress=None):
    """
    Embed (cached) + fit + calibrate + save.

    students_only=True trains the classifier on enrolled students alone and keeps the
    VGGFace2 identities purely as an impostor cohort for threshold calibration. Set it
    False to train the full N-class model (what the paper's comparison run uses).
    """
    if progress:
        progress("Loading ArcFace engine…")
    X, y, info = embed_dataset(dataset=dataset, progress=progress)

    if students_only:
        imp_mask = np.array([is_impostor(n) for n in y])
        X_imp = X[imp_mask]
        X_gen, y_gen = X[~imp_mask], y[~imp_mask]
        if len(np.unique(y_gen)) < 1:
            # nobody has enrolled yet — fall back to the full set so /predict still has
            # something to load rather than crashing on an empty model
            if progress:
                progress("No enrolled students yet; using all identities.")
            X_gen, y_gen, X_imp = X, y, np.empty((0, X.shape[1]), dtype=np.float32)
            students_only = False
    else:
        X_gen, y_gen = X, y
        X_imp = np.empty((0, X.shape[1]), dtype=np.float32)

    if progress:
        progress(f"Building centroids from {len(X_gen)} embeddings / "
                 f"{len(np.unique(y_gen))} students ({len(X_imp)} impostors held out)…")
    le, centroids, thresholds = fit_and_save(X_gen, y_gen, X_imp)

    return {
        "identities": int(len(le.classes_)),
        "names": [str(c) for c in le.classes_],
        "images": int(len(X_gen)),
        "students_only": students_only,
        "impostors_held_out": int(len(X_imp)),
        "thresholds": thresholds,
        "newly_embedded": info["embedded"],
        "from_cache": info["from_cache"],
        "skipped": info["skipped"],
        "_model": (le, centroids, thresholds),
    }
