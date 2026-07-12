"""
benchmark.py
Cost, throughput and capacity of the deployed system — measured, not estimated.

Answers the three deployment questions:
    1. How long does one frame take, and how does that scale with faces in it?
    2. How much CPU / memory does it use?
    3. How many students can it handle — per frame, and enrolled in total?

Usage:
    python scripts/benchmark.py
"""

import os
import sys
import time
import json

import cv2
import numpy as np
import psutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import trainer
from arcface_engine import ArcFaceEngine

RESULTS_DIR = "results"
FACE_COUNTS = [1, 2, 4, 8, 16]
REPEATS = 3
TILE, PAD = 220, 40


def build_frame(n_faces, paths):
    """Tile n faces onto one canvas — a stand-in for a classroom group shot."""
    cols = int(np.ceil(np.sqrt(n_faces)))
    rows = int(np.ceil(n_faces / cols))
    cell = TILE + 2 * PAD
    canvas = np.full((rows * cell, cols * cell, 3), 210, np.uint8)
    for i in range(n_faces):
        img = cv2.imread(paths[i % len(paths)])
        if img is None:
            continue
        face = cv2.resize(img, (TILE, TILE))
        r, c = divmod(i, cols)
        y, x = r * cell + PAD, c * cell + PAD
        canvas[y:y + TILE, x:x + TILE] = face
    return canvas


def main():
    proc = psutil.Process()
    engine = ArcFaceEngine.get()

    # a pool of distinct faces to tile
    paths = []
    for d in sorted(os.listdir(trainer.DATASET_DIR))[:40]:
        p = os.path.join(trainer.DATASET_DIR, d)
        if os.path.isdir(p):
            fs = [f for f in os.listdir(p) if f.lower().endswith(".jpg")]
            if fs:
                paths.append(os.path.join(p, fs[0]))

    mem_before = proc.memory_info().rss / 1e6
    print(f"Model resident memory: {mem_before:.0f} MB (ArcFace + detector + landmarks)")
    print(f"CPU cores available  : {psutil.cpu_count()}\n")

    print("THROUGHPUT — one /predict call on a frame containing N faces")
    print(f"{'faces':>6} {'detected':>9} {'latency':>10} {'per face':>10} {'max fps':>8}")
    print("-" * 50)

    rows = []
    for n in FACE_COUNTS:
        frame = build_frame(n, paths)
        # warm-up so we time steady state, not first-call graph setup
        engine.embed_faces(frame)

        proc.cpu_percent(interval=None)
        t0 = time.perf_counter()
        for _ in range(REPEATS):
            faces = engine.embed_faces(frame)
        dt = (time.perf_counter() - t0) / REPEATS
        cpu = proc.cpu_percent(interval=None)

        per_face = dt / max(len(faces), 1)
        rows.append({"faces_in_frame": n, "detected": len(faces),
                     "latency_s": round(dt, 3), "per_face_s": round(per_face, 3),
                     "max_fps": round(1 / dt, 2), "cpu_percent": round(cpu, 1)})
        print(f"{n:>6} {len(faces):>9} {dt*1000:>8.0f}ms {per_face*1000:>8.0f}ms {1/dt:>8.2f}")

    mem_after = proc.memory_info().rss / 1e6
    peak_cpu = max(r["cpu_percent"] for r in rows)

    # ── matching cost: how many ENROLLED students can we compare against? ──────
    print("\nMATCHING COST — comparing one face against N enrolled students")
    print(f"{'students':>9} {'match time':>12}")
    print("-" * 24)
    emb = np.random.randn(512).astype(np.float32)
    emb /= np.linalg.norm(emb)
    match_rows = []
    for n_students in [10, 100, 1000, 10000]:
        M = np.random.randn(n_students, 512).astype(np.float32)
        M /= np.linalg.norm(M, axis=1, keepdims=True)
        t0 = time.perf_counter()
        for _ in range(100):
            sims = M @ emb
            np.argsort(sims)[::-1][:2]
        dt = (time.perf_counter() - t0) / 100
        match_rows.append({"students": n_students, "match_ms": round(dt * 1000, 4)})
        print(f"{n_students:>9} {dt*1000:>10.3f}ms")

    out = {
        "memory_mb": round(mem_after, 1),
        "cpu_cores": psutil.cpu_count(),
        "peak_cpu_percent_of_one_core": peak_cpu,
        "throughput": rows,
        "matching": match_rows,
    }
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, "benchmark.json"), "w") as f:
        json.dump(out, f, indent=2)

    print(f"\nMemory: {mem_after:.0f} MB   Peak CPU: {peak_cpu:.0f}% of one core")
    print(f"Saved → {RESULTS_DIR}/benchmark.json")


if __name__ == "__main__":
    main()
