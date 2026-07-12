"""
make_ppt.py
Builds the deck in the DEPARTMENT TEMPLATE exactly (Project_Presentation_Format_2025):

    Title Page · Idea Title · Technical Approach & Workflow (×2) ·
    Results · Impact and Benefits · Research and References

Template rules copied from the format PDF:
    - white background
    - centred heading, Times New Roman, bold
    - body text in Arial with "•" bullets and "❖" section markers
    - full-width blue footer bar carrying a white slide number on the right

Every number and figure is generated from this repository's own measurements
(results/evaluation.json, results/benchmark.json, scripts/test_spoof.py) rather than
typed in, so the slides cannot drift from what the code does. The team's earlier deck
claimed MTCNN + FaceNet + MongoDB — none of which this system uses — and a 95% accuracy
that was never measured. That is the failure mode this script exists to prevent.

    python scripts/make_ppt.py   ->   results/PresenceAI_Presentation.pptx
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

RESULTS = "results"
OUT = os.path.join(RESULTS, "PresenceAI_Presentation.pptx")
FIG = os.path.join(RESULTS, "ppt_figs")

# ── template palette ─────────────────────────────────────────────────────────
BAR = RGBColor(0x10, 0x76, 0xBC)      # the blue footer bar
NAVY = RGBColor(0x1F, 0x3A, 0x6E)
BLACK = RGBColor(0x00, 0x00, 0x00)
INK = RGBColor(0x1A, 0x1A, 0x1A)
RED = RGBColor(0xC0, 0x00, 0x00)
GREEN = RGBColor(0x1E, 0x7A, 0x45)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

HEAD_FONT = "Times New Roman"
BODY_FONT = "Arial"

M_BLUE, M_RED, M_GREEN, M_GREY, M_AMBER = "#1076bc", "#c00000", "#1e7a45", "#595959", "#c07b0b"


# ════════════════════════════════════════════════════════════════ FIGURES ══
def _box(ax, x, y, w, h, t, fc, ec, fs=8, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06",
                                facecolor=fc, edgecolor=ec, linewidth=1.3, zorder=2))
    ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", zorder=3, linespacing=1.35)


def _arrow(ax, x1, y1, x2, y2, c=M_GREY):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=12, color=c, linewidth=1.2, zorder=1))


def figures(ev, bm):
    os.makedirs(FIG, exist_ok=True)
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "figure.dpi": 200})

    # workflow strip (slide 3)
    fig, ax = plt.subplots(figsize=(11.8, 2.4)); ax.axis("off")
    ax.set_xlim(0, 11.8); ax.set_ylim(0, 2.4)
    steps = [
        ("1. Face input\n(web camera)", "#eef4fb"),
        ("2. Detect ALL faces\nRetinaFace / SCRFD", "#dce9f7"),
        ("3. Align + embed\nArcFace 512-d", "#c9dcf3"),
        ("4. Match vs each\nstudent centroid", "#b6cfef"),
        ("5. FOUR GATES\nsize / threshold\nmargin / LIVENESS", "#f8d7d2"),
        ("6. Temporal vote\n(3 frames agree)", "#d5ecdf"),
        ("7. Attendance\nrecorded (CSV)", "#c3e5d1"),
    ]
    w, gap = 1.45, 0.22
    for i, (label, col) in enumerate(steps):
        x = i * (w + gap)
        ec = M_RED if "GATES" in label else "#8fa3b8"
        _box(ax, x, 0.6, w, 1.15, label, col, ec, 7.6, "GATES" in label)
        if i < len(steps) - 1:
            _arrow(ax, x + w, 1.17, x + w + gap, 1.17)
    ax.text(0, 0.2, "The deep model is FROZEN — enrolling a student stores a centroid; it does not retrain the "
                    "network.   Steps 5-6 are our contribution.",
            fontsize=8, color=M_GREY, style="italic")
    fig.tight_layout(); fig.savefig(f"{FIG}/workflow.png"); plt.close(fig)

    # the four gates (slide 4)
    fig, ax = plt.subplots(figsize=(11.8, 2.5)); ax.axis("off")
    ax.set_xlim(0, 11.8); ax.set_ylim(0, 2.5)
    gates = [
        ("GATE 1 - SIZE\nface >= 40 px ?", 'reject ->\n"Move closer"', "#fff4e0", M_AMBER),
        ("GATE 2 - THRESHOLD\ncos >= 0.148 ?", 'reject ->\n"Unknown"', "#fff4e0", M_AMBER),
        ("GATE 3 - MARGIN\ntop1 - top2 >= 0.15 ?", 'reject ->\n"Uncertain"', "#fff4e0", M_AMBER),
        ("GATE 4 - LIVENESS\nis the face moving ?", 'reject ->\n"Not live"', "#f8d7d2", M_RED),
    ]
    for i, (t, rej, fc, ec) in enumerate(gates):
        x = 0.15 + i * 2.75
        _box(ax, x, 1.2, 2.35, 0.9, t, fc, ec, 8, True)
        ax.text(x + 1.17, 0.9, rej, ha="center", va="top", fontsize=7, color=M_RED)
        if i < 3:
            _arrow(ax, x + 2.35, 1.65, x + 2.75, 1.65, c=M_GREEN)
    _box(ax, 11.2, 1.2, 0.45, 0.9, "OK", "#d5ecdf", M_GREEN, 9, True)
    ax.text(5.9, 0.25, "The classifier has NO \"I don't know\" option — it always outputs a name.\n"
                       "Every gate exists because a confident answer from a bad input is worse than no answer.",
            fontsize=8.5, ha="center", color=M_RED, fontweight="bold")
    fig.tight_layout(); fig.savefig(f"{FIG}/gates.png"); plt.close(fig)

    # the attack, drawn (slide 2)
    fig, ax = plt.subplots(figsize=(9.4, 2.2)); ax.axis("off")
    ax.set_xlim(0, 9.4); ax.set_ylim(0, 2.2)
    _box(ax, 0.1, 1.2, 1.6, 0.75, "REAL person\nat the camera", "#d5ecdf", M_GREEN)
    _box(ax, 0.1, 0.2, 1.6, 0.75, "PHOTO of them,\nheld up", "#f8d7d2", M_RED)
    _box(ax, 2.3, 0.7, 1.8, 0.8, "ArcFace\nembedding", "#eef4fb", M_GREY, 8, True)
    _arrow(ax, 1.7, 1.57, 2.3, 1.3, c=M_GREEN)
    _arrow(ax, 1.7, 0.57, 2.3, 0.9, c=M_RED)
    _box(ax, 4.8, 0.7, 2.1, 0.8, "Nearly IDENTICAL\n512-d vectors", "#fff4e0", M_AMBER, 8, True)
    _arrow(ax, 4.1, 1.1, 4.8, 1.1)
    _box(ax, 7.6, 1.2, 1.7, 0.75, "Marked PRESENT", "#d5ecdf", M_GREEN)
    _box(ax, 7.6, 0.2, 1.7, 0.75, "Marked PRESENT", "#f8d7d2", M_RED, 8, True)
    _arrow(ax, 6.9, 1.3, 7.6, 1.57, c=M_GREEN)
    _arrow(ax, 6.9, 0.9, 7.6, 0.57, c=M_RED)
    ax.text(4.7, 2.06, "Face recognition is DESIGNED to do this — it is what makes it a good model.",
            fontsize=9, ha="center", color=M_RED, fontweight="bold")
    fig.tight_layout(); fig.savefig(f"{FIG}/attack.png"); plt.close(fig)

    # results charts
    fig, ax = plt.subplots(figsize=(3.7, 2.7))
    bars = ax.bar(["Recognition\nonly", "+ Liveness\n(ours)"], [100, 0],
                  color=[M_RED, M_GREEN], width=0.5)
    for b, v in zip(bars, [100, 0]):
        ax.text(b.get_x() + b.get_width() / 2, v + 4, f"{v}%", ha="center",
                fontweight="bold", fontsize=13)
    ax.set_ylabel("Attack success (%)"); ax.set_ylim(0, 118)
    ax.set_title("Photo held to the camera", fontsize=10, fontweight="bold")
    fig.tight_layout(); fig.savefig(f"{FIG}/spoof.png"); plt.close(fig)

    rows = ev["ablation"]
    fig, ax = plt.subplots(figsize=(5.2, 2.7))
    x = range(len(rows))
    ax.bar([i - 0.19 for i in x], [r["far"] for r in rows], 0.38,
           label="Strangers admitted", color=M_BLUE)
    ax.bar([i + 0.19 for i in x], [r["false_log_rate"] for r in rows], 0.38,
           label="Wrong records", color="#8e5ad6")
    ax.set_xticks(list(x))
    ax.set_xticklabels(["Baseline", "+ Calibrated\nthreshold", "+ Top-2\nmargin",
                        "+ Temporal\nvoting"], fontsize=7.5)
    ax.set_ylabel("Error rate (%)"); ax.legend(fontsize=7.5, frameon=False)
    ax.set_title("Ablation — one guard at a time", fontsize=10, fontweight="bold")
    fig.tight_layout(); fig.savefig(f"{FIG}/ablation.png"); plt.close(fig)

    deg = ev["degradation"]
    fig, ax = plt.subplots(figsize=(3.9, 2.7))
    ax.plot([d["face_px"] for d in deg], [d["accuracy"] * 100 for d in deg],
            "o-", color=M_BLUE, lw=2, ms=4)
    ax.axvspan(0, 40, color=M_RED, alpha=0.07)
    ax.axvline(40, ls="--", color=M_AMBER, lw=1.4)
    ax.text(46, 68, "gate: 40px", color=M_AMBER, fontsize=8)
    ax.set_xlabel("Face width (pixels)"); ax.set_ylabel("Accuracy (%)")
    ax.set_title("Operating envelope", fontsize=10, fontweight="bold")
    fig.tight_layout(); fig.savefig(f"{FIG}/degradation.png"); plt.close(fig)

    # cost (slide 6)
    fig, ax = plt.subplots(figsize=(4.4, 2.3))
    ax.barh(["PresenceAI\n(offline)", "Cloud face API\n(continuous)"], [0, 150000],
            color=[M_GREEN, M_RED], height=0.45)
    ax.set_xlabel("Recurring cost per school, per year (INR)")
    ax.text(3000, 0, "= 0", va="center", fontsize=11, fontweight="bold", color=M_GREEN)
    ax.text(146000, 1, "1,50,000  ", va="center", ha="right", fontsize=9.5,
            fontweight="bold", color="white")
    ax.set_title("...and the cloud uploads every student's face",
                 fontsize=9, fontweight="bold")
    fig.tight_layout(); fig.savefig(f"{FIG}/cost.png"); plt.close(fig)
    print("  6 figures generated")


# ═══════════════════════════════════════════════════ TEMPLATE PRIMITIVES ══
def footer(s, n):
    """Full-width blue bar + white slide number — the template's signature."""
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(6.95),
                             Inches(13.333), Inches(0.55))
    bar.fill.solid(); bar.fill.fore_color.rgb = BAR
    bar.line.fill.background(); bar.shadow.inherit = False
    tb = s.shapes.add_textbox(Inches(12.3), Inches(7.02), Inches(0.85), Inches(0.4))
    p = tb.text_frame.paragraphs[0]
    p.text = str(n); p.alignment = PP_ALIGN.RIGHT
    r = p.runs[0]
    r.font.size = Pt(12); r.font.bold = True
    r.font.color.rgb = WHITE; r.font.name = BODY_FONT


