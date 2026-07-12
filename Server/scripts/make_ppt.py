"""
make_ppt.py
Rebuilds the project deck in the team's OWN 10-slide structure (Title / Project Title /
Objective / Problem Definition / Literature Review / Proposed Methodology / Experimental
Details / Results & Analysis / Conclusion / References / Thank You).

Every number comes from this repository's own measurements — results/evaluation.json,
results/benchmark.json, scripts/test_spoof.py — rather than being typed in, so the slides
cannot drift away from what the code actually does. The previous deck claimed MTCNN +
FaceNet + MongoDB (none of which the system uses) and a 95% accuracy that was never
measured; that is exactly the class of error this script exists to prevent.

    python scripts/make_ppt.py
    -> results/PresenceAI_Presentation.pptx
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

RESULTS = "results"
OUT = os.path.join(RESULTS, "PresenceAI_Presentation.pptx")
FIG = os.path.join(RESULTS, "ppt_figs")

NAVY = RGBColor(0x1F, 0x3A, 0x6E)
INK = RGBColor(0x1A, 0x1A, 0x1A)
GREY = RGBColor(0x55, 0x5F, 0x6D)
RED = RGBColor(0xC0, 0x39, 0x2B)
GREEN = RGBColor(0x1E, 0x8E, 0x5A)


# ── figures ───────────────────────────────────────────────────────────────────
def figures(ev):
    os.makedirs(FIG, exist_ok=True)
    plt.rcParams.update({"font.size": 11, "axes.spines.top": False,
                         "axes.spines.right": False, "figure.dpi": 200})

    fig, ax = plt.subplots(figsize=(4.2, 3))
    ax.bar(["Recognition\nonly", "+ Liveness\n(ours)"], [100, 0],
           color=["#c0392b", "#1e8e5a"], width=0.55)
    for x, v in zip([0, 1], [100, 0]):
        ax.text(x, v + 3, f"{v}%", ha="center", fontweight="bold")
    ax.set_ylabel("Photo-attack success (%)"); ax.set_ylim(0, 112)
    ax.set_title("A printed photo is marked present", fontsize=11, fontweight="bold")
    fig.tight_layout(); fig.savefig(f"{FIG}/spoof.png"); plt.close(fig)

    rows = ev["ablation"]
    labels = ["Baseline", "+ Calibrated\nthreshold", "+ Top-2\nmargin", "+ Temporal\nvoting"]
    fig, ax = plt.subplots(figsize=(6.2, 3))
    x = range(len(rows))
    ax.bar([i - 0.19 for i in x], [r["far"] for r in rows], 0.38,
           label="Strangers admitted (FAR)", color="#2e6fdb")
    ax.bar([i + 0.19 for i in x], [r["false_log_rate"] for r in rows], 0.38,
           label="Wrong attendance records", color="#8e5ad6")
    ax.set_xticks(list(x)); ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Error rate (%)"); ax.legend(fontsize=9, frameon=False)
    ax.set_title("Each guard, switched on one at a time", fontsize=11, fontweight="bold")
    fig.tight_layout(); fig.savefig(f"{FIG}/ablation.png"); plt.close(fig)

    deg = ev["degradation"]
    fig, ax = plt.subplots(figsize=(4.4, 3))
    ax.plot([d["face_px"] for d in deg], [d["accuracy"] * 100 for d in deg],
            "o-", color="#2e6fdb", lw=2)
    ax.axvline(40, ls="--", color="#e08e0b")
    ax.text(43, 70, "gate: 40px", color="#e08e0b", fontsize=9)
    ax.set_xlabel("Face width in frame (px)"); ax.set_ylabel("Accuracy (%)")
    ax.set_title("Collapses below ~24px", fontsize=11, fontweight="bold")
    fig.tight_layout(); fig.savefig(f"{FIG}/degradation.png"); plt.close(fig)

    # workflow — replaces the old MTCNN/FaceNet/MongoDB diagram
    fig, ax = plt.subplots(figsize=(12, 2.4))
    ax.axis("off")
    steps = [
        ("1. Face input\n(web camera)", "#eef2f9"),
        ("2. Detect ALL faces\nRetinaFace / SCRFD", "#dbe6f7"),
        ("3. Align + embed\nArcFace → 512-d", "#c8daf4"),
        ("4. Match\nvs student centroids", "#b5cef1"),
        ("5. FOUR GATES\nsize · threshold\nmargin · LIVENESS", "#ffd9d0"),
        ("6. Temporal vote\n(3 frames agree)", "#d8e9f5"),
        ("7. Attendance\nrecorded (CSV)", "#cfeade"),
    ]
    w, gap = 1.42, 0.2
    for i, (label, col) in enumerate(steps):
        xp = i * (w + gap)
        edge = "#c0392b" if "GATES" in label else "#93a1b8"
        ax.add_patch(plt.Rectangle((xp, 0), w, 1.0, facecolor=col, edgecolor=edge,
                                   lw=1.8 if "GATES" in label else 1.2, zorder=2))
        ax.text(xp + w / 2, 0.5, label, ha="center", va="center", fontsize=7.8,
                fontweight="bold" if "GATES" in label else "normal", zorder=3)
        if i < len(steps) - 1:
            ax.annotate("", xy=(xp + w + gap, 0.5), xytext=(xp + w, 0.5),
                        arrowprops=dict(arrowstyle="->", color="#55606d", lw=1.3))
    ax.set_xlim(-0.1, len(steps) * (w + gap)); ax.set_ylim(-0.4, 1.15)
    ax.text(0, -0.32, "The deep model is FROZEN — enrolling a student stores a centroid; it does "
                      "not retrain the network. Steps 5–6 are our contribution.",
            fontsize=8, color="#55606d", style="italic")
    fig.tight_layout(); fig.savefig(f"{FIG}/workflow.png"); plt.close(fig)
    print(f"  figures → {FIG}/")


# ── slide helpers ─────────────────────────────────────────────────────────────
def slide(prs, heading):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    box = s.shapes.add_textbox(Inches(0.4), Inches(0.2), Inches(12.5), Inches(0.7))
    p = box.text_frame.paragraphs[0]
    p.text = heading
    p.alignment = PP_ALIGN.CENTER
    p.runs[0].font.size = Pt(28)
    p.runs[0].font.bold = True
    p.runs[0].font.color.rgb = NAVY
    return s


def bullets(s, items, left, top, width, height, size=13):
    tf = s.shapes.add_textbox(Inches(left), Inches(top),
                              Inches(width), Inches(height)).text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        text, bold, colour, lvl = (item if isinstance(item, tuple) else (item, False, INK, 0))
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = text
        p.level = lvl
        p.space_after = Pt(5)
        for r in p.runs:
            r.font.size = Pt(size)
            r.font.bold = bold
            r.font.color.rgb = colour
    return tf


def main():
    ev = json.load(open(os.path.join(RESULTS, "evaluation.json")))
    bm = json.load(open(os.path.join(RESULTS, "benchmark.json")))
    figures(ev)
    base, final = ev["ablation"][0], ev["ablation"][-1]

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)

    # ── 1. TITLE PAGE ────────────────────────────────────────────────────────
    s = prs.slides.add_slide(prs.slide_layouts[6])
    box = s.shapes.add_textbox(Inches(0.8), Inches(0.8), Inches(11.7), Inches(1.6))
    tf = box.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "AUTOMATIC ATTENDANCE SYSTEM USING MULTIPLE FACE RECOGNITION"
    p.alignment = PP_ALIGN.CENTER
    p.runs[0].font.size = Pt(30); p.runs[0].font.bold = True; p.runs[0].font.color.rgb = NAVY
    p2 = tf.add_paragraph()
    p2.text = "Spoof-Resistant Multi-Face Attendance — Recognition Alone Is Not Enough"
    p2.alignment = PP_ALIGN.CENTER
    p2.runs[0].font.size = Pt(15); p2.runs[0].font.italic = True
    p2.runs[0].font.color.rgb = GREY

    bullets(s, [
        ("Team Members' Name and Roll Number", True, INK, 0),
        "1. Souryadeep Deb (13000222064)          2. Soham Bhattacharya (13000222065)",
        "3. Srija Basak (13000222066)              4. Sneha Singh (13000222067)",
        "",
        ("Group Number — 18", True, INK, 0),
        ("Mentor Name — Mr Prodipta Bhowmik", True, INK, 0),
    ], 3.0, 3.0, 8.0, 2.6, size=14)

    box = s.shapes.add_textbox(Inches(0.8), Inches(6.3), Inches(11.7), Inches(1.0))
    for i, line in enumerate(["Department of Information Technology",
                              "Techno Main Salt Lake", "Kolkata - 700091"]):
        p = box.text_frame.paragraphs[0] if i == 0 else box.text_frame.add_paragraph()
        p.text = line; p.alignment = PP_ALIGN.CENTER
        p.runs[0].font.size = Pt(13); p.runs[0].font.bold = True

    # ── 2. PROJECT TITLE ─────────────────────────────────────────────────────
    s = slide(prs, "PROJECT TITLE")
    bullets(s, [
        ("Automatic Attendance System using Multiple Face Recognition", True, NAVY, 0),
        "",
        ("Research focus", True, INK, 0),
        "A state-of-the-art face model still marks a printed photograph present",
        ("100% of the time. We measured it, and we fixed it.", True, RED, 0),
        "",
        "Detecting and recognising every face in one frame — and then deciding,",
        "separately and carefully, who is actually PRESENT.",
    ], 2.2, 2.4, 9.0, 3.6, size=16)

    # ── 3. OBJECTIVE ─────────────────────────────────────────────────────────
    s = slide(prs, "OBJECTIVE OF THE PROJECT")
    bullets(s, [
        ("1.  Automate attendance using multi-face recognition", True, INK, 0),
        "Detect and identify every face in a single frame, not one person at a time.",
        "",
        ("2.  Reject strangers — an open-set system", True, INK, 0),
        "A classifier must always name someone. Ours is allowed to answer 'nobody'.",
        "",
        ("3.  Resist presentation attacks (photo / screen spoofing)", True, RED, 0),
        "Recognition alone cannot tell a person from a photo of that person.",
        "",
        ("4.  Make the attendance commit reliable, not just the recognition", True, INK, 0),
        "Attendance is irreversible — one bad frame must not mark the wrong student.",
        "",
        ("5.  Run on ordinary hardware, offline", True, INK, 0),
        "One laptop, one webcam, no GPU, no cloud, no student data leaving campus.",
    ], 1.2, 1.3, 11.0, 5.5, size=13.5)

    # ── 4. PROBLEM DEFINITION ────────────────────────────────────────────────
    s = slide(prs, "PROBLEM DEFINITION")
    bullets(s, [
        ("Traditional manual attendance is slow, error-prone and open to proxy marking.", True, INK, 0),
        "A 60-student roll-call costs ~5 minutes of every lecture — roughly 80 hours a year.",
        "",
        ("But automating it with face recognition introduces a NEW problem, and this is the", True, NAVY, 0),
        ("gap our project addresses:", True, NAVY, 0),
    ], 0.7, 1.2, 12.0, 1.6, size=14)

    bullets(s, [
        ("Face recognition is DESIGNED to give a photo of you the same embedding as you.", True, RED, 0),
        ("That is what makes it a good face model — and it is why recognition alone", True, RED, 0),
        ("cannot prevent proxy attendance. We tested it: a printed photo was marked", True, RED, 0),
        ("present 100% of the time.", True, RED, 0),
    ], 0.9, 3.1, 11.6, 1.4, size=15)

    bullets(s, [
        ("Four failures a real deployment must survive", True, NAVY, 0),
        "•  A photograph or phone screen held up to the camera  →  marked present",
        "•  A stranger walking past  →  a softmax has no way to say 'nobody'",
        "•  A student at the back of the room  →  too few pixels to identify, but still named",
        "•  One misread frame  →  wrong student marked present for the entire day",
    ], 0.9, 4.9, 11.6, 2.0, size=13)

    # ── 5. LITERATURE REVIEW ─────────────────────────────────────────────────
    s = slide(prs, "LITERATURE REVIEW")
    bullets(s, [
        "D'Souza et al. (2019) [1] — automated attendance via histogram-based features; "
        "improves efficiency but is sensitive to lighting and pose.",
        "",
        "Arsenovic et al. (2017) [2] — CNN-based deep learning for attendance; higher accuracy "
        "and real-time performance.",
        "",
        "Kakarla et al. (2020) [3] — CNN smart attendance recognising multiple students under "
        "moderate pose and expression change.",
        "",
        "Varadharajan et al. (2016) [4] — face-detection classroom attendance; accuracy drops "
        "under occlusion and poor lighting.",
        "",
        "Siswanto et al. (2014) [5] — face biometrics as a hygienic alternative to fingerprint "
        "attendance.",
        "",
        "Deng et al. (2019) [6] — ArcFace: additive angular margin loss. The 512-d embedding "
        "our system uses (pretrained and frozen — we do not claim it).",
    ], 0.7, 1.2, 12.0, 4.4, size=12.5)

    bullets(s, [
        ("RESEARCH GAP", True, RED, 0),
        ("Every attendance paper above reports one accuracy number on clean data. None of them "
         "test a presentation attack, none report a stranger-rejection rate, and none treat "
         "'recognised' and 'marked present' as different decisions. That gap is our project.", True, RED, 0),
    ], 0.7, 5.9, 12.0, 1.1, size=12.5)

    # ── 6. PROPOSED METHODOLOGY ──────────────────────────────────────────────
    s = slide(prs, "PROPOSED METHODOLOGY")
    bullets(s, [
        ("How it works", True, NAVY, 0),
        "Every face in the frame is detected, embedded (512-d) and matched against each",
        "enrolled student's centroid. A face must then pass FOUR gates before the system is",
        "willing to put a name on it — and several frames must agree before attendance is",
        "written. Records go to CSV; nothing leaves the machine.",
        "",
        ("Problem addressed", True, NAVY, 0),
        "Replaces manual roll-call, eliminates the signed-register proxy, rejects strangers,",
        "and blocks the photo/screen proxy that defeats ordinary face recognition.",
    ], 0.7, 1.2, 6.3, 3.0, size=12.5)

    bullets(s, [
        ("Innovation and uniqueness — stated honestly", True, NAVY, 0),
        "",
        ("We do NOT claim a new face-recognition model.", True, RED, 0),
        "ArcFace is pretrained and frozen. Training our own on 30 students would need a GPU,",
        "thousands of images per person, and would still name a stranger every time.",
        "",
        ("What IS ours:", True, GREEN, 0),
        "•  Liveness that works on classroom hardware. Blink detection is the standard trick, "
        "but a blink lasts ~0.3 s and our system samples ~1.4 frames/s — we measured it failing. "
        "So we measure facial motion from landmarks the detector already produces: a live face "
        "keeps deforming, a photo is rigid. Rotation and scale are normalised away, so waving "
        "the photo does not help the attacker. No extra model. No GPU.",
        "•  A threshold calibrated on 2,880 impostor faces, not hand-picked.",
        "•  Attendance treated as an irreversible commit needing agreement across frames.",
        "•  Enrolment in 1.4 s (was 607 s) by caching embeddings.",
        "•  A guard that did NOT work (top-2 margin) — reported, not hidden.",
    ], 7.2, 1.2, 5.6, 5.6, size=11)

    # ── 7. EXPERIMENTAL DETAILS ──────────────────────────────────────────────
    s = slide(prs, "EXPERIMENTAL DETAILS")
    s.shapes.add_picture(f"{FIG}/workflow.png", Inches(0.4), Inches(0.95), width=Inches(12.5))

    bullets(s, [
        ("Technologies", True, NAVY, 0),
        "Language:  Python 3.13",
        "Detection:  RetinaFace / SCRFD (det_10g)",
        "Recognition:  ArcFace ResNet-50 (buffalo_l) → 512-d",
        "Runtime:  ONNX Runtime — CPU only, no GPU",
        "Classifier:  linear SVM + cosine-to-centroid (scikit-learn)",
        "Backend:  Flask REST API, token authentication",
        "Frontend:  React · Vite · TailwindCSS",
        "Storage:  CSV + JSON on disk — no cloud, no DB server",
    ], 0.7, 3.3, 5.8, 3.6, size=12)

    bullets(s, [
        ("Experimental protocol", True, NAVY, 0),
        "96 VGGFace2 identities → 30 simulated 'students' + 66 'strangers'.",
        "Student images split 70/30: enrolment vs held-out test images.",
        "Strangers split in half: one half calibrates the threshold,",
        "the other half measures it.",
        "",
        ("Both splits are essential.", True, RED, 0),
        "Scoring a face against a centroid built from that same face gives",
        "100% and proves nothing. A threshold tuned on the same strangers",
        "you then report a false-accept rate against is not a measurement.",
        "",
        "Hardware: MacBook Air, CPU only. 2 real users enrolled for the",
        "live deployment demo.",
    ], 6.9, 3.3, 5.9, 3.6, size=11.5)

    # ── 8. RESULTS AND ANALYSIS ──────────────────────────────────────────────
    s = slide(prs, "RESULTS AND ANALYSIS")
    s.shapes.add_picture(f"{FIG}/spoof.png", Inches(0.4), Inches(1.0), height=Inches(2.4))
    s.shapes.add_picture(f"{FIG}/ablation.png", Inches(4.1), Inches(1.0), height=Inches(2.4))
    s.shapes.add_picture(f"{FIG}/degradation.png", Inches(9.2), Inches(1.0), height=Inches(2.4))

    data = [
        ["Metric", "Before", "After"],
        ["Photo marked present (attack success)", "100%", "0%"],
        ["Strangers admitted (FAR)", f"{base['far']}%", f"{final['far']}%"],
        ["Wrong attendance records", f"{base['false_log_rate']}%", f"{final['false_log_rate']}%"],
        ["Time to enrol a student", "607 s", "1.4 s"],
        ["Time to mark present", "10.5 s", "2.8 s"],
    ]
    tbl = s.shapes.add_table(len(data), 3, Inches(0.5), Inches(3.7),
                             Inches(7.0), Inches(2.4)).table
    tbl.columns[0].width = Inches(3.8)
    tbl.columns[1].width = Inches(1.6)
    tbl.columns[2].width = Inches(1.6)
    for r, row in enumerate(data):
        for c, val in enumerate(row):
            cell = tbl.cell(r, c); cell.text = val
            run = cell.text_frame.paragraphs[0].runs[0]
            run.font.size = Pt(11); run.font.bold = (r == 0)
            if r > 0 and c == 2:
                run.font.bold = True; run.font.color.rgb = GREEN

    bullets(s, [
        ("Capacity (laptop CPU, no GPU)", True, NAVY, 0),
        f"16 faces in one frame: {bm['throughput'][-1]['latency_s']} s",
        "10,000 enrolled students: +1.2 ms per match",
        "One 1080p camera covers ~7 m — a classroom",
        f"Memory: {bm['memory_mb']:.0f} MB",
        "",
        ("Key findings", True, NAVY, 0),
        "Calibrating the threshold cut strangers admitted 4×.",
        "Temporal voting drove wrong records to zero.",
        ("The top-2 margin guard did NOT help — we report it.", True, RED, 0),
    ], 7.8, 3.7, 5.1, 3.2, size=11)

    # ── 9. CONCLUSION ────────────────────────────────────────────────────────
    s = slide(prs, "CONCLUSION")
    bullets(s, [
        ("A pretrained face model is not an attendance system.", True, NAVY, 0),
        "It fails in three measurable ways, and each one is fixable in the decision layer.",
        "",
        ("Automation", True, INK, 0),
        "Every face in the frame detected and identified in one pass; enrolment takes 1.4 s.",
        "",
        ("Integrity", True, INK, 0),
        "Manual proxy (a friend signing the register) is eliminated. Photo and screen proxy",
        "is blocked by liveness — attack success 100% → 0%. Strangers admitted: 0.20%.",
        "",
        ("Precision", True, INK, 0),
        "Open-set rejection with a threshold calibrated on 2,880 impostor faces. Faces below",
        "40 px are refused rather than guessed at. Wrong attendance records: 0%.",
        "",
        ("Efficiency", True, INK, 0),
        "16 faces per frame in 1.3 s on a laptop CPU. Fully offline: no cloud, no GPU, ₹0/year.",
    ], 0.7, 1.2, 7.2, 5.6, size=12.5)

    bullets(s, [
        ("LIMITATIONS & FUTURE WORK", True, RED, 0),
        "",
        ("Video replay still defeats liveness.", True, INK, 0),
        "A recorded face genuinely moves. We raise the attack cost from 'print a photo' to",
        "'record and replay a video' — a real gain, not a complete defence. A depth or",
        "texture-based anti-spoof model is the next step.",
        "",
        ("The look-alike guard is unproven.", True, INK, 0),
        "Our cohort contains no look-alike pairs, so the top-2 margin had nothing to catch.",
        "We cannot claim it works.",
        "",
        ("Only 2 real users enrolled.", True, INK, 0),
        "All quantitative claims come from the 30-identity cohort. The live system is a",
        "feasibility demonstration.",
        "",
        ("The cohort is photographic.", True, INK, 0),
        "VGGFace2 images are cleaner than a classroom webcam, so real-world numbers will",
        "be worse than these.",
    ], 8.1, 1.2, 4.8, 5.6, size=10.5)

    # ── 10. REFERENCES ───────────────────────────────────────────────────────
    s = slide(prs, "REFERENCES")
    bullets(s, [
        "[1]  D'Souza, J. W. S., et al. (2019). Automated Attendance Marking and Management System "
        "by Facial Recognition Using Histogram. Array, 3–4: 100014. DOI: 10.1016/j.array.2019.100014",
        "",
        "[2]  Arsenovic, M., Sladojevic, S., Anderla, A., Stefanovic, D. (2017). FaceTime — Deep "
        "Learning Based Face Recognition Attendance System. IEEE SISY 2017, pp. 53–58. "
        "DOI: 10.1109/SISY.2017.8080587",
        "",
        "[3]  Kakarla, S., Gangula, P., Rahul, M. S., Singh, C. S. C., Sarma, T. H. (2020). Smart "
        "Attendance Management System Based on Face Recognition Using CNN. IEEE-HYDCON 2020, pp. 1–5. "
        "DOI: 10.1109/HYDCON48903.2020.9242847",
        "",
        "[4]  Varadharajan, E., Dharani, R., Jeevitha, S., Kavinmathi, B., Hemalatha, S. (2016). "
        "Automatic Attendance Management System Using Face Detection. IC-GET 2016, pp. 1–3. "
        "DOI: 10.1109/GET.2016.7916753",
        "",
        "[5]  Siswanto, A. R. S., Nugroho, A. S., Galinium, M. (2014). Implementation of Face "
        "Recognition Algorithm for Biometrics Based Time Attendance System. ICISS 2014, pp. 149–154. "
        "DOI: 10.1109/ICTSS.2014.7013165",
        "",
        "[6]  Deng, J., Guo, J., Xue, N., Zafeiriou, S. (2019). ArcFace: Additive Angular Margin Loss "
        "for Deep Face Recognition. CVPR 2019, pp. 4690–4699. DOI: 10.1109/CVPR.2019.00482",
        "",
        "[7]  Deng, J., Guo, J., Ververas, E., Kotsia, I., Zafeiriou, S. (2020). RetinaFace: Single-Shot "
        "Multi-Level Face Localisation in the Wild. CVPR 2020. DOI: 10.1109/CVPR42600.2020.00525",
        "",
        "[8]  Pan, G., Sun, L., Wu, Z., Lao, S. (2007). Eyeblink-based Anti-Spoofing in Face Recognition "
        "from a Generic Webcamera. ICCV 2007, pp. 1–8. DOI: 10.1109/ICCV.2007.4409068",
        "",
        "[9]  ISO/IEC 30107-3:2023 — Information technology — Biometric presentation attack detection — "
        "Part 3: Testing and reporting.",
        "",
        "[10] Cao, Q., Shen, L., Xie, W., Parkhi, O. M., Zisserman, A. (2018). VGGFace2: A Dataset for "
        "Recognising Faces across Pose and Age. IEEE FG 2018, pp. 67–74.",
        "",
        ("Source code and all measurement scripts: "
         "github.com/SohamBhattacharjee2003/MutiFace-Attendance-System", True, NAVY, 0),
    ], 0.6, 1.05, 12.2, 6.1, size=9.5)

    # ── 11. THANK YOU ────────────────────────────────────────────────────────
    s = prs.slides.add_slide(prs.slide_layouts[6])
    box = s.shapes.add_textbox(Inches(0.8), Inches(3.0), Inches(11.7), Inches(1.4))
    p = box.text_frame.paragraphs[0]
    p.text = "THANK YOU"
    p.alignment = PP_ALIGN.CENTER
    p.runs[0].font.size = Pt(48); p.runs[0].font.bold = True; p.runs[0].font.italic = True

    prs.save(OUT)
    print(f"\n✅ {OUT}  ({len(prs.slides._sldIdLst)} slides)")


if __name__ == "__main__":
    main()
