"""
liveness.py
Anti-spoofing: is this a person, or a photograph of a person?

THE ATTACK IT STOPS
    Face recognition alone cannot tell a person from a photo of that person — the embedding
    is nearly identical, which is precisely what a good face model is built to do. So an
    attendance system built on recognition alone is trivially defeated: hold up a printed
    photo, or a phone showing a friend's face, and they are marked present. That is exactly
    the "proxy attendance" such systems claim to prevent, and measurably they do not:
    scripts/test_spoof.py puts the attack success rate at 100% without this module.

HOW — facial motion (primary signal)
    A live face never holds still: micro-expressions, small 3-D head rotations, the jaw and
    brows all keep moving. A photograph is rigid. We compare the face's SHAPE across frames
    after dividing out translation, in-plane rotation and scale — so waving the photo about
    does not help the attacker, because all three of those are normalized away. What is left
    is pure deformation, which only a real face produces.

    Measured on this project's own users:
        photo held up (hand-shake + sensor noise) : 0.015
        Arnab, live                                : 0.066
        Soham, live                                : 0.135
    Threshold sits at 0.035, between the two populations.

    This signal was chosen because it survives the frame rate we actually run at. The live
    page samples ~0.67 fps; a blink lasts ~0.3s and is therefore almost never *sampled*, so
    a blink-only design leaves real users stuck on "please blink" indefinitely. Facial
    motion, by contrast, is easier to see the further apart the frames are.

HOW — blink (secondary signal)
    Retained because a caught blink is conclusive, but it can no longer be the only way to
    pass. Eye-aspect-ratio is judged against each person's OWN open-eye baseline: Arnab's
    open eye measures 0.51 and Soham's 0.27, so any fixed constant declares one of them
    permanently shut.

LIMITS (state these honestly)
    A *video* replay of a real person would defeat this — the recorded face moves. Beating
    that needs a texture/depth-based passive anti-spoof model. What this buys is raising the
    attack cost from "print a photo" to "record and replay a video". That is a large
    practical gain, not a complete defence, and the report should say so.
"""

import time
import threading
from collections import defaultdict, deque

import numpy as np

# 106-point landmark indices for the eye contours (verified against the 5-point kps)
LEFT_EYE = list(range(33, 43))
RIGHT_EYE = list(range(87, 97))

# ── Signal 1: facial motion (primary) ────────────────────────────────────────
# The live page samples ~1 frame every 1.5s (0.67 fps). A blink lasts ~0.3s, so a blink is
# almost never *sampled* at that rate — blink detection alone leaves a real person stuck on
# "please blink" forever. Facial motion is the signal that actually works at low frame
# rates, and it gets *easier* the further apart the frames are.
#
# We compare the face's SHAPE between frames after removing translation, in-plane rotation
# and scale. That normalization is the whole trick: waving a photo around changes all three,
# and they are divided out — so a rigid photo has almost no shape change, while a live face
# never stops changing (micro-expressions, 3-D head pose).
#
# Measured on this project's own data:
#     photo held up (hand-shake + sensor noise) : 0.015
#     Soham, live                                : 0.135
#     Arnab, live                                : 0.066
MOTION_THRESHOLD = 0.035   # ~2x the photo value, ~2x below the quietest real user

# ── Signal 2: blink (bonus) ──────────────────────────────────────────────────
# Kept because when a blink IS caught it is strong evidence, but it can no longer be the
# only way to pass. Thresholds are relative to each person's own open-eye baseline:
# Arnab's open eye reads 0.51, Soham's 0.27 — any fixed constant calls one of them shut.
CLOSE_RATIO = 0.65     # eye counts as shut below 65% of that person's baseline
OPEN_RATIO = 0.85      # and open again above 85% (hysteresis stops threshold flapping)
BASELINE_PCTL = 90     # "eyes open" = the 90th percentile of their recent EARs

MIN_SAMPLES = 3        # frames before we can judge at all (~2s at 0.7s/frame)
# A real person who happens to be sitting still for a moment has not yet produced enough
# motion to pass — but calling them a SPOOF at that point is a false alarm, and it is what
# made the UI flash "not live (photo?)" at a genuine user. Until this many frames have
# accumulated we say "checking"; only a face that stays rigid this long is called out.
SPOOF_AFTER = 7
LIVE_WINDOW = 30.0     # seconds a liveness pass stays fresh
HISTORY = 40           # per-identity samples kept