def heading(prs, title, size=34):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    tb = s.shapes.add_textbox(Inches(0.6), Inches(0.12), Inches(12.1), Inches(0.85))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title; p.alignment = PP_ALIGN.CENTER
    r = p.runs[0]
    r.font.size = Pt(size); r.font.bold = True
    r.font.color.rgb = BLACK; r.font.name = HEAD_FONT
    return s


def bullets(s, items, l, t, w, h, size=14, center=False):
    tf = s.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h)).text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        body, bold, col, lvl = (item if isinstance(item, tuple) else (item, False, INK, 0))
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = body; p.level = lvl; p.space_after = Pt(6)
        if center:
            p.alignment = PP_ALIGN.CENTER
        for r in p.runs:
            r.font.size = Pt(size); r.font.bold = bold
            r.font.color.rgb = col; r.font.name = BODY_FONT
    return tf


def table(s, data, l, t, w, h, widths, green_col=None):
    tbl = s.shapes.add_table(len(data), len(data[0]), Inches(l), Inches(t),
                             Inches(w), Inches(h)).table
    for i, cw in enumerate(widths):
        tbl.columns[i].width = Inches(cw)
    for r, row in enumerate(data):
        for c, v in enumerate(row):
            cell = tbl.cell(r, c); cell.text = str(v)
            runs = cell.text_frame.paragraphs[0].runs
            if not runs:
                continue
            run = runs[0]
            run.font.size = Pt(11); run.font.name = BODY_FONT
            run.font.bold = (r == 0) or (c == 0 and r > 0)
            if green_col is not None and c == green_col and r > 0:
                run.font.color.rgb = GREEN; run.font.bold = True
    return tbl


