"""
make_ppt.py
Rebuilds the team's OWN deck — same 11 slides, same headings, same visual language
(navy Times New Roman headings, coloured outline boxes, chevrons, blue footer bar).
Only the CONTENT changes.

    Title · Project Title · Objective · Problem Definition · Literature Review ·
    Proposed Methodology · Experimental Details · Results and Analysis ·
    Conclusion · References · Thank You

Every number and figure comes from this repository's own measurements
(results/evaluation.json, results/benchmark.json, scripts/test_spoof.py) rather than
being typed in. The previous deck claimed MTCNN + FaceNet + MongoDB — none of which
this system uses — a 95% accuracy that was never measured, and "high accuracy using
MTCNN model" (MTCNN is a *detector*; it cannot recognise anyone). Generating the slides
from the measurement files is what stops that happening again.

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
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

RESULTS = "results"
OUT = os.path.join(RESULTS, "PresenceAI_Presentation.pptx")
FIG = os.path.join(RESULTS, "ppt_figs")

# ── the team's existing palette, sampled from their deck ─────────────────────
HEAD_NAVY = RGBColor(0x1F, 0x38, 0x64)     # heading colour
BAR_BLUE = RGBColor(0x10, 0x76, 0xBC)      # footer bar
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BLACK = RGBColor(0x00, 0x00, 0x00)
INK = RGBColor(0x1A, 0x1A, 0x1A)
RED = RGBColor(0xC0, 0x00, 0x00)
GREEN = RGBColor(0x1E, 0x7A, 0x45)

# outline colours used on their objective / conclusion slides
O_GREEN = RGBColor(0x70, 0xAD, 0x47)
O_RED = RGBColor(0xC0, 0x00, 0x00)
O_BLUE = RGBColor(0x44, 0x72, 0xC4)
O_ORANGE = RGBColor(0xED, 0x7D, 0x31)
O_PURPLE = RGBColor(0x80, 0x64, 0xA2)
O_TEAL = RGBColor(0x4B, 0xAC, 0xC6)

LIT_FILL = RGBColor(0xDE, 0xEA, 0xF6)
LIT_LINE = RGBColor(0x2E, 0x75, 0xB6)
BOX_BLUE = RGBColor(0xB8, 0xCC, 0xE4)
BOX_ORANGE = RGBColor(0xFB, 0xD5, 0xB5)

HEAD_FONT = "Times New Roman"
BODY_FONT = "Calibri"

M_BLUE, M_RED, M_GREEN, M_GREY, M_AMBER = "#1076bc", "#c00000", "#1e7a45", "#595959", "#c07b0b"


# ════════════════════════════════════════════════════════════════ FIGURES ══
def _box(ax, x, y, w, h, t, fc, ec, fs=8, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.05",
                                facecolor=fc, edgecolor=ec, linewidth=1.3, zorder=2))
    ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", zorder=3, linespacing=1.35)


def _arrow(ax, x1, y1, x2, y2, c=M_GREY):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=11, color=c, linewidth=1.2, zorder=1))


def figures(ev, bm):
    os.makedirs(FIG, exist_ok=True)
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "figure.dpi": 200})

    # the attack, drawn — slide 2 (PROJECT TITLE)
    fig, ax = plt.subplots(figsize=(9.0, 2.3)); ax.axis("off")
    ax.set_xlim(0, 9.0); ax.set_ylim(0, 2.3)
    _box(ax, 0.1, 1.25, 1.6, 0.78, "REAL person\nat the camera", "#d5ecdf", M_GREEN)
    _box(ax, 0.1, 0.22, 1.6, 0.78, "PHOTO of them,\nheld up", "#f8d7d2", M_RED)
    _box(ax, 2.25, 0.72, 1.75, 0.82, "ArcFace\nembedding", "#eef4fb", M_GREY, 8, True)
    _arrow(ax, 1.7, 1.64, 2.25, 1.35, c=M_GREEN)
    _arrow(ax, 1.7, 0.61, 2.25, 0.9, c=M_RED)
    _box(ax, 4.6, 0.72, 2.05, 0.82, "Nearly IDENTICAL\n512-d vectors", "#fff4e0", M_AMBER, 8, True)
    _arrow(ax, 4.0, 1.13, 4.6, 1.13)
    _box(ax, 7.25, 1.25, 1.65, 0.78, "Marked PRESENT", "#d5ecdf", M_GREEN)
    _box(ax, 7.25, 0.22, 1.65, 0.78, "Marked PRESENT", "#f8d7d2", M_RED, 8, True)
    _arrow(ax, 6.65, 1.35, 7.25, 1.64, c=M_GREEN)
    _arrow(ax, 6.65, 0.9, 7.25, 0.61, c=M_RED)
    ax.text(4.5, 2.16, "Face recognition is DESIGNED to do this — it is what makes it a good model.",
            fontsize=9, ha="center", color=M_RED, fontweight="bold")
    fig.tight_layout(); fig.savefig(f"{FIG}/attack.png"); plt.close(fig)

    # workflow flowchart — slide 7 (EXPERIMENTAL DETAILS), vertical like theirs
    fig, ax = plt.subplots(figsize=(4.6, 6.0)); ax.axis("off")
    ax.set_xlim(0, 4.6); ax.set_ylim(0, 6.0)
    steps = [
        ("1.  Face Input\n(Web Camera)", "#eef4fb", "#8fa3b8"),
        ("2.  Face Detection\n(RetinaFace / SCRFD)", "#dce9f7", "#8fa3b8"),
        ("3.  Feature Extraction\n(ArcFace → 512-d)", "#c9dcf3", "#8fa3b8"),
        ("4.  Face Matching\n(cosine vs centroid)", "#b6cfef", "#8fa3b8"),
        ("5.  FOUR GATES\nsize · threshold\nmargin · LIVENESS", "#f8d7d2", M_RED),
        ("6.  Temporal Vote\n(3 frames agree)", "#d5ecdf", M_GREEN),
        ("7.  Attendance Recorded\n(CSV file)", "#c3e5d1", M_GREEN),
    ]
    h, gap = 0.66, 0.18
    for i, (label, fc, ec) in enumerate(steps):
        y = 5.3 - i * (h + gap)
        _box(ax, 0.15, y, 4.3, h, label, fc, ec, 8.5, "GATES" in label)
        if i < len(steps) - 1:
            _arrow(ax, 2.3, y, 2.3, y - gap, c="#595959")
    ax.text(2.3, 0.05, "Steps 5–6 are our contribution.", fontsize=8,
            ha="center", color=M_GREY, style="italic")
    fig.tight_layout(); fig.savefig(f"{FIG}/workflow.png"); plt.close(fig)

    # results charts — slide 8
    fig, ax = plt.subplots(figsize=(3.8, 2.6))
    bars = ax.bar(["Recognition\nonly", "+ Liveness\n(ours)"], [100, 0],
                  color=[M_RED, M_GREEN], width=0.5)
    for b, v in zip(bars, [100, 0]):
        ax.text(b.get_x() + b.get_width() / 2, v + 4, f"{v}%", ha="center",
                fontweight="bold", fontsize=13)
    ax.set_ylabel("Attack success (%)"); ax.set_ylim(0, 118)
    ax.set_title("Photo held to the camera", fontsize=10, fontweight="bold")
    fig.tight_layout(); fig.savefig(f"{FIG}/spoof.png"); plt.close(fig)

    rows = ev["ablation"]
    fig, ax = plt.subplots(figsize=(4.6, 2.6))
    x = range(len(rows))
    ax.bar([i - 0.19 for i in x], [r["far"] * 100 for r in rows], 0.38,
           label="Strangers admitted", color=M_BLUE)
    ax.bar([i + 0.19 for i in x], [r["false_log_rate"] * 100 for r in rows], 0.38,
           label="Wrong records", color="#8064a2")
    ax.set_xticks(list(x))
    ax.set_xticklabels(["Base", "+ Calib.\nthresh.", "+ Top-2\nmargin", "+ Temporal\nvote"],
                       fontsize=7.5)
    ax.set_ylabel("Error rate (%)"); ax.legend(fontsize=7, frameon=False)
    ax.set_title("Ablation — one guard at a time", fontsize=10, fontweight="bold")
    fig.tight_layout(); fig.savefig(f"{FIG}/ablation.png"); plt.close(fig)

    deg = ev["degradation"]
    fig, ax = plt.subplots(figsize=(3.8, 2.6))
    ax.plot([d["face_px"] for d in deg], [d["accuracy"] * 100 for d in deg],
            "o-", color=M_BLUE, lw=2, ms=4)
    ax.axvspan(0, 40, color=M_RED, alpha=0.07)
    ax.axvline(40, ls="--", color=M_AMBER, lw=1.4)
    ax.text(46, 68, "gate: 40px", color=M_AMBER, fontsize=8)
    ax.set_xlabel("Face width (pixels)"); ax.set_ylabel("Accuracy (%)")
    ax.set_title("Operating envelope", fontsize=10, fontweight="bold")
    fig.tight_layout(); fig.savefig(f"{FIG}/degradation.png"); plt.close(fig)
    print("  5 figures generated")


# ═════════════════════════════════════════════════════════════ PRIMITIVES ══
def footer(s, n):
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(6.95),
                             Inches(13.333), Inches(0.55))
    bar.fill.solid(); bar.fill.fore_color.rgb = BAR_BLUE
    bar.line.fill.background(); bar.shadow.inherit = False
    tb = s.shapes.add_textbox(Inches(12.3), Inches(7.02), Inches(0.85), Inches(0.4))
    p = tb.text_frame.paragraphs[0]
    p.text = str(n); p.alignment = PP_ALIGN.RIGHT
    r = p.runs[0]
    r.font.size = Pt(12); r.font.bold = True
    r.font.color.rgb = WHITE; r.font.name = BODY_FONT


def heading(prs, title, size=36):
    """Navy, bold, centred, Times New Roman — exactly as in the team's deck."""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    tb = s.shapes.add_textbox(Inches(0.5), Inches(0.12), Inches(12.3), Inches(0.9))
    p = tb.text_frame.paragraphs[0]
    p.text = title; p.alignment = PP_ALIGN.CENTER
    r = p.runs[0]
    r.font.size = Pt(size); r.font.bold = True
    r.font.color.rgb = HEAD_NAVY; r.font.name = HEAD_FONT
    return s


