# PresenceAI — Spoof-Resistant Multi-Face Attendance

Recognises every face in one camera frame and marks those students present — **and refuses
to be fooled by a photograph.**

> A state-of-the-art face model, used the normal way, marks a **printed photo present 100%
> of the time.** We measured that, and this repository is the decision layer that fixes it.

| | Before | After |
|---|---|---|
| Photo held to the camera → marked present | **100%** | **0%** |
| Strangers admitted (FAR) | 0.81% | **0.20%** |
| Wrong attendance records | 3.54% | **0%** |
| Time to enrol a student | 607 s | **1.4 s** |
| Time to mark a student present | 10.5 s | **2.8 s** |

Every number above is produced by a script in this repo, not typed by hand.
Run `python scripts/evaluate.py` and `python scripts/test_spoof.py` to reproduce them.

---

## Why recognition alone is not enough

Face recognition is **designed** to give a photo of you the same embedding as you — that is
exactly what makes it a good face model. So it can **never** tell a person from a photo of
that person. Not with more training, not with a bigger model. It is structurally impossible.

Which means **recognition alone cannot prevent proxy attendance**, and every attendance
paper claiming otherwise is wrong. To stop the photo attack you have to measure something
that isn't the face. We measure **motion**.

---

## How it works

```
  Webcam frame  (1 every 0.7 s)
        │
        ▼
  1. DETECT      RetinaFace/SCRFD — finds EVERY face, plus 106 landmarks per face (free)
        │
        ▼
  2. EMBED       ArcFace ResNet-50 — each face becomes 512 numbers ("embedding")
        │         The model is FROZEN. We never train it.
        ▼
  3. MATCH       cosine similarity vs each student's CENTROID (the average of their
        │         enrolment photos). No classifier — the space is already separated.
        ▼
  4. FOUR GATES  any one can refuse:
        │           size      face ≥ 40 px          → else "Move closer"
        │           threshold cos ≥ 0.147           → else "Unknown"
        │           margin    top1 − top2 ≥ 0.15    → else "Uncertain"
        │           LIVENESS  is the face moving?   → else "Not live (photo?)"
        ▼
  5. TEMPORAL VOTE   3 frames must agree
        │            (attendance is written once a day and cannot be undone)
        ▼
  6. logs/attendance_YYYY-MM-DD.csv
```

**Steps 1–3 are standard, off-the-shelf components. Steps 4–5 are the contribution.**

### The four gates exist because the model cannot say "I don't know"

A classifier always outputs a name. Feed it a 20-pixel blur, a stranger, or a photograph —
it still answers, confidently. A confident answer from bad input is worse than no answer,
because you believe it. The gates are the "I don't know" the model lacks.

### Liveness: why not blink detection?

Blink detection is the textbook approach ("a photo can't blink"). **We implemented it and
measured it failing.** A blink lasts ~0.3 s; the live page samples ~1.4 frames/sec, so the
blink happens *between* frames and is almost never caught.

Instead we measure **facial motion** from the landmarks the detector already produces.
Translation, rotation and scale are normalised away first — so **waving the photo around
does not help the attacker**; only genuine deformation survives.

| | motion score |
|---|---|
| Photo, hand-held | **0.015** |
| Real face, live | 0.066 – 0.135 |
| Threshold | **0.035** |

---

## Repository layout