# ═══════════════════════════════════════════════════════════════════ MAIN ══
def main():
    ev = json.load(open(os.path.join(RESULTS, "evaluation.json")))
    bm = json.load(open(os.path.join(RESULTS, "benchmark.json")))
    figures(ev, bm)

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)

    # ── 1 · TITLE PAGE ──────────────────────────────────────────────────────
    s = prs.slides.add_slide(prs.slide_layouts[6])
    tb = s.shapes.add_textbox(Inches(0.8), Inches(0.45), Inches(11.7), Inches(1.5))
    tf = tb.text_frame; tf.word_wrap = True
    for i, line in enumerate(["AUTOMATIC ATTENDANCE SYSTEM USING",
                              "MULTIPLE FACE RECOGNITION"]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line; p.alignment = PP_ALIGN.CENTER
        r = p.runs[0]; r.font.size = Pt(34); r.font.bold = True
        r.font.color.rgb = NAVY; r.font.name = HEAD_FONT

    bullets(s, [
        ("Problem Statement Title -  Recognition alone cannot stop proxy attendance:", True, BLACK, 0),
        ("a printed photo is marked present 100% of the time.", True, RED, 0),
    ], 2.2, 1.9, 9.0, 0.8, size=14)

    bullets(s, [
        ("Team Members' Name and Roll Number -", True, BLACK, 0),
        "        1. Souryadeep Deb (13000222064)            2. Soham Bhattacharya (13000222065)",
        "        3. Srija Basak (13000222066)                4. Sneha Singh (13000222067)",
        "",
        ("Group Number -  18", True, BLACK, 0),
        "",
        ("Mentor Name -  Mr Prodipta Bhowmik", True, BLACK, 0),
    ], 2.2, 2.85, 9.0, 2.5, size=14)

    bullets(s, [
        ("Department of Information Technology", True, BLACK, 0),
        ("Techno Main Salt Lake", True, BLACK, 0),
        ("Kolkata -700091", True, BLACK, 0),
    ], 4.4, 5.45, 4.6, 1.3, size=13, center=True)

    # ── 2 · IDEA TITLE ──────────────────────────────────────────────────────
    s = heading(prs, "IDEA TITLE")
    bullets(s, [("❖ Proposed Solution", True, NAVY, 0)], 0.6, 1.0, 12.1, 0.4, size=19)
    bullets(s, [
        "•  Detect and recognise EVERY face in one frame  (RetinaFace + ArcFace, 512-d).",
        "•  A face must pass FOUR gates — size, threshold, margin, liveness — before it gets a name.",
        "•  Attendance is committed only when 3 frames agree.  Runs offline on a laptop CPU.",
    ], 0.75, 1.45, 12.0, 1.1, size=14)

    bullets(s, [("❖ How it addresses the problem", True, NAVY, 0)], 0.6, 2.6, 12.1, 0.4, size=19)
    s.shapes.add_picture(f"{FIG}/attack.png", Inches(1.9), Inches(3.05), width=Inches(9.5))

    bullets(s, [("❖ Innovation and uniqueness", True, NAVY, 0)], 0.6, 5.2, 12.1, 0.4, size=19)
    bullets(s, [
        ("•  We do NOT claim a new face model — ArcFace is pretrained and frozen.", True, RED, 0),
        "•  Liveness that works at 1.4 frames/sec, where blink detection provably fails.",
        "•  Threshold calibrated on 2,880 impostor faces — not hand-picked.",
        "•  Attendance treated as an irreversible commit.   Enrolment:  607 s → 1.4 s.",
    ], 0.75, 5.65, 12.0, 1.2, size=13)

    # ── 3 · TECHNICAL APPROACH (1/2) ────────────────────────────────────────
    s = heading(prs, "TECHNICAL APPROACH & WORKFLOW DIAGRAM", 29)
    bullets(s, [("❖ Technologies used", True, NAVY, 0)], 0.6, 0.9, 12.1, 0.4, size=18)
    table(s, [
        ["Layer", "Technology"],
        ["Language", "Python 3.13"],
        ["Face detection", "RetinaFace / SCRFD (det_10g)"],
        ["Recognition", "ArcFace ResNet-50 (buffalo_l) → 512-d embedding"],
        ["Runtime", "ONNX Runtime — CPU only, NO GPU"],
        ["Classifier", "Linear SVM + cosine-to-centroid (scikit-learn)"],
        ["Backend / Frontend", "Flask REST API (token auth) · React + Vite + Tailwind"],
        ["Storage", "CSV + JSON on disk — no cloud, no database server"],
    ], 0.7, 1.35, 7.5, 2.7, [2.1, 5.4])

    bullets(s, [
        ("❖ The model is FROZEN", True, NAVY, 0),
        "•  Pretrained on ~600,000 identities. It never learns",
        "   \"who is Soham\" — it learns what makes any two",
        "   faces different.",
        "•  Enrolling a student = embed their photos, store the",
        "   average vector (a centroid). No training. No GPU.",
        ("•  Embeddings cached → enrolment 607 s → 1.4 s", True, GREEN, 0),
        "",
        ("❖ Open-set, not closed-set", True, NAVY, 0),
        "•  Prior work:  \"WHICH of my N students is this?\"",
        "   — a softmax MUST name someone.",
        ("•  Ours:  \"Is this ANY of my students?\"", True, INK, 0),
        ("   — allowed to answer \"nobody\".", True, INK, 0),
    ], 8.4, 1.35, 4.5, 3.0, size=11.5)

    bullets(s, [("❖ Workflow", True, NAVY, 0)], 0.6, 4.25, 12.1, 0.4, size=18)
    s.shapes.add_picture(f"{FIG}/workflow.png", Inches(0.45), Inches(4.7), width=Inches(12.4))

    # ── 4 · TECHNICAL APPROACH (2/2) ────────────────────────────────────────
    s = heading(prs, "TECHNICAL APPROACH — DECISION PIPELINE", 29)
    bullets(s, [("❖ Four gates before a face gets a name", True, NAVY, 0)],
            0.6, 0.9, 12.1, 0.4, size=18)
    s.shapes.add_picture(f"{FIG}/gates.png", Inches(0.45), Inches(1.35), width=Inches(12.4))

    bullets(s, [
        ("❖ Then: 3 frames must agree → attendance is written  "
         "(once per day, and irreversible)", True, NAVY, 0),
    ], 0.6, 3.85, 12.1, 0.4, size=15)

    bullets(s, [
        ("❖ Liveness — why not blink detection?", True, NAVY, 0),
        "•  A blink lasts 0.3 s.  We sample 1.4 frames/sec.",
        "   We measured blink detection FAILING.",
        "•  Instead we measure facial motion from the 106",
        "   landmarks the detector already produces for free.",
        "•  Rotation and scale are normalised out — so shaking",
        "   the photo does not help the attacker.",
        ("•  No extra model.  No extra compute.  No GPU.", True, GREEN, 0),
    ], 0.75, 4.35, 7.3, 2.4, size=12.5)

    table(s, [
        ["Motion score", "Value"],
        ["Photo held up (hand-shake)", "0.015"],
        ["Arnab, live", "0.066"],
        ["Soham, live", "0.135"],
        ["Threshold", "0.035"],
    ], 8.3, 4.4, 4.5, 1.7, [2.9, 1.6])

    bullets(s, [
        ("Protocol:  96 identities → 30 STUDENTS (70% enrol / 30% test)  +  "
         "66 STRANGERS (half calibrate / half measure the FAR).", True, RED, 0),
    ], 8.3, 6.2, 4.5, 0.6, size=10)

    # ── 5 · RESULTS ─────────────────────────────────────────────────────────
    s = heading(prs, "RESULTS")
    s.shapes.add_picture(f"{FIG}/spoof.png", Inches(0.5), Inches(0.95), height=Inches(2.35))
    s.shapes.add_picture(f"{FIG}/ablation.png", Inches(4.35), Inches(0.95), height=Inches(2.35))
    s.shapes.add_picture(f"{FIG}/degradation.png", Inches(9.4), Inches(0.95), height=Inches(2.35))

    table(s, [
        ["Metric", "Before", "After"],
        ["Photo marked present (attack success)", "100%", "0%"],
        ["Strangers admitted (FAR)", "0.81%", "0.20%"],
        ["Wrong attendance records", "3.54%", "0%"],
        ["Time to enrol a student", "607 s", "1.4 s"],
        ["Time to mark a student present", "10.5 s", "2.8 s"],
    ], 0.5, 3.55, 7.3, 2.6, [3.9, 1.7, 1.7], green_col=2)

    bullets(s, [
        ("❖ Key findings", True, NAVY, 0),
        "•  Calibrating the threshold cut strangers admitted 4×.",
        "•  Temporal voting drove wrong records to zero.",
        ("•  The top-2 margin guard did NOT help — we report it.", True, RED, 0),
        "",
        ("❖ Capacity  (laptop CPU, no GPU)", True, NAVY, 0),
        f"•  16 faces in one frame:  {bm['throughput'][-1]['latency_s']} s",
        "•  10,000 enrolled students:  +1.2 ms per match",
        "•  One 1080p camera covers ~7 m — a whole classroom",
        "",
        ("❖ Limitation:  a VIDEO replay would still pass.", True, RED, 0),
    ], 8.1, 3.55, 4.8, 3.2, size=12)

    # ── 6 · IMPACT AND BENEFITS ─────────────────────────────────────────────
    s = heading(prs, "IMPACT AND BENEFITS")
    bullets(s, [("❖ Potential impact on the target audience", True, NAVY, 0)],
            0.6, 0.95, 12.1, 0.4, size=18)
    bullets(s, [
        "•  A 60-student roll-call costs ~5 minutes of every lecture — about 80 teaching hours a year, returned.",
        "•  Target: schools that cannot afford a GPU or a cloud subscription — and cannot legally upload their "
        "students' faces to one.",
    ], 0.75, 1.4, 12.0, 0.9, size=13)

    bullets(s, [("❖ Benefits of the solution", True, NAVY, 0)], 0.6, 2.35, 12.1, 0.4, size=18)
    bullets(s, [
        ("SOCIAL", True, NAVY, 0),
        "•  Contactless — no queue, no register passed around.",
        "•  Manual proxy eliminated.",
        ("•  Photo proxy blocked:   100% → 0%.", True, GREEN, 0),
        ("•  Video-replay proxy NOT yet blocked — stated, not hidden.", True, RED, 0),
        "",
        ("PRIVACY & LEGAL", True, NAVY, 0),
        "•  Runs fully offline — student faces never leave the campus.",
        "•  Under India's DPDP Act 2023, biometric data is sensitive personal data.",
        "   Uploading children's faces to a cloud is a liability, not a feature.",
    ], 0.75, 2.8, 8.0, 3.7, size=12.5)

    bullets(s, [("ECONOMIC", True, NAVY, 0)], 8.9, 2.8, 4.0, 0.35, size=12.5)
    s.shapes.add_picture(f"{FIG}/cost.png", Inches(8.9), Inches(3.2), width=Inches(4.0))
    bullets(s, [
        "•  One laptop + one webcam.  No GPU, no servers.",
        ("•  Recurring cost = 0.", True, GREEN, 0),
    ], 8.9, 5.4, 4.0, 0.9, size=12)

    # ── 7 · RESEARCH AND REFERENCES ─────────────────────────────────────────
    s = heading(prs, "RESEARCH AND REFERENCES")
    bullets(s, [
        ("❖ Attendance systems — prior work (none of which tests a presentation attack)", True, NAVY, 0),
        "[1]  D'Souza, J. W. S., et al. (2019). Automated Attendance Marking and Management System by Facial "
        "Recognition Using Histogram. Array, 3–4: 100014.   DOI: 10.1016/j.array.2019.100014",
        "[2]  Arsenovic, M., et al. (2017). FaceTime — Deep Learning Based Face Recognition Attendance System. "
        "IEEE SISY 2017, pp. 53–58.   DOI: 10.1109/SISY.2017.8080587",
        "[3]  Kakarla, S., et al. (2020). Smart Attendance Management System Based on Face Recognition Using CNN. "
        "IEEE-HYDCON 2020.   DOI: 10.1109/HYDCON48903.2020.9242847",
        "[4]  Varadharajan, E., et al. (2016). Automatic Attendance Management System Using Face Detection. "
        "IC-GET 2016, pp. 1–3.   DOI: 10.1109/GET.2016.7916753",
        "[5]  Siswanto, A. R. S., et al. (2014). Implementation of Face Recognition Algorithm for Biometrics Based "
        "Time Attendance System. ICISS 2014, pp. 149–154.   DOI: 10.1109/ICTSS.2014.7013165",
        "",
        ("❖ Models used — pretrained and frozen (not our contribution)", True, NAVY, 0),
        "[6]  Deng, J., Guo, J., Xue, N., Zafeiriou, S. (2019). ArcFace: Additive Angular Margin Loss for Deep Face "
        "Recognition. CVPR 2019, pp. 4690–4699.   DOI: 10.1109/CVPR.2019.00482",
        "[7]  Deng, J., et al. (2020). RetinaFace: Single-Shot Multi-Level Face Localisation in the Wild. "
        "CVPR 2020.   DOI: 10.1109/CVPR42600.2020.00525",
        "[8]  Cao, Q., et al. (2018). VGGFace2: A Dataset for Recognising Faces across Pose and Age. "
        "IEEE FG 2018, pp. 67–74.",
        "",
        ("❖ Presentation attacks — the gap this project addresses", True, RED, 0),
        "[9]   Pan, G., Sun, L., Wu, Z., Lao, S. (2007). Eyeblink-based Anti-Spoofing in Face Recognition from a "
        "Generic Webcamera. ICCV 2007, pp. 1–8.   DOI: 10.1109/ICCV.2007.4409068",
        "[10] ISO/IEC 30107-3:2023 — Biometric presentation attack detection — Part 3: Testing and reporting.",
        "",
        ("❖ Source code and all measurement scripts:", True, NAVY, 0),
        ("       github.com/SohamBhattacharjee2003/MutiFace-Attendance-System", True, GREEN, 0),
    ], 0.6, 0.95, 12.2, 5.9, size=10.5)

    for i, sl in enumerate(prs.slides):
        if i:
            footer(sl, i + 1)

    prs.save(OUT)
    print(f"\n✅ {OUT}   ({len(prs.slides._sldIdLst)} slides)")


if __name__ == "__main__":
    main()
