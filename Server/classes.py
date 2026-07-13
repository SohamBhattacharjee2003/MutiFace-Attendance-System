"""
classes.py
Classes, rosters, and self-enrolment links.

The prototype only knew "students" — one flat list, enrolled by the teacher at the
teacher's laptop. A college needs three things that model cannot express:

  1. A teacher takes SEVERAL classes (IT-B 4th Year, CSE-A 3rd Year, ...), and a student
     in one is not a student in another. Attendance must be per class.
  2. Students should enrol THEMSELVES — the teacher cannot sit through 60 face captures.
  3. But an open enrolment link is a hole: attendance is exactly the thing people cheat.
     So the teacher publishes a ROSTER first (roll number + name), and the link only lets
     someone enrol if their roll number is already on it. A stranger holding the link has
     no roll number to claim.

Storage is JSON on disk, like the rest of the system — no database server, nothing leaves
the machine.

    data/classes.json     [{id, name, code, teacher, roster:[{roll,name,enrolled}], ...}]
    processed_dataset/<class_code>__<roll>/   the student's enrolment images
    logs/<class_code>/attendance_YYYY-MM-DD.csv
"""

import os
import csv
import json
import glob
import secrets
import threading
from datetime import datetime, timedelta


# ── Where state lives ────────────────────────────────────────────────────────
# Everything the system must NOT lose on a restart — enrolment images, the trained
# centroids, attendance CSVs, teacher accounts — lives under one root. In development
# that root is the current directory; in a container it is a MOUNTED VOLUME, so a redeploy
# or a crash does not wipe every enrolled student.
#
#     STATE_DIR=/data python api.py
STATE_DIR = os.getenv("STATE_DIR", ".")

DATA_DIR      = os.path.join(STATE_DIR, "data")
DATASET_DIR   = os.path.join(STATE_DIR, "processed_dataset")
LOGS_DIR      = os.path.join(STATE_DIR, "logs")
CLASSES_FILE = os.path.join(DATA_DIR, "classes.json")

_lock = threading.Lock()


# ── storage ──────────────────────────────────────────────────────────────────
def _load():
    if not os.path.exists(CLASSES_FILE):
        return []
    with open(CLASSES_FILE) as f:
        return json.load(f)


def _save(classes):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CLASSES_FILE, "w") as f:
        json.dump(classes, f, indent=2)


def clean_roll(roll):
    """
    Normalise a roll number to exactly what a student will type.

    The client parses pasted roster lines, and a greedy pattern once stored the roll as
    "13000222065," — comma included. The student then typed "13000222065", the strings did
    not match, and they were told they were not on the roster. The client is fixed, but a
    roll number is an identity key: normalise it here too, so no client can ever poison it
    again. Strips whitespace and any trailing/leading separators.
    """
    return str(roll).strip().strip(",;\t ").strip()


def student_key(class_code, roll):
    """
    The folder name / model label for one student.

    Namespaced by class, so roll 12 in IT-B and roll 12 in CSE-A are different people and
    can never be confused for one another by the recogniser.
    """
    return f"{class_code}__{clean_roll(roll)}"


def parse_key(key):
    """student_key() -> (class_code, roll), or (None, None) if it isn't one."""
    if "__" not in key:
        return None, None
    code, _, roll = key.partition("__")
    return code, roll


