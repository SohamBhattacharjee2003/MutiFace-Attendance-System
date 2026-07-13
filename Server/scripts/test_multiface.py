"""
test_multiface.py
End-to-end test of MULTI-face recognition: builds a composite frame containing
several known identities, POSTs it to /predict, and checks that every face is
detected and correctly named.

This exercises the same path the web LiveAttendance page uses
(ArcFace detect+embed → SVM → cosine-vs-centroid threshold), which the CLI
attendance.py does NOT (that one still runs the legacy dlib classifier).

Usage (api.py must already be running on :5000):
    python scripts/test_multiface.py                  # 4 random trained identities
    python scripts/test_multiface.py --faces 6
    python scripts/test_multiface.py --names Soham n000002 n000005
    python scripts/test_multiface.py --save out.jpg   # write the composite frame
"""

import os
import io
import glob
import base64
import random
import argparse

import cv2
import joblib
import numpy as np
import requests

API          = os.getenv("API_URL", "http://127.0.0.1:5000")
DATASET_DIR  = "processed_dataset"
ARCFACE_LE   = os.path.join("models", "arcface_label_encoder.pkl")

# Detection needs context around the face; the dataset holds tight 160px crops,
# so each tile gets padding and an upscale before being placed on the canvas.
TILE      = 320
PAD       = 60
COLS      = 3


def trained_names():
    """Identities the classifier actually knows (dataset dirs alone aren't enough)."""
    le = joblib.load(ARCFACE_LE)
    return [str(c) for c in le.classes_]


def pick_image(name):
    files = sorted(glob.glob(os.path.join(DATASET_DIR, name, "*.jpg")))
    return files[-1] if files else None   # last image ≈ least likely to be in train split


def build_composite(names):
    """Tile one face per identity onto a single canvas, padded so RetinaFace can detect."""
    cols = min(COLS, len(names))
    rows = (len(names) + cols - 1) // cols
    cell = TILE + 2 * PAD
    canvas = np.full((rows * cell, cols * cell, 3), 200, dtype=np.uint8)

    placed = []
    for i, name in enumerate(names):
        path = pick_image(name)
        if not path:
            print(f"  ⚠ no images for {name}, skipping")
            continue
        face = cv2.resize(cv2.imread(path), (TILE, TILE))
        r, c = divmod(i, cols)
        y, x = r * cell + PAD, c * cell + PAD
        canvas[y:y + TILE, x:x + TILE] = face
        placed.append({"name": name, "cx": x + TILE // 2, "cy": y + TILE // 2})
    return canvas, placed


def to_data_url(bgr):
    ok, buf = cv2.imencode(".jpg", bgr)
    if not ok:
        raise RuntimeError("jpeg encode failed")
    return "data:image/jpeg;base64," + base64.b64encode(buf).decode()


def match_expected(box, placed):
    """Which expected face does this returned box cover? (box center → tile center)"""
    x1, y1, x2, y2 = box
    bx, by = (x1 + x2) / 2, (y1 + y2) / 2
    best, best_d = None, float("inf")
    for p in placed:
        d = (p["cx"] - bx) ** 2 + (p["cy"] - by) ** 2
        if d < best_d:
            best, best_d = p, d
    return best if best_d ** 0.5 < TILE else None


def main():
    ap = argparse.ArgumentParser(description="Multi-face /predict test")
    ap.add_argument("--faces", type=int, default=4, help="how many identities to put in the frame")
    ap.add_argument("--names", nargs="+", help="specific identities (default: random trained ones)")
    ap.add_argument("--save", help="write the composite frame here for eyeballing")
    args = ap.parse_args()

    known = trained_names()
    if args.names:
        unknown = [n for n in args.names if n not in known]
        if unknown:
            print(f"⚠ not in the trained model (will be 'Unknown'): {', '.join(unknown)}")
        names = args.names
    else:
        names = random.sample(known, min(args.faces, len(known)))

    print(f"Building a frame with {len(names)} face(s): {', '.join(names)}")
    canvas, placed = build_composite(names)
    if args.save:
        cv2.imwrite(args.save, canvas)
        print(f"Composite frame → {args.save}")

    r = requests.post(f"{API}/predict", json={"image": to_data_url(canvas)}, timeout=60)
    r.raise_for_status()
    results = r.json().get("results", [])

    print(f"\nExpected {len(placed)} face(s), detector returned {len(results)}")
    print(f"{'expected':<12} {'predicted':<12} {'cos':>6}  {'det':>5}  ok")
    print("-" * 46)

    correct = 0
    for res in results:
        exp = match_expected(res["box"], placed)
        exp_name = exp["name"] if exp else "?"
        ok = exp is not None and res["name"] == exp_name
        correct += ok
        print(f"{exp_name:<12} {res['name']:<12} {res['confidence']:>6.3f}"
              f"  {res.get('det_score', 0):>5.2f}  {'✅' if ok else '❌'}")

    detected = len(results)
    print("-" * 46)
    print(f"Detection : {detected}/{len(placed)} faces found")
    print(f"Identity  : {correct}/{len(placed)} correctly named")
    if detected == len(placed) and correct == len(placed):
        print("\n✅ PASS — every face detected and correctly identified")
        return 0
    print("\n❌ FAIL — see rows marked ❌ above")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