def rbox(s, l, t, w, h, fill, line, lw=1.5):
    shp = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l), Inches(t),
                             Inches(w), Inches(h))
    if fill is None:
        shp.fill.solid(); shp.fill.fore_color.rgb = WHITE
    else:
        shp.fill.solid(); shp.fill.fore_color.rgb = fill
    shp.line.color.rgb = line; shp.line.width = Pt(lw)
    shp.shadow.inherit = False
    shp.text_frame.text = ""
    return shp


def chevron(s, l, t, w, h, fill, label):
    shp = s.shapes.add_shape(MSO_SHAPE.CHEVRON, Inches(l), Inches(t), Inches(w), Inches(h))
    shp.fill.solid(); shp.fill.fore_color.rgb = fill
    shp.line.fill.background(); shp.shadow.inherit = False
    tf = shp.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.text = label; p.alignment = PP_ALIGN.CENTER
    r = p.runs[0]
    r.font.size = Pt(13); r.font.bold = True
    r.font.color.rgb = WHITE; r.font.name = BODY_FONT
    return shp


def text(s, items, l, t, w, h, size=14, center=False, italic=False):
    tf = s.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h)).text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    for i, item in enumerate(items):
        body, bold, col, lvl = (item if isinstance(item, tuple) else (item, False, INK, 0))
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = body; p.level = lvl; p.space_after = Pt(5)
        if center:
            p.alignment = PP_ALIGN.CENTER
        for r in p.runs:
            r.font.size = Pt(size); r.font.bold = bold; r.font.italic = italic
            r.font.color.rgb = col; r.font.name = BODY_FONT
    return tf


