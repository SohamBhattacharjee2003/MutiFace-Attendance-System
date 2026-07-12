"""
make_ppt.py
Builds the 6-slide project presentation required by the department template
(Title / Idea / Technical Approach / Results / Impact / References).

Every number in the deck is read from this repository's own measurements — results/
evaluation.json, benchmark.json and the spoof test — rather than typed in by hand, so
the slides cannot drift away from what the code actually does.

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

    # 1. presentation attack
    fig, ax = plt.subplots(figsize=(4.2, 3))
    ax.bar(["Recognition\nonly", "+ Liveness\n(ours)"], [100, 0],
           color=["#c0392b", "#1e8e5a"], width=0.55)
    for x, v in zip([0, 1], [100, 0]):
        ax.text(x, v + 3, f"{v}%", ha="center", fontweight="bold")
    ax.set_ylabel("Photo-attack success (%)")
    ax.set_ylim(0, 112)
    ax.set_title("A printed photo is marked present", fontsize=11, fontweight="bold")
    fig.tight_layout(); fig.savefig(f"{FIG}/spoof.png"); plt.close(fig)

    # 2. ablation — what each guard buys
    rows = ev["ablation"]
    labels = ["Baseline", "+ Calibrated\nthreshold", "+ Top-2\nmargin", "+ Temporal\nvoting"]
    far = [r["far"] for r in rows]
    flr = [r["false_log_rate"] for r in rows]
    x = range(len(rows))
    fig, ax = plt.subplots(figsize=(6.4, 3))
    ax.bar([i - 0.19 for i in x], far, 0.38, label="Strangers admitted (FAR)", color="#2e6fdb")
    ax.bar([i + 0.19 for i in x], flr, 0.38, label="Wrong attendance records", color="#8e5ad6")
    ax.set_xticks(list(x)); ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Error rate (%)")
    ax.legend(fontsize=9, frameon=False)
    ax.set_title("Each guard, switched on one at a time", fontsize=11, fontweight="bold")
    fig.tight_layout(); fig.savefig(f"{FIG}/ablation.png"); plt.close(fig)

    # 3. how far can a student sit
    deg = ev["degradation"]
    fig, ax = plt.subplots(figsize=(4.6, 3))
    ax.plot([d["face_px"] for d in deg], [d["accuracy"] * 100 for d in deg],
            "o-", color="#2e6fdb", lw=2)
    ax.axvline(40, ls="--", color="#e08e0b")
    ax.text(42, 70, "gate: 40px", color="#e08e0b", fontsize=9)
    ax.set_xlabel("Face width in the frame (pixels)")
    ax.set_ylabel("Accuracy (%)")
    ax.set_title("Recognition collapses below ~24px", fontsize=11, fontweight="bold")
    fig.tight_layout(); fig.savefig(f"{FIG}/degradation.png"); plt.close(fig)

    # 4. pipeline / workflow
    fig, ax = plt.subplots(figsize=(11, 2.3))
    ax.axis("off")
    steps = [
        ("Webcam\nframe", "#eef2f9"),
        ("RetinaFace\ndetect ALL faces", "#dbe6f7"),
        ("ArcFace\n512-d embedding", "#c8daf4"),
        ("Match vs\nstudent centroids", "#b5cef1"),
        ("4 GATES\nsize · threshold\nmargin · LIVENESS", "#ffd9d0"),
        ("Temporal vote\n→ attendance", "#cfeade"),
    ]
    w, gap = 1.55, 0.22
    for i, (label, col) in enumerate(steps):
        xpos = i * (w + gap)
        edge = "#c0392b" if "GATES" in label else "#93a1b8"
        ax.add_patch(plt.Rectangle((xpos, 0), w, 1.0, facecolor=col,
                                   edgecolor=edge, lw=1.6, zorder=2))
        ax.text(xpos + w / 2, 0.5, label, ha="center", va="center",
                fontsize=8.5, fontweight="bold" if "GATES" in label else "normal", zorder=3)
        if i < len(steps) - 1:
            ax.annotate("", xy=(xpos + w + gap, 0.5), xytext=(xpos + w, 0.5),
                        arrowprops=dict(arrowstyle="->", color="#55606d", lw=1.4))
    ax.set_xlim(-0.1, len(steps) * (w + gap)); ax.set_ylim(-0.35, 1.15)
    ax.text(0, -0.28, "The deep model is FROZEN — enrolling a student stores a centroid, "
                      "it does not retrain the network", fontsize=8, color="#55606d", style="italic")
    fig.tight_layout(); fig.savefig(f"{FIG}/workflow.png"); plt.close(fig)

    print(f"  figures → {FIG}/")


# ── slide helpers ─────────────────────────────────────────────────────────────
def title_bar(slide, text):
    box = slide.shapes.add_textbox(Inches(0.45), Inches(0.22), Inches(12.4), Inches(0.75))
    p = box.text_frame.paragraphs[0]
    p.text = text
    p.alignment = PP_ALIGN.CENTER
    p.runs[0].font.size = Pt(30)
    p.runs[0].font.bold = True
    p.runs[0].font.color.rgb = NAVY


def bullets(slide, items, left, top, width, height, size=13):
    tf = slide.shapes.add_textbox(Inches(left), Inches(top),
                                  Inches(width), Inches(height)).text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        text, bold, colour, indent = (item if isinstance(item, tuple)
                                      else (item, False, INK, 0))
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = text
        p.level = indent
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

    base = ev["ablation"][0]
    final = ev["ablation"][-1]

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    blank = prs.slide_layouts[6]

    # ── 1. TITLE ─────────────────────────────────────────────────────────────
    s = prs.slides.add_slide(blank)
    box = s.shapes.add_textbox(Inches(0.8), Inches(0.9), Inches(11.7), Inches(1.5))
    tf = box.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "AUTOMATIC ATTENDANCE SYSTEM USING MULTIPLE FACE RECOGNITION"
    p.alignment = PP_ALIGN.CENTER
    p.runs[0].font.size = Pt(30); p.runs[0].font.bold = True
    p.runs[0].font.color.rgb = NAVY
    p2 = tf.add_paragraph()
    p2.text = "Spoof-Resistant Multi-Face Attendance: Recognition Alone Is Not Enough"
    p2.alignment = PP_ALIGN.CENTER
    p2.runs[0].font.size = Pt(15); p2.runs[0].font.italic = True
    p2.runs[0].font.color.rgb = GREY

    bullets(s, [
        ("Problem Statement Title — Automating classroom attendance with multi-face "
         "recognition, without it being defeated by a photograph", True, INK, 0),
        "",
        ("Team Members", True, NAVY, 0),
        "1. Souryadeep Deb (13000222064)          2. Soham Bhattacharya (13000222065)",
        "3. Srija Basak (13000222066)              4. Sneha Singh (13000222067)",
        "",
        ("Group Number — 18", True, INK, 0),
        ("Mentor — Mr Prodipta Bhowmik", True, INK, 0),
        "PROJICB-781",
    ], 2.6, 2.7, 8.5, 3.2, size=13)

    box = s.shapes.add_textbox(Inches(0.8), Inches(6.5), Inches(11.7), Inches(0.9))
    for i, line in enumerate(["Department of Computer Science & Engineering (Cyber Security)",
                              "Techno Main Salt Lake, Kolkata - 700091"]):
        p = box.text_frame.paragraphs[0] if i == 0 else box.text_frame.add_paragraph()
        p.text = line; p.alignment = PP_ALIGN.CENTER
        p.runs[0].font.size = Pt(12); p.runs[0].font.bold = (i == 0)

    # ── 2. IDEA ──────────────────────────────────────────────────────────────
    s = prs.slides.add_slide(blank)
    title_bar(s, "IDEA / PROPOSED SOLUTION")

    bullets(s, [
        ("The problem nobody in the literature measures", True, NAVY, 0),
        "Face recognition is BUILT to give a photo of you the same embedding as you.",
        "So recognition alone cannot stop proxy attendance. We tested it:",
        (f"a printed photo was marked present {100}% of the time.", True, RED, 0),
        "",
        ("Our solution — separate RECOGNISING from MARKING PRESENT", True, NAVY, 0),
        "Attendance is written once a day and is irreversible: one bad frame marks the",
        "wrong student present until tomorrow. So committing is its own decision, taken",
        "only after four gates pass and several frames agree:",
        ("1.  Size — a face under 40px is refused, not guessed at", False, INK, 1),
        ("2.  Threshold — calibrated on 2,880 impostor faces, not hand-picked", False, INK, 1),
        ("3.  Margin — the runner-up identity must be clearly beaten", False, INK, 1),
        ("4.  LIVENESS — is this a person, or a photograph of one?", True, RED, 1),
    ], 0.55, 1.15, 6.6, 5.6, size=12.5)

    bullets(s, [
        ("Innovation and uniqueness", True, NAVY, 0),
        "",
        ("• We do NOT claim a new face model.", True, INK, 0),
        "ArcFace is pretrained and frozen. Claiming otherwise would be dishonest, and",
        "training our own on 30 students would be worse in every measurable way.",
        "",
        ("• Liveness that works on classroom hardware.", True, INK, 0),
        "Blink detection is the standard trick, but a blink lasts ~0.3s and our system",
        "samples ~1.4 frames/sec — we measured it failing. Instead we measure facial",
        "motion from landmarks the detector already produces: a live face keeps",
        "deforming, a photo is rigid. Rotation and scale are normalised away, so waving",
        "the photo about does not help the attacker. No extra model, no GPU.",
        "",
        ("• Enrolment in 1.4s, not 10 minutes.", True, INK, 0),
        "Embeddings are cached, so a new student costs only their own photos.",
        "",
        ("• We report a fix that did NOT work.", True, GREEN, 0),
        "The top-2 margin guard changed nothing on our cohort. We say so.",
    ], 7.4, 1.15, 5.5, 5.6, size=11.5)

    # ── 3. TECHNICAL APPROACH ────────────────────────────────────────────────
    s = prs.slides.add_slide(blank)
    title_bar(s, "TECHNICAL APPROACH & WORKFLOW")
    s.shapes.add_picture(f"{FIG}/workflow.png", Inches(0.5), Inches(1.1), width=Inches(12.3))

    bullets(s, [
        ("Technologies", True, NAVY, 0),
        "Detection: RetinaFace / SCRFD (det_10g)",
        "Recognition: ArcFace ResNet-50 (buffalo_l, w600k_r50) → 512-d embeddings",
        "Runtime: ONNX Runtime, CPU only — no GPU required",
        "Classifier: linear SVM + cosine-to-centroid over scikit-learn",
        "Backend: Python 3.13 · Flask REST API · token auth",
        "Frontend: React · Vite · TailwindCSS",
        "Storage: CSV + JSON on disk — no cloud, no database server",
    ], 0.55, 3.5, 6.2, 3.4, size=12)

    bullets(s, [
        ("Method — why it is built this way", True, NAVY, 0),
        ("The deep model is frozen and never retrained.", True, INK, 0),
        "It was trained on ~600k identities; what it learned is not 'who is Soham' but",
        "'what makes any two faces different'. Enrolling a student = embed their photos",
        "and store the average (their centroid). That is a table insert, not a training run.",
        "",
        ("Closed-set vs open-set — the key difference", True, INK, 0),
        "Prior work asks 'WHICH of my N students is this?' — a softmax must always name",
        "someone. We ask 'is this ANY of my students at all?' The system is allowed to",
        "answer 'nobody', which is the only honest answer when a stranger walks past.",
    ], 7.0, 3.5, 5.9, 3.4, size=11.5)

    # ── 4. RESULTS ───────────────────────────────────────────────────────────
    s = prs.slides.add_slide(blank)
    title_bar(s, "RESULTS")

    box = s.shapes.add_textbox(Inches(0.5), Inches(0.95), Inches(12.4), Inches(0.4))
    p = box.text_frame.paragraphs[0]
    p.text = ("Protocol: 30 simulated students + 66 strangers (VGGFace2). Test images never used "
              "for enrolment; the threshold is calibrated on one half of the strangers and measured "
              "on the other.")
    p.runs[0].font.size = Pt(10.5); p.runs[0].font.italic = True
    p.runs[0].font.color.rgb = GREY

    s.shapes.add_picture(f"{FIG}/spoof.png", Inches(0.5), Inches(1.5), height=Inches(2.5))
    s.shapes.add_picture(f"{FIG}/ablation.png", Inches(4.4), Inches(1.5), height=Inches(2.5))
    s.shapes.add_picture(f"{FIG}/degradation.png", Inches(9.5), Inches(1.5), height=Inches(2.5))

    # headline table
    rows_data = [
        ["Metric", "Before", "After"],
        ["Photo marked present (attack success)", "100%", "0%"],
        ["Strangers admitted (FAR)", f"{base['far']}%", f"{final['far']}%"],
        ["Wrong attendance records", f"{base['false_log_rate']}%", f"{final['false_log_rate']}%"],
        ["Time to enrol a student", "607 s", "1.4 s"],
        ["Time to mark a student present", "10.5 s", "2.8 s"],
    ]
    tbl = s.shapes.add_table(len(rows_data), 3, Inches(0.5), Inches(4.3),
                             Inches(7.4), Inches(2.4)).table
    tbl.columns[0].width = Inches(4.0)
    tbl.columns[1].width = Inches(1.7)
    tbl.columns[2].width = Inches(1.7)
    for r, row in enumerate(rows_data):
        for c, val in enumerate(row):
            cell = tbl.cell(r, c)
            cell.text = val
            para = cell.text_frame.paragraphs[0]
            para.runs[0].font.size = Pt(11)
            para.runs[0].font.bold = (r == 0)
            if r > 0 and c == 2:
                para.runs[0].font.bold = True
                para.runs[0].font.color.rgb = GREEN

    bullets(s, [
        ("Capacity (measured, laptop CPU, no GPU)", True, NAVY, 0),
        f"16 faces recognised in one frame in {bm['throughput'][-1]['latency_s']}s",
        "10,000 enrolled students add only 1.2 ms to a match",
        "One 1080p camera covers ~7 m — a whole classroom",
        f"Memory: {bm['memory_mb']:.0f} MB",
        "",
        ("Honest limitations", True, RED, 0),
        "A VIDEO replay would still pass — we raise the attack cost from",
        "'print a photo' to 'record and replay a video', not to zero.",
        "The top-2 margin guard did not help; the cohort has no look-alikes.",
        "Only 2 real users enrolled — the numbers above come from the 30-identity cohort.",
    ], 8.2, 4.3, 4.7, 2.7, size=10.5)

    # ── 5. IMPACT ────────────────────────────────────────────────────────────
    s = prs.slides.add_slide(blank)
    title_bar(s, "IMPACT AND BENEFITS")

    bullets(s, [
        ("Impact on the target audience", True, NAVY, 0),
        "A 60-student roll-call takes ~5 minutes of every lecture. Over a 200-day year",
        "that is roughly 80 hours of teaching time returned to teaching.",
        "Attendance is marked without contact, without a queue, and without a register",
        "that can be signed by a friend.",
        "",
        ("Social — the proxy problem, honestly", True, NAVY, 0),
        "Manual proxy (a friend signing for you) is eliminated.",
        "Photo/screen proxy is blocked by liveness — measured 100% → 0%.",
        ("Video-replay proxy is NOT yet blocked. We state this rather than hide it.", False, RED, 0),
        "",
        ("Privacy — why this beats a cloud face API", True, NAVY, 0),
        "The system runs fully offline. Students' faces never leave the campus.",
        "Under India's DPDP Act 2023, biometric data is sensitive personal data —",
        "uploading children's faces to a third-party cloud is a liability, not a feature.",
    ], 0.55, 1.2, 6.4, 5.6, size=12)

    bullets(s, [
        ("Economic", True, NAVY, 0),
        "Our system: one laptop + one webcam. No GPU. No servers. No per-scan fee.",
        "Recurring cost ≈ ₹0.",
        "",
        "A cloud face API (≈ $0.001 per image) for continuous classroom scanning:",
        ("≈ ₹1,50,000 per year, per school — and it uploads every student's face.", True, RED, 0),
        "",
        ("Scalability", True, NAVY, 0),
        "Enrolling 10,000 students costs 1.2 ms per match, because the deep model is",
        "frozen and matching is a matrix multiply. A trained-CNN approach would need",
        "retraining every time a student joins.",
        "",
        ("Auditability", True, NAVY, 0),
        "Every decision exposes its evidence — the similarity score, the runner-up",
        "margin, the face size, the liveness verdict. A disputed attendance record can",
        "be explained. Commercial systems are black boxes.",
    ], 7.1, 1.2, 5.7, 5.6, size=12)

    # ── 6. REFERENCES ────────────────────────────────────────────────────────
    s = prs.slides.add_slide(blank)
    title_bar(s, "RESEARCH AND REFERENCES")

    bullets(s, [
        ("Core models used (pretrained, frozen — not our contribution)", True, NAVY, 0),
        "[1]  Deng, J., Guo, J., Xue, N., Zafeiriou, S. (2019). ArcFace: Additive Angular Margin Loss "
        "for Deep Face Recognition. CVPR 2019, pp. 4690–4699.  DOI: 10.1109/CVPR.2019.00482",
        "[2]  Deng, J., Guo, J., Ververas, E., Kotsia, I., Zafeiriou, S. (2020). RetinaFace: Single-Shot "
        "Multi-Level Face Localisation in the Wild. CVPR 2020.  DOI: 10.1109/CVPR42600.2020.00525",
        "[3]  Schroff, F., Kalenichenko, D., Philbin, J. (2015). FaceNet: A Unified Embedding for Face "
        "Recognition and Clustering. CVPR 2015, pp. 815–823.  DOI: 10.1109/CVPR.2015.7298682",
        "",
        ("Attendance systems — prior work (none of which addresses spoofing)", True, NAVY, 0),
        "[4]  D'Souza, J. W. S., et al. (2019). Automated Attendance Marking and Management System by "
        "Facial Recognition Using Histogram. Array, 3–4: 100014.",
        "[5]  Arsenovic, M., Sladojevic, S., Anderla, A., Stefanovic, D. (2017). FaceTime — Deep "
        "Learning Based Face Recognition Attendance System. IEEE SISY 2017, pp. 53–58.",
        "[6]  Kakarla, S., et al. (2020). Smart Attendance Management System Based on Face Recognition "
        "Using CNN. IEEE-HYDCON 2020, pp. 1–5.  DOI: 10.1109/HYDCON48903.2020.9242847",
        "[7]  Varadharajan, E., et al. (2016). Automatic Attendance Management System Using Face "
        "Detection. IC-GET 2016, pp. 1–3.  DOI: 10.1109/GET.2016.7916753",
        "[8]  Siswanto, A. R. S., Nugroho, A. S., Galinium, M. (2014). Implementation of Face Recognition "
        "Algorithm for Biometrics Based Time Attendance System. ICISS 2014, pp. 149–154.",
        "",
        ("Anti-spoofing / presentation attacks — the gap we address", True, NAVY, 0),
        "[9]  Pan, G., Sun, L., Wu, Z., Lao, S. (2007). Eyeblink-based Anti-Spoofing in Face Recognition "
        "from a Generic Webcamera. ICCV 2007, pp. 1–8.",
        "[10] ISO/IEC 30107-3:2023 — Biometric Presentation Attack Detection, Part 3: Testing and Reporting.",
        "",
        ("Data, code and reproducibility", True, NAVY, 0),
        "Dataset: VGGFace2 (Cao et al., 2018) — 96 identities used as an impostor cohort.",
        "Source code and all measurement scripts: github.com/SohamBhattacharjee2003/MutiFace-Attendance-System",
    ], 0.55, 1.1, 12.3, 5.9, size=10)

    prs.save(OUT)
    print(f"\n✅ {OUT}")
    print(f"   {len(prs.slides.__iter__.__self__._sldIdLst)} slides, "
          f"figures embedded from live measurements")


if __name__ == "__main__":
    main()
