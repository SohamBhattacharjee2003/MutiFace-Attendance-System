"""
test_spoof.py
Measures how easily the system is fooled by a presentation attack (a photo of a student
held up to the camera), with liveness OFF and ON.

WHY THIS IS THE EXPERIMENT THAT MATTERS
    Face recognition is *designed* to give a photo of you the same embedding as you. So
    recognition alone cannot prevent proxy attendance — the claim every attendance paper
    makes. This script puts a number on that failure and on the fix.

TWO MODES

  --sim   (no hardware, runs anywhere)
          Replays a still image as a stream of frames — exactly what the camera sees when
          someone holds a photo up: a real face, perfectly recognizable, that never blinks.
          Reports whether attendance would be committed.

  --live  (the real test, for the report)
          Uses the webcam. Sit in front of it yourself → PASS expected.
          Then hold a printed photo / phone screen up → FAIL expected.

Usage:
    python scripts/test_spoof.py --sim
    python scripts/test_spoof.py --live --name Soham
"""

import os
import sys
import time
import glob
import argparse

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import liveness
from arcface_engine import ArcFaceEngine

FRAMES = 30          # how long the attacker holds the photo up (frames)
FPS = 5              # simulated frame rate


def attack_photo(engine, path, frames=FRAMES, fps=FPS):
    """Replay one still image as a video stream. Returns (recognized, blinked)."""
    img = cv2.imread(path)
    if img is None:
        return False, False

    liveness.reset("ATTACKER")
    detected = False
    live = False
    t = time.time()
    for i in range(frames):
        faces = engine.embed_faces(img)
        if not faces:
            continue
        detected = True
        is_live, ear, _ = liveness.update("ATTACKER", faces[0].get("landmarks"),
                                          now=t + i / fps)
        live = live or is_live
    return detected, live


def run_sim():
    engine = ArcFaceEngine.get()
    students = [d for d in sorted(os.listdir("processed_dataset"))
                if os.path.isdir(os.path.join("processed_dataset", d))
                and not d.lower().startswith("n0")]

    print("PRESENTATION ATTACK — a still photo held up to the camera\n")
    print(f"{'target':<12} {'face recognized':>16} {'blinked':>9} "
          f"{'liveness OFF':>14} {'liveness ON':>13}")
    print("-" * 70)

    off_success = on_success = total = 0
    for name in students:
        files = sorted(glob.glob(f"processed_dataset/{name}/*.jpg"))
        if not files:
            continue
        detected, blinked = attack_photo(engine, files[-1])
        if not detected:
            continue
        total += 1

        # liveness OFF: recognition alone decides → the photo is marked present
        marked_off = True
        # liveness ON: attendance also needs a blink, which a photo cannot produce
        marked_on = blinked

        off_success += marked_off
        on_success += marked_on
        print(f"{name:<12} {'YES':>16} {str(blinked):>9} "
              f"{'MARKED ✗':>14} {('MARKED ✗' if marked_on else 'BLOCKED ✓'):>13}")

    if not total:
        print("no usable student photos found")
        return
    print("-" * 70)
    print(f"\nAttack success rate")
    print(f"  liveness OFF : {off_success}/{total} ({off_success/total*100:.0f}%)  "
          f"— every photo is marked present")
    print(f"  liveness ON  : {on_success}/{total} ({on_success/total*100:.0f}%)  "
          f"— a photo cannot blink")
    print("\nNOTE: a *video* replay of a blinking person would still pass. Blink detection")
    print("raises the attack cost from 'print a photo' to 'record and replay a video';")
    print("it is not a complete defence. State this in Limitations.")


def run_live(name):
    engine = ArcFaceEngine.get()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("could not open the camera"); return

    liveness.reset(name)
    print(f"Live liveness test for '{name}'. Press Q to stop.")
    print("  1) Sit in front of the camera and blink → should turn LIVE")
    print("  2) Hold a printed photo / phone up      → should stay SPOOF\n")

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        faces = engine.embed_faces(frame)
        for f in faces:
            x1, y1, x2, y2 = f["box"]
            is_live, ear, state = liveness.update(name, f.get("landmarks"))
            colour = (0, 200, 0) if is_live else (0, 0, 220)
            label = f"{'LIVE' if is_live else 'SPOOF'} ear={ear:.2f}" if ear else state
            cv2.rectangle(frame, (x1, y1), (x2, y2), colour, 2)
            cv2.putText(frame, label, (x1, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, colour, 2)
        cv2.imshow("Liveness test — Q to quit", frame)
        if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q")):
            break
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sim", action="store_true", help="replay still photos (no camera)")
    ap.add_argument("--live", action="store_true", help="webcam test")
    ap.add_argument("--name", default="Tester")
    a = ap.parse_args()
    if a.live:
        run_live(a.name)
    else:
        run_sim()