```
Major/
├── Server/                        Python backend
│   ├── api.py                     Flask REST API — the four gates, voting, auth, auto-retrain
│   ├── arcface_engine.py          wraps InsightFace: image → boxes + 512-d + 106 landmarks
│   ├── liveness.py                anti-spoofing: rigid-normalised landmark-shape motion
│   ├── trainer.py                 enrolment: embed (cached) → centroids → calibrate gates
│   │
│   ├── scripts/
│   │   ├── evaluate.py            THE experiment: 30 students + 66 strangers, held-out
│   │   │                          splits → ablation table + degradation curve
│   │   ├── test_spoof.py          the presentation attack: 100% → 0%
│   │   ├── test_multiface.py      many faces in one frame, end to end through /predict
│   │   ├── benchmark.py           latency, memory, capacity
│   │   ├── make_ppt.py            builds the deck FROM the measurement files
│   │   ├── dataset.py             download VGGFace2 (impostor cohort)
│   │   └── preprocess.py          crop it
│   │
│   ├── models/                    centroids · label encoder · thresholds · embedding cache
│   ├── processed_dataset/<name>/  enrolment images (gitignored — biometric data)
│   ├── logs/attendance_*.csv      the attendance records (gitignored)
│   └── results/                   evaluation.json · benchmark.json · the deck
│
└── Frontend/                      React + Vite + Tailwind
    └── src/
        ├── pages/                 Home · Research · Login · Dashboard · Register ·
        │                          LiveAttendance · Attendance · StudentList · Records
        ├── components/ui.jsx      the shared design system
        └── utils/api.js           all backend calls (token attached automatically)
```

**There is no classifier and no `.pkl` model to train.** A student *is* a row in
`models/arcface_centroids.pkl`. That is why enrolment takes 1.4 s.

---

## Running it

```bash
# ── backend ──
cd Server
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt        # insightface + onnxruntime, CPU only
python api.py                          # http://127.0.0.1:5000

# ── frontend ──
cd Frontend
npm install
npm run dev                            # http://localhost:5173
```

Sign up, register a student (the model retrains itself in ~1.4 s and hot-swaps — **no
restart**), then open **Live** and watch the gates work.

**Try the attack yourself:** hold a printed photo of an enrolled student to the camera.
It will be recognised, and it will **never** be marked present.

---

## Reproducing every number in the report

```bash
cd Server
python scripts/evaluate.py       # ablation + operating envelope  → results/evaluation.json
python scripts/test_spoof.py     # presentation attack, 100% → 0%
python scripts/benchmark.py      # latency + capacity             → results/benchmark.json
python scripts/make_ppt.py       # rebuilds the deck from the two files above
```

### Experimental protocol

96 VGGFace2 identities → **30 simulated students** + **66 strangers**.
Student images split 70/30 into *enrolment* vs *held-out test*. Strangers split in half:
one half **calibrates** the threshold, the other half **measures** it.

Both splits are essential. Scoring a face against a centroid built from *that same face*
gives 100% and proves nothing. A threshold tuned on the same strangers you then report a
false-accept rate against is not a measurement.

---

## Honest limitations

- **A video replay still passes.** A recorded face genuinely moves. We raise the attack
  cost from *"print a photo"* to *"record and replay a video"* — a real gain, not a
  complete defence. Beating it needs a depth or texture based anti-spoof model.
- **The look-alike (top-2 margin) guard did not help.** Our cohort contains no look-alike
  pairs, so it had nothing to catch. We report it rather than quietly drop it.
- **Only 2 real users are enrolled.** Every quantitative claim comes from the 30-identity
  cohort; the live system is a feasibility demonstration.
- **VGGFace2 images are cleaner than a classroom webcam**, so real-world numbers will be
  worse than these.

---

## Privacy

Runs **fully offline**. No cloud, no GPU, no database server. Student faces never leave the
machine. Under India's DPDP Act 2023 biometric data is *sensitive personal data* —
uploading children's faces to a third-party cloud is a liability, not a feature.

`processed_dataset/`, `logs/`, `data/users.json` and `data/secret.key` are gitignored.

---

## What we do and do not claim

**We did not build a new face-recognition model.** ArcFace is pretrained and frozen.
Training our own on 30 students would need a GPU and thousands of images per person — and
would still name a stranger every single time, because a softmax cannot abstain.

**What is ours:** the finding that recognition alone fails, the liveness method that works
at the frame rate this hardware actually delivers, thresholds calibrated from an impostor
cohort, treating the attendance commit as a separate irreversible decision — and an honest
evaluation of all of it, including the guard that did not work.