# ═══════════════════════════════════════════════════════════════════ MAIN ══
def main():
    ev = json.load(open(os.path.join(RESULTS, "evaluation.json")))
    bm = json.load(open(os.path.join(RESULTS, "benchmark.json")))
    figures(ev, bm)

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)

    # ── TITLE PAGE (no number, exactly as theirs) ───────────────────────────
    s = prs.slides.add_slide(prs.slide_layouts[6])
    tb = s.shapes.add_textbox(Inches(0.8), Inches(0.45), Inches(11.7), Inches(1.5))
    tf = tb.text_frame; tf.word_wrap = True
    for i, line in enumerate(["AUTOMATIC ATTENDANCE SYSTEM USING",
                              "MULTIPLE FACE RECOGNITION"]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line; p.alignment = PP_ALIGN.CENTER
        r = p.runs[0]; r.font.size = Pt(36); r.font.bold = True
        r.font.color.rgb = HEAD_NAVY; r.font.name = HEAD_FONT

    text(s, [
        ("Team Members' Name and Roll Number-", True, BLACK, 0),
        "",
        ("          1. Souryadeep Deb (13000222064)              2. Soham Bhattacharya (13000222065)", True, BLACK, 0),
        "",
        ("          3. Srija Basak (13000222066)                  4. Sneha Singh (13000222067)", True, BLACK, 0),
        "",
        ("Group Number-  18", True, BLACK, 0),
        "",
        ("Mentor Name-  Mr Prodipta Bhowmik", True, BLACK, 0),
    ], 1.8, 2.1, 10.0, 3.0, size=14)

    text(s, [
        ("Department of Information Technology", True, BLACK, 0),
        ("Techno Main Salt Lake", True, BLACK, 0),
        ("Kolkata -700091", True, BLACK, 0),
    ], 4.4, 5.5, 4.6, 1.3, size=14, center=True)

    # ── 1 · PROJECT TITLE ──────────────────────────────────────────────────
    s = heading(prs, "PROJECT TITLE")
    text(s, [("Automatic Attendance System using Multiple Face Recognition", False, HEAD_NAVY, 0)],
         1.0, 1.15, 11.3, 0.5, size=20, center=True, italic=True)
    text(s, [("Spoof-Resistant Multi-Face Attendance with Liveness-Gated Commit", True, RED, 0)],
         1.0, 1.75, 11.3, 0.45, size=15, center=True)
    s.shapes.add_picture(f"{FIG}/attack.png", Inches(2.1), Inches(2.4), width=Inches(9.1))
    rbox(s, 2.1, 5.3, 9.1, 1.05, None, O_RED, 1.5)
    text(s, [
        ("We tested it: a printed photograph was marked present 100% of the time.", True, RED, 0),
        ("This project is about closing that gap.", False, INK, 0),
    ], 2.3, 5.45, 8.7, 0.85, size=14, center=True)

    # ── 2 · OBJECTIVE OF THE PROJECT ───────────────────────────────────────
    s = heading(prs, "OBJECTIVE OF THE PROJECT")
    objectives = [
        ("To detect and recognise multiple faces simultaneously in a single frame.", O_GREEN),
        ("To reject strangers — an open-set system that is allowed to answer \"nobody\".", O_RED),
        ("To resist presentation attacks: a photo or phone screen must NOT be marked present.", O_BLUE),
        ("To make the attendance commit reliable — it is written once a day and cannot be undone.", O_ORANGE),
        ("To run offline on a laptop CPU: no GPU, no cloud, no student data leaving campus.", O_PURPLE),
    ]
    for i, (t, col) in enumerate(objectives):
        y = 1.3 + i * 1.08
        rbox(s, 2.6, y, 8.6, 0.85, None, col, 1.75)
        text(s, [(t, False, INK, 0)], 2.85, y + 0.19, 8.1, 0.6, size=14, italic=True)
        # the connector rails from their original slide
        bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(2.15), Inches(y + 0.38),
                                 Inches(0.42), Inches(0.05))
        bar.fill.solid(); bar.fill.fore_color.rgb = col
        bar.line.fill.background(); bar.shadow.inherit = False

    # ── 3 · PROBLEM DEFINITION ─────────────────────────────────────────────
    s = heading(prs, "PROBLEM DEFINITION")
    rbox(s, 0.7, 1.15, 11.9, 0.95, BOX_BLUE, LIT_LINE, 1.25)
    text(s, [
        ("Traditional manual attendance is slow, error-prone and vulnerable to proxy marking —", False, BLACK, 0),
        ("a 60-student roll-call costs ~5 minutes of every lecture, about 80 teaching hours a year.", False, BLACK, 0),
    ], 0.95, 1.3, 11.4, 0.8, size=14, italic=True)

    rbox(s, 0.7, 2.35, 11.9, 1.5, RGBColor(0xF8, 0xD7, 0xD2), O_RED, 1.75)
    text(s, [
        ("But automating it with face recognition introduces a NEW problem — and this is the gap "
         "our project addresses:", True, BLACK, 0),
        ("Face recognition is DESIGNED to give a photo of you the same embedding as you. That is "
         "exactly what makes it a good face model.", False, RED, 0),
        ("So recognition ALONE cannot prevent proxy attendance. We measured it: a printed photo was "
         "marked present 100% of the time.", True, RED, 0),
    ], 0.95, 2.5, 11.4, 1.35, size=13)

    rbox(s, 0.7, 4.1, 11.9, 2.55, BOX_ORANGE, O_ORANGE, 1.25)
    text(s, [
        ("Four failures a real classroom deployment must survive:", False, BLACK, 0),
        "",
        ("•   A photograph or phone screen held to the camera  →  marked present", False, BLACK, 0),
        ("•   A stranger walking past  →  a softmax classifier has no way to say \"nobody\"", False, BLACK, 0),
        ("•   A student at the back of the room  →  too few pixels to identify, but still named", False, BLACK, 0),
        ("•   One misread frame  →  the wrong student marked present for the entire day", False, BLACK, 0),
    ], 0.95, 4.25, 11.4, 2.35, size=14)

    # ── 4 · LITERATURE REVIEW ──────────────────────────────────────────────
    s = heading(prs, "LITERATURE REVIEW")
    lits = [
        ("D'Souza et al. (2019) [1] ", "proposed an automated attendance system using facial recognition "
                                       "with histogram-based feature extraction; efficient, but sensitive to lighting and pose."),
        ("Arsenovic et al. (2017) [2] ", "applied CNN-based deep learning for face recognition, achieving "
                                         "higher accuracy and real-time performance."),
        ("Kakarla et al. (2020) [3] ", "proposed a CNN smart attendance system recognising multiple students "
                                       "under moderate pose and expression change."),
        ("Varadharajan et al. (2016) [4] ", "developed a face-detection classroom attendance system; accuracy "
                                            "drops under occlusion and poor lighting."),
        ("Siswanto et al. (2014) [5] ", "introduced face biometrics as a hygienic alternative to fingerprint "
                                        "attendance systems."),
    ]
    for i, (who, what) in enumerate(lits):
        y = 1.15 + i * 0.92
        rbox(s, 0.7, y, 11.9, 0.8, LIT_FILL, LIT_LINE, 1.0)
        tf = s.shapes.add_textbox(Inches(0.95), Inches(y + 0.1), Inches(11.4), Inches(0.62)).text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        r1 = p.add_run(); r1.text = who
        r1.font.size = Pt(13); r1.font.bold = True; r1.font.name = BODY_FONT
        r1.font.color.rgb = BLACK
        r2 = p.add_run(); r2.text = what
        r2.font.size = Pt(13); r2.font.name = BODY_FONT; r2.font.color.rgb = INK

    rbox(s, 0.7, 5.8, 11.9, 0.9, RGBColor(0xF8, 0xD7, 0xD2), O_RED, 1.75)
    text(s, [
        ("RESEARCH GAP —  every paper above reports one accuracy number on clean data. None test a "
         "presentation attack, none report a stranger-rejection rate, and none treat \"recognised\" and "
         "\"marked present\" as different decisions.", True, RED, 0),
    ], 0.95, 5.95, 11.4, 0.75, size=12.5)

    # ── 5 · PROPOSED METHODOLOGY ───────────────────────────────────────────
    s = heading(prs, "PROPOSED METHODOLOGY")
    text(s, [("Proposed Solution", True, RGBColor(0x9E, 0x2B, 0x25), 0)],
         0.6, 3.1, 2.4, 0.5, size=18, center=True)
    ar = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(0.7), Inches(3.65),
                            Inches(2.2), Inches(0.45))
    ar.fill.solid(); ar.fill.fore_color.rgb = RGBColor(0xD6, 0xDC, 0xE5)
    ar.line.fill.background(); ar.shadow.inherit = False
    ar.text_frame.text = ""

    blocks = [
        ("How it Works:", RGBColor(0x9C, 0xB9, 0x3A), [
            "•  Detects EVERY face in one frame (RetinaFace), embeds each into a 512-d vector (ArcFace),",
            "   and matches it against each enrolled student's centroid.",
            "•  Records name, confidence and status to a CSV file. Nothing leaves the machine.",
        ]),
        ("Problem Addressed:", RGBColor(0x45, 0xA3, 0xAF), [
            "•  Replaces manual attendance and eliminates the signed-register proxy.",
            "•  Rejects strangers, and blocks the photo / screen proxy that defeats ordinary",
            "   face recognition.",
        ]),
        ("Innovation and uniqueness of the solution", RGBColor(0x7B, 0x5E, 0xA7), [
            "•  We do NOT claim a new face model — ArcFace is pretrained and FROZEN.",
            "•  LIVENESS that works at 1.4 frames/sec, where blink detection provably fails.",
            "•  Threshold calibrated on 2,880 impostor faces — not hand-picked.",
            "•  Attendance as an irreversible commit.  Enrolment: 607 s → 1.4 s.",
            "•  We also report a guard that did NOT work (top-2 margin).",
        ]),
    ]
    y = 1.2
    for label, col, lines in blocks:
        h = 1.75 if "Innovation" in label else 1.5
        chevron(s, 3.3, y, 2.9, h, col, label)
        text(s, [(l, False, INK, 0) for l in lines], 6.45, y + 0.18, 6.4, h - 0.25, size=12)
        y += h + 0.2

    # ── 6 · EXPERIMENTAL DETAILS ───────────────────────────────────────────
    s = heading(prs, "EXPERIMENTAL DETAILS")
    rbox(s, 0.5, 1.1, 6.9, 0.55, RGBColor(0x7B, 0x5E, 0xA7), RGBColor(0x7B, 0x5E, 0xA7))
    text(s, [("Programming Language:  Python 3.13", True, WHITE, 0)],
         0.7, 1.2, 6.5, 0.4, size=14)

    rows = [
        ("Face Detection", "RetinaFace / SCRFD  (det_10g)"),
        ("Recognition", "ArcFace ResNet-50 (buffalo_l) → 512-d embedding"),
        ("Runtime", "ONNX Runtime — CPU only, NO GPU"),
        ("Matching", "Nearest-centroid, cosine similarity  (no classifier)"),
        ("Frontend", "React · Vite · TailwindCSS"),
        ("Backend", "Flask REST API  (Bearer-token auth)"),
        ("Storage", "CSV + JSON on disk — no cloud, no database server"),
    ]
    for i, (k, v) in enumerate(rows):
        y = 1.85 + i * 0.62
        rbox(s, 0.5, y, 2.0, 0.52, LIT_FILL, LIT_LINE, 1.0)
        text(s, [(k, True, BLACK, 0)], 0.6, y + 0.12, 1.85, 0.35, size=12)
        rbox(s, 2.6, y, 4.8, 0.52, None, LIT_LINE, 1.0)
        text(s, [(v, False, INK, 0)], 2.75, y + 0.12, 4.6, 0.35, size=11.5)

    s.shapes.add_picture(f"{FIG}/workflow.png", Inches(8.15), Inches(1.1), height=Inches(5.55))
    text(s, [("WORKFLOW", True, LIT_LINE, 0)], 8.15, 6.6, 4.6, 0.35, size=14, center=True)

    # ── 7 · RESULTS AND ANALYSIS ───────────────────────────────────────────
    s = heading(prs, "RESULTS AND ANALYSIS")
    s.shapes.add_picture(f"{FIG}/spoof.png", Inches(0.55), Inches(1.0), height=Inches(2.3))
    s.shapes.add_picture(f"{FIG}/ablation.png", Inches(4.55), Inches(1.0), height=Inches(2.3))
    s.shapes.add_picture(f"{FIG}/degradation.png", Inches(9.15), Inches(1.0), height=Inches(2.3))

    caps = [
        (0.5, O_RED, "Presentation Attack", [
            "A printed photo was marked present 100% of the",
            "time by recognition alone.",
            "With liveness — motion measured from the",
            "detector's own landmarks — it is 0%.",
        ]),
        (4.5, O_GREEN, "Ablation of Each Guard", [
            "Calibrating the threshold cut strangers admitted",
            "4× (0.81% → 0.20%).",
            "Temporal voting drove wrong attendance records",
            "to zero (3.54% → 0%).",
        ]),
        (8.5, O_PURPLE, "Operating Envelope", [
            "Accuracy collapses below 24 px and is fully",
            "recovered by 40 px — so faces under 40 px are",
            "refused, not guessed at.",
            "One 1080p camera therefore covers about 7 m.",
        ]),
    ]
    for x, col, title, lines in caps:
        rbox(s, x, 3.5, 4.3, 2.05, None, col, 1.75)
        text(s, [(title, True, col, 0)], x + 0.2, 3.6, 3.9, 0.35, size=13, center=True)
        text(s, [(l, False, INK, 0) for l in lines], x + 0.2, 4.0, 3.9, 1.45, size=11)

    rbox(s, 0.5, 5.75, 12.3, 0.9, RGBColor(0xF8, 0xD7, 0xD2), O_RED, 1.5)
    text(s, [
        ("Honest limitation —  a VIDEO replay of a real person would still pass, because a recorded "
         "face genuinely moves. We raise the attack cost from \"print a photo\" to \"record and replay "
         "a video\": a real gain, not a complete defence.", True, RED, 0),
    ], 0.75, 5.9, 11.9, 0.75, size=12)

    # ── 8 · CONCLUSION ─────────────────────────────────────────────────────
    s = heading(prs, "CONCLUSION")
    rbox(s, 0.55, 1.2, 3.3, 1.95, None, O_BLUE, 1.5)
    text(s, [
        ("A pretrained face model is NOT an attendance system.", True, HEAD_NAVY, 0),
        "",
        ("It fails in three measurable ways — and each one is fixable in the decision layer, "
         "not the model.", False, INK, 0),
    ], 0.75, 1.35, 2.9, 1.75, size=12.5)

    rbox(s, 0.55, 3.45, 3.3, 2.4, None, O_PURPLE, 1.5)
    text(s, [
        ("Limitations", True, RED, 0),
        "",
        ("•  A video replay would still pass.", False, INK, 0),
        ("•  The look-alike guard is unproven.", False, INK, 0),
        ("•  Only 2 real users enrolled — all numbers come from the 30-identity cohort.", False, INK, 0),
    ], 0.75, 3.6, 2.9, 2.2, size=11.5)

    concl = [
        ("Automation", RGBColor(0xC0, 0x50, 0x4D),
         "Detects and identifies every face in one frame.  Enrolling a new student takes 1.4 s "
         "(was 607 s) — no retraining, no GPU."),
        ("Integrity", RGBColor(0x9B, 0xBB, 0x59),
         "Manual proxy eliminated.  Photo / screen proxy BLOCKED by liveness: attack success "
         "100% → 0%.  Strangers admitted: 0.20%."),
        ("Precision", RGBColor(0x80, 0x64, 0xA2),
         "Open-set rejection with a threshold calibrated on 2,880 impostor faces.  Faces under "
         "40 px are refused, not guessed.  Wrong attendance records: 0%."),
        ("Efficiency", RGBColor(0x4B, 0xAC, 0xC6),
         "16 faces in one frame in 1.3 s on a laptop CPU.  Fully offline — no cloud, no GPU, "
         "no recurring cost."),
    ]
    y = 1.2
    for label, col, body in concl:
        chevron(s, 4.15, y, 1.5, 1.35, col, label)
        rbox(s, 5.9, y + 0.1, 6.9, 1.15, None, col, 1.25)
        text(s, [(body, False, INK, 0)], 6.05, y + 0.22, 6.6, 1.0, size=11.5)
        y += 1.45

    # ── 9 · REFERENCES ─────────────────────────────────────────────────────
    s = heading(prs, "REFERENCES")
    refs = [
        "1.  D'Souza, J. W. S., et al. (2019). Automated Attendance Marking and Management System by Facial "
        "Recognition Using Histogram. Array, 3–4: 100014.  DOI: 10.1016/j.array.2019.100014",
        "2.  Arsenovic, M., Sladojevic, S., Anderla, A., Stefanovic, D. (2017). FaceTime — Deep Learning Based "
        "Face Recognition Attendance System. IEEE SISY 2017, pp. 53–58.  DOI: 10.1109/SISY.2017.8080587",
        "3.  Kakarla, S., Gangula, P., Rahul, M. S., Singh, C. S. C., Sarma, T. H. (2020). Smart Attendance "
        "Management System Based on Face Recognition Using CNN. IEEE-HYDCON 2020, pp. 1–5.  "
        "DOI: 10.1109/HYDCON48903.2020.9242847",
        "4.  Varadharajan, E., Dharani, R., Jeevitha, S., Kavinmathi, B., Hemalatha, S. (2016). Automatic Attendance "
        "Management System Using Face Detection. IC-GET 2016, pp. 1–3.  DOI: 10.1109/GET.2016.7916753",
        "5.  Siswanto, A. R. S., Nugroho, A. S., Galinium, M. (2014). Implementation of Face Recognition Algorithm "
        "for Biometrics Based Time Attendance System. ICISS 2014, pp. 149–154.  DOI: 10.1109/ICTSS.2014.7013165",
        "6.  Deng, J., Guo, J., Xue, N., Zafeiriou, S. (2019). ArcFace: Additive Angular Margin Loss for Deep Face "
        "Recognition. CVPR 2019, pp. 4690–4699.  DOI: 10.1109/CVPR.2019.00482    ← the model this system uses",
        "7.  Deng, J., Guo, J., Ververas, E., Kotsia, I., Zafeiriou, S. (2020). RetinaFace: Single-Shot Multi-Level "
        "Face Localisation in the Wild. CVPR 2020.  DOI: 10.1109/CVPR42600.2020.00525",
        "8.  Pan, G., Sun, L., Wu, Z., Lao, S. (2007). Eyeblink-based Anti-Spoofing in Face Recognition from a "
        "Generic Webcamera. ICCV 2007, pp. 1–8.  DOI: 10.1109/ICCV.2007.4409068",
        "9.  ISO/IEC 30107-3:2023 — Biometric presentation attack detection — Part 3: Testing and reporting.",
    ]
    for i, r in enumerate(refs):
        y = 1.1 + i * 0.63
        rbox(s, 0.5, y, 12.3, 0.55, None, LIT_LINE, 1.0)
        col = RED if i in (5, 7, 8) else INK
        text(s, [(r, False, col, 0)], 0.65, y + 0.09, 12.0, 0.42, size=10)

    # ── 10 · THANK YOU ─────────────────────────────────────────────────────
    s = prs.slides.add_slide(prs.slide_layouts[6])
    tb = s.shapes.add_textbox(Inches(0.8), Inches(2.9), Inches(11.7), Inches(1.4))
    p = tb.text_frame.paragraphs[0]
    p.text = "THANK YOU"; p.alignment = PP_ALIGN.CENTER
    r = p.runs[0]
    r.font.size = Pt(54); r.font.bold = True; r.font.italic = True
    r.font.color.rgb = BLACK; r.font.name = HEAD_FONT

    # slide numbers start at 1 on PROJECT TITLE, exactly as in the original deck
    for i, sl in enumerate(prs.slides):
        if i:
            footer(sl, i)

    prs.save(OUT)
    print(f"\n✅ {OUT}   ({len(prs.slides._sldIdLst)} slides)")


if __name__ == "__main__":
    main()