# ── classes ──────────────────────────────────────────────────────────────────
def create(teacher_email, name):
    """A class gets a short random code; that code IS the enrolment link."""
    with _lock:
        classes = _load()
        cls = {
            "id": secrets.token_hex(4),
            "code": secrets.token_urlsafe(6),      # goes in the shareable URL
            "name": name.strip(),
            "teacher": teacher_email,
            "roster": [],
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        classes.append(cls)
        _save(classes)
    return cls


def list_for(teacher_email):
    out = []
    for c in _load():
        if c["teacher"] != teacher_email:
            continue
        out.append({**c, **stats(c)})
    return sorted(out, key=lambda c: c["created"], reverse=True)


def get(class_id, teacher_email=None):
    for c in _load():
        if c["id"] == class_id and (teacher_email is None or c["teacher"] == teacher_email):
            return c
    return None


def get_by_code(code):
    """Public lookup — used by the student enrolment link. No auth."""
    for c in _load():
        if c["code"] == code:
            return c
    return None


def delete(class_id, teacher_email):
    with _lock:
        classes = _load()
        cls = next((c for c in classes if c["id"] == class_id
                    and c["teacher"] == teacher_email), None)
        if not cls:
            return False
        _save([c for c in classes if c["id"] != class_id])
    return True


# ── roster ───────────────────────────────────────────────────────────────────
def add_to_roster(class_id, teacher_email, entries):
    """
    entries: [{"roll": "13000222065", "name": "Soham Bhattacharya"}, ...]
    Re-adding an existing roll updates the name rather than duplicating the student.
    """
    with _lock:
        classes = _load()
        cls = next((c for c in classes if c["id"] == class_id
                    and c["teacher"] == teacher_email), None)
        if not cls:
            return None
        by_roll = {s["roll"]: s for s in cls["roster"]}
        for e in entries:
            roll = clean_roll(e.get("roll", ""))
            name = str(e.get("name", "")).strip()
            if not roll or not name:
                continue
            if roll in by_roll:
                by_roll[roll]["name"] = name
            else:
                by_roll[roll] = {"roll": roll, "name": name, "enrolled": False,
                                 "images": 0, "enrolled_at": None}
        cls["roster"] = sorted(by_roll.values(), key=lambda s: s["roll"])
        _save(classes)
    return cls


def remove_from_roster(class_id, teacher_email, roll):
    with _lock:
        classes = _load()
        cls = next((c for c in classes if c["id"] == class_id
                    and c["teacher"] == teacher_email), None)
        if not cls:
            return None
        cls["roster"] = [s for s in cls["roster"] if clean_roll(s["roll"]) != clean_roll(roll)]
        _save(classes)
    return cls


def mark_enrolled(class_code, roll, n_images):
    """Called after a student's self-enrolment succeeds."""
    with _lock:
        classes = _load()
        cls = next((c for c in classes if c["code"] == class_code), None)
        if not cls:
            return None
        roll = clean_roll(roll)
        for s in cls["roster"]:
            if s["roll"] == roll:
                s["enrolled"] = True
                s["images"] = n_images
                s["enrolled_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                break
        _save(classes)
    return cls


def on_roster(cls, roll):
    """The gate on the public link: is this roll number one the teacher published?"""
    roll = clean_roll(roll)
    return next((s for s in cls["roster"] if clean_roll(s["roll"]) == roll), None)


def stats(cls):
    total = len(cls["roster"])
    enrolled = sum(1 for s in cls["roster"] if s["enrolled"])
    return {"total": total, "enrolled": enrolled, "pending": total - enrolled}


# ── attendance, per class ────────────────────────────────────────────────────
def log_path(class_code, day=None):
    day = day or datetime.now().strftime("%Y-%m-%d")
    d = os.path.join(LOGS_DIR, class_code)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"attendance_{day}.csv")


def present_on(class_code, day):
    """{roll: {time, confidence}} for one class on one day."""
    path = log_path(class_code, day)
    if not os.path.exists(path):
        return {}
    out = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            _, roll = parse_key(row.get("StudentKey", ""))
            if roll:
                out[roll] = {"time": row.get("Timestamp"),
                             "confidence": row.get("Confidence")}
    return out


def day_report(cls, day=None):
    """Today's register: every student on the roster, marked present or absent."""
    day = day or datetime.now().strftime("%Y-%m-%d")
    present = present_on(cls["code"], day)
    rows = []
    for s in cls["roster"]:
        hit = present.get(s["roll"])
        rows.append({
            "roll": s["roll"],
            "name": s["name"],
            "enrolled": s["enrolled"],
            "status": "present" if hit else ("absent" if s["enrolled"] else "not-enrolled"),
            "time": hit["time"] if hit else None,
            "confidence": float(hit["confidence"]) if hit and hit["confidence"] else None,
        })
    n_present = sum(1 for r in rows if r["status"] == "present")
    return {
        "date": day,
        "class": {"id": cls["id"], "name": cls["name"], "code": cls["code"]},
        "present": n_present,
        "absent": sum(1 for r in rows if r["status"] == "absent"),
        "not_enrolled": sum(1 for r in rows if r["status"] == "not-enrolled"),
        "total": len(rows),
        "percent": round(100 * n_present / len(rows), 1) if rows else 0.0,
        "rows": sorted(rows, key=lambda r: r["roll"]),
    }


def history(cls, days=30):
    """
    A student × day grid — the shape a teacher actually wants.

    A list of daily totals tells you nothing about WHO keeps missing class. The grid
    does: one row per student, one column per day, so a pattern of absence is visible
    at a glance instead of buried in thirty separate reports.
    """
    today = datetime.now().date()
    dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days - 1, -1, -1)]

    # only keep days this class actually met (a log file exists)
    met = [d for d in dates if os.path.exists(log_path(cls["code"], d))]
    per_day = {d: present_on(cls["code"], d) for d in met}

    grid = []
    for s in cls["roster"]:
        marks = [{"date": d, "present": s["roll"] in per_day[d]} for d in met]
        attended = sum(1 for m in marks if m["present"])
        grid.append({
            "roll": s["roll"],
            "name": s["name"],
            "enrolled": s["enrolled"],
            "marks": marks,
            "attended": attended,
            "held": len(met),
            "percent": round(100 * attended / len(met), 1) if met else 0.0,
        })

    daily = [{"date": d, "present": len(per_day[d]), "total": len(cls["roster"])} for d in met]
    return {
        "class": {"id": cls["id"], "name": cls["name"]},
        "dates": met,
        "days_held": len(met),
        "students": sorted(grid, key=lambda g: g["percent"]),   # worst attendance first
        "daily": daily,
        "average": round(sum(d["present"] for d in daily) / max(len(daily), 1), 1),
    }