_lock = threading.Lock()
_history = defaultdict(lambda: deque(maxlen=HISTORY))   # identity -> [(ts, ear, shape)]
_last_live = {}                                         # identity -> timestamp


def normalized_shape(landmarks):
    """
    Face shape with translation, scale and in-plane rotation removed.

    Anchored on the two eye centres: they define the face's position, size and roll, so
    dividing them out leaves only how the face is *deforming* — which is what separates a
    person from a photograph of a person.
    """
    p = np.asarray(landmarks, dtype=np.float32)
    if p.shape[0] < 97:
        return None
    eye_l = p[LEFT_EYE].mean(axis=0)
    eye_r = p[RIGHT_EYE].mean(axis=0)
    centre = (eye_l + eye_r) / 2.0
    axis = eye_r - eye_l
    scale = float(np.linalg.norm(axis))
    if scale < 1e-6:
        return None
    ang = float(np.arctan2(axis[1], axis[0]))
    c, s = np.cos(-ang), np.sin(-ang)
    rot = np.array([[c, -s], [s, c]], dtype=np.float32)
    return ((p - centre) @ rot.T) / scale


def _motion(shapes):
    """Mean per-landmark deviation from the average shape — 0 for a rigid photo."""
    if len(shapes) < 2:
        return 0.0
    S = np.stack(shapes)
    return float(np.linalg.norm(S - S.mean(axis=0), axis=2).mean())


def eye_aspect_ratio(landmarks):
    """
    Height/width of the eye contour, averaged over both eyes.

    Uses the bounding box of each eye's contour points rather than hand-picked lid
    landmarks, so it does not depend on the exact ordering of points within the contour —
    only on which points belong to which eye.
    """
    if landmarks is None or len(landmarks) < 97:
        return None

    ratios = []
    for idx in (LEFT_EYE, RIGHT_EYE):
        pts = np.asarray(landmarks)[idx]
        w = float(pts[:, 0].max() - pts[:, 0].min())
        h = float(pts[:, 1].max() - pts[:, 1].min())
        if w <= 1e-6:
            continue
        ratios.append(h / w)
    return float(np.mean(ratios)) if ratios else None


def update(identity, landmarks, now=None):
    """
    Feed one frame's landmarks for a recognized identity.

    Passes on EITHER signal:
      * the face is moving/deforming like a real face (works at 0.67 fps), or
      * a blink was caught (rare at this frame rate, but conclusive when it happens).

    Returns (is_live, ear, state).
    """
    now = now or time.time()
    ear = eye_aspect_ratio(landmarks)
    shape = normalized_shape(landmarks) if landmarks is not None else None

    if ear is None or shape is None:
        return False, None, "no_landmarks"

    with _lock:
        hist = _history[identity]
        hist.append((now, ear, shape))

        recent = [(e, s) for ts, e, s in hist if now - ts <= LIVE_WINDOW]
        if len(recent) < MIN_SAMPLES:
            return False, ear, "checking"          # not enough frames to judge yet

        ears = [e for e, _ in recent]
        shapes = [s for _, s in recent]

        motion = _motion(shapes)
        moving = motion >= MOTION_THRESHOLD

        # blink: eye collapsed below this person's own baseline, then reopened
        baseline = float(np.percentile(ears, BASELINE_PCTL))
        blinked = False
        if baseline > 1e-6:
            blinked = (any(e < CLOSE_RATIO * baseline for e in ears[:-1])
                       and ears[-1] > OPEN_RATIO * baseline)

        if moving or blinked:
            _last_live[identity] = now

        live_ts = _last_live.get(identity)
        fresh = live_ts is not None and (now - live_ts) <= LIVE_WINDOW
        seen = len(recent)

    if fresh:
        return True, ear, "live"
    # Still gathering evidence — a real person may simply have been still so far.
    if seen < SPOOF_AFTER:
        return False, ear, "checking"
    # Rigid for this long is what a photograph looks like.
    return False, ear, "spoof_suspected"


def reset(identity=None):
    """Clear tracked state (whole store, or one identity)."""
    with _lock:
        if identity is None:
            _history.clear(); _last_live.clear()
        else:
            _history.pop(identity, None); _last_live.pop(identity, None)
