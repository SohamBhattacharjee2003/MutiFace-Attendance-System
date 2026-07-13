import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowLeft, Users, UserCheck, CheckCircle2, XCircle, Clock, Copy, Check,
  Link2, CalendarDays, ClipboardList, UserPlus, Trash2, TrendingDown,
} from "lucide-react";
import { Card, CardTitle, Button, Badge, Empty } from "../components/ui";
import {
  getClass, addToRoster, removeFromRoster, getClassAttendance, getClassHistory,
} from "../utils/api";

const TABS = [
  { id: "today", label: "Today's register", icon: ClipboardList },
  { id: "history", label: "Attendance history", icon: CalendarDays },
  { id: "roster", label: "Roster", icon: Users },
];

export default function ClassDetail() {
  const { id } = useParams();
  const [cls, setCls] = useState(null);
  const [tab, setTab] = useState("today");
  const [today, setToday] = useState(null);
  const [hist, setHist] = useState(null);
  const [copied, setCopied] = useState(false);

  const load = () => {
    getClass(id).then(setCls).catch(console.error);
    getClassAttendance(id).then(setToday).catch(console.error);
    getClassHistory(id).then(setHist).catch(console.error);
  };
  useEffect(() => { load(); const t = setInterval(load, 5000); return () => clearInterval(t); }, [id]);

  if (!cls) return <div className="min-h-screen pt-24 text-center text-sm text-[--muted]">Loading…</div>;

  const link = `${window.location.origin}/enroll/${cls.code}`;
  const copy = () => {
    navigator.clipboard.writeText(link);
    setCopied(true); setTimeout(() => setCopied(false), 1600);
  };

  return (
    <div className="min-h-screen w-full mx-auto max-w-6xl px-5 sm:px-8 pt-24 pb-16">
      <Link to="/classes" className="mb-5 inline-flex items-center gap-2 text-sm text-[--muted] hover:text-white">
        <ArrowLeft className="h-4 w-4" /> All classes
      </Link>

      {/* header */}
      <Card pad="p-5" className="mb-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="display-lg text-white">{cls.name}</h1>
            <div className="mt-2 flex flex-wrap gap-2">
              <Badge tone="muted"><Users className="h-3 w-3" />{cls.total} on roster</Badge>
              <Badge tone="good"><UserCheck className="h-3 w-3" />{cls.enrolled} enrolled</Badge>
              {cls.pending > 0 && <Badge tone="warn"><Clock className="h-3 w-3" />{cls.pending} pending</Badge>}
            </div>
          </div>

          <div className="flex items-center gap-2 rounded-lg border border-white/10 bg-black/25 p-2">
            <Link2 className="h-3.5 w-3.5 text-[--brand]" />
            <code className="max-w-[240px] truncate font-mono text-[11px] text-slate-400">{link}</code>
            <Button size="sm" variant="ghost" onClick={copy}>
              {copied ? <><Check className="h-3 w-3 text-emerald-400" />Copied</> : <><Copy className="h-3 w-3" />Share link</>}
            </Button>
          </div>
        </div>
      </Card>

      {/* tabs */}
      <div className="mb-4 flex flex-wrap gap-1.5">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`inline-flex items-center gap-2 rounded-lg border px-3.5 py-2 text-sm font-medium transition
              ${tab === t.id
                ? "border-[--brand] bg-[--brand]/15 text-white"
                : "border-white/10 bg-white/[0.03] text-[--muted] hover:border-white/25 hover:text-white"}`}
          >
            <t.icon className="h-4 w-4" /> {t.label}
          </button>
        ))}
      </div>

      {tab === "today" && <Today report={today} />}
      {tab === "history" && <History hist={hist} />}
      {tab === "roster" && <Roster cls={cls} onChange={load} />}
    </div>
  );
}

/* ══════════════════════════ TODAY'S REGISTER ══════════════════════════ */
function Today({ report }) {
  if (!report) return null;
  const { present, absent, not_enrolled, total, percent, rows, date } = report;

  const tone = {
    present: ["good", CheckCircle2, "Present"],
    absent: ["bad", XCircle, "Absent"],
    "not-enrolled": ["muted", Clock, "Not enrolled"],
  };

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_2fr] lg:items-start">
      <Card pad="p-5">
        <CardTitle>{date}</CardTitle>

        {/* the one number the teacher wants */}
        <div className="mb-5 text-center">
          <div className="relative mx-auto h-28 w-28">
            <svg viewBox="0 0 100 100" className="h-full w-full -rotate-90">
              <circle cx="50" cy="50" r="42" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="9" />
              <motion.circle
                cx="50" cy="50" r="42" fill="none" stroke="url(#g)" strokeWidth="9" strokeLinecap="round"
                strokeDasharray={264}
                initial={{ strokeDashoffset: 264 }}
                animate={{ strokeDashoffset: 264 - (264 * percent) / 100 }}
                transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
              />
              <defs>
                <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stopColor="#4f8bff" />
                  <stop offset="100%" stopColor="#10b981" />
                </linearGradient>
              </defs>
            </svg>
            <div className="absolute inset-0 grid place-items-center">
              <div>
                <div className="text-2xl font-bold tabular-nums text-white">{percent}%</div>
                <div className="text-[10px] uppercase tracking-wide text-slate-600">present</div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-2 text-center">
          {[["Present", present, "text-emerald-300"],
            ["Absent", absent, "text-rose-300"],
            ["Not enrolled", not_enrolled, "text-slate-500"]].map(([k, v, c]) => (
            <div key={k} className="rounded-lg border border-white/10 bg-black/20 p-2.5">
              <div className={`text-lg font-bold tabular-nums ${c}`}>{v}</div>
              <div className="text-[10px] uppercase tracking-wide text-slate-600">{k}</div>
            </div>
          ))}
        </div>
        <p className="mt-4 text-[11px] leading-relaxed text-slate-600">
          Updates live as students are recognised on the Live page. A student is marked
          present once — the first time three frames agree.
        </p>
      </Card>

      <Card pad="p-0">
        <div className="scroll-x max-h-[560px] overflow-y-auto">
          <table className="w-full min-w-[520px] text-left text-sm">
            <thead className="sticky top-0 z-10 border-b border-white/10 bg-[--bg-1]/95 backdrop-blur">
              <tr className="text-[11px] uppercase tracking-wide text-slate-500">
                <th className="px-4 py-3 font-medium">Roll</th>
                <th className="px-4 py-3 font-medium">Name</th>
                <th className="px-4 py-3 font-medium">Time</th>
                <th className="px-4 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => {
                const [t, Icon, label] = tone[r.status];
                return (
                  <tr key={r.roll} className="border-b border-white/[0.06] transition hover:bg-white/[0.03]">
                    <td className="px-4 py-2.5 font-mono text-xs text-slate-400">{r.roll}</td>
                    <td className="px-4 py-2.5 font-medium text-white">{r.name}</td>
                    <td className="px-4 py-2.5 font-mono text-xs tabular-nums text-slate-500">
                      {r.time ? r.time.slice(11, 19) : "—"}
                    </td>
                    <td className="px-4 py-2.5">
                      <Badge tone={t}><Icon className="h-3 w-3" />{label}</Badge>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

/* ══════════════════════════ ATTENDANCE HISTORY ══════════════════════════
 * A list of daily totals tells a teacher nothing about WHO keeps missing class.
 * This is a student × day grid: one row per student, one square per day. A pattern of
 * absence is visible at a glance, and the worst attendance floats to the top.
 */
function History({ hist }) {
  if (!hist) return null;
  if (!hist.days_held) {
    return (
      <Card pad="p-6">
        <Empty icon={CalendarDays} title="No classes held yet"
               sub="Run Live attendance once and the history grid will start filling in." />
      </Card>
    );
  }

  const { students, dates, days_held, average, daily } = hist;
  const pct = (p) => (p >= 75 ? "text-emerald-300" : p >= 50 ? "text-amber-300" : "text-rose-300");

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-3">
        {[
          ["Classes held", days_held, "text-slate-200"],
          ["Average present", average, "text-sky-300"],
          ["Below 75%", students.filter((s) => s.percent < 75 && s.enrolled).length, "text-rose-300"],
        ].map(([k, v, c]) => (
          <Card key={k} pad="p-4">
            <div className={`text-xl font-bold tabular-nums ${c}`}>{v}</div>
            <div className="mt-1 text-xs text-[--muted]">{k}</div>
          </Card>
        ))}
      </div>

      <Card pad="p-5">
        <CardTitle right={
          <div className="flex items-center gap-3 text-[10px] text-slate-500">
            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-sm bg-emerald-500/80" /> present
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-sm bg-white/10" /> absent
            </span>
          </div>
        }>
          Attendance grid — worst first
        </CardTitle>

        <div className="scroll-x">
          <table className="w-full min-w-[640px]">
            <thead>
              <tr>
                <th className="pb-2 text-left text-[10px] uppercase tracking-wide text-slate-600">Student</th>
                {dates.map((d) => (
                  <th key={d} className="pb-2 text-center text-[9px] font-medium text-slate-600" title={d}>
                    {d.slice(8)}
                  </th>
                ))}
                <th className="pb-2 pl-3 text-right text-[10px] uppercase tracking-wide text-slate-600">%</th>
              </tr>
            </thead>
            <tbody>
              {students.map((s, i) => (
                <tr key={s.roll} className="group">
                  <td className="py-1 pr-3">
                    <div className="flex items-center gap-2">
                      {s.enrolled && s.percent < 75 && (
                        <TrendingDown className="h-3 w-3 shrink-0 text-rose-400" />
                      )}
                      <span className="truncate text-xs font-medium text-slate-300">{s.name}</span>
                      <span className="font-mono text-[10px] text-slate-600">{s.roll}</span>
                    </div>
                  </td>
                  {s.marks.map((m) => (
                    <td key={m.date} className="px-0.5 py-1">
                      <motion.div
                        initial={{ scale: 0 }} animate={{ scale: 1 }}
                        transition={{ delay: i * 0.015 }}
                        title={`${m.date} — ${m.present ? "present" : "absent"}`}
                        className={`mx-auto h-5 w-5 rounded-[4px] ${
                          m.present
                            ? "bg-emerald-500/80 shadow-[0_0_8px_rgba(16,185,129,0.35)]"
                            : "border border-white/10 bg-white/[0.04]"
                        }`}
                      />
                    </td>
                  ))}
                  <td className={`py-1 pl-3 text-right font-mono text-xs font-bold tabular-nums ${pct(s.percent)}`}>
                    {s.percent}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="mt-4 text-[11px] leading-relaxed text-slate-600">
          Sorted by attendance, lowest first — the students who need chasing are always at
          the top, instead of buried across thirty separate daily reports.
        </p>
      </Card>
    </div>
  );
}

/* ══════════════════════════ ROSTER ══════════════════════════ */
function Roster({ cls, onChange }) {
  const [bulk, setBulk] = useState("");
  const [busy, setBusy] = useState(false);

  /* Accepts pasted lines: "13000222065, Soham Bhattacharya" or tab/space separated.
     Teachers have this list in a spreadsheet already — typing 60 students one at a
     time is how a feature goes unused. */
  const parse = (text) =>
    text.split("\n").map((l) => l.trim()).filter(Boolean).map((line) => {
      const m = line.match(/^(\S+)[,\t ]+(.+)$/);
      return m ? { roll: m[1].trim(), name: m[2].trim() } : null;
    }).filter(Boolean);

  const parsed = parse(bulk);

  const add = async () => {
    if (!parsed.length) return;
    setBusy(true);
    try { await addToRoster(cls.id, parsed); setBulk(""); onChange(); }
    catch (e) { alert(e.message); }
    setBusy(false);
  };

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_1.4fr] lg:items-start">
      <Card pad="p-5">
        <CardTitle>Add students</CardTitle>
        <p className="mb-3 text-xs leading-relaxed text-[--muted]">
          Paste one student per line — <span className="font-mono text-slate-400">roll, name</span>.
          Straight from your spreadsheet.
        </p>
        <textarea
          value={bulk}
          onChange={(e) => setBulk(e.target.value)}
          rows={8}
          placeholder={"13000222064, Souryadeep Deb\n13000222065, Soham Bhattacharya\n13000222066, Srija Basak"}
          className="w-full rounded-lg border border-white/12 bg-black/25 p-3 font-mono text-xs
                     text-white placeholder:text-slate-600 focus:border-[--brand] focus:outline-none"
        />
        <div className="mt-3 flex items-center justify-between">
          <span className="text-[11px] text-slate-600">
            {parsed.length ? `${parsed.length} students detected` : "nothing detected yet"}
          </span>
          <Button size="sm" onClick={add} disabled={busy || !parsed.length}>
            <UserPlus className="h-3.5 w-3.5" /> Add {parsed.length || ""}
          </Button>
        </div>
        <p className="mt-4 text-[11px] leading-relaxed text-slate-600">
          The roster is the security gate. Only these roll numbers can enrol through the
          shared link — anyone else who opens it has no roll number to claim.
        </p>
      </Card>

      <Card pad="p-0">
        <div className="scroll-x max-h-[520px] overflow-y-auto">
          <table className="w-full min-w-[420px] text-left text-sm">
            <thead className="sticky top-0 z-10 border-b border-white/10 bg-[--bg-1]/95 backdrop-blur">
              <tr className="text-[11px] uppercase tracking-wide text-slate-500">
                <th className="px-4 py-3 font-medium">Roll</th>
                <th className="px-4 py-3 font-medium">Name</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {cls.roster.length === 0 && (
                <tr><td colSpan="4" className="px-4 py-12 text-center text-xs text-slate-600">
                  No students yet — paste your list on the left.
                </td></tr>
              )}
              {cls.roster.map((s) => (
                <tr key={s.roll} className="border-b border-white/[0.06] hover:bg-white/[0.03]">
                  <td className="px-4 py-2.5 font-mono text-xs text-slate-400">{s.roll}</td>
                  <td className="px-4 py-2.5 font-medium text-white">{s.name}</td>
                  <td className="px-4 py-2.5">
                    {s.enrolled
                      ? <Badge tone="good"><UserCheck className="h-3 w-3" />{s.images} images</Badge>
                      : <Badge tone="warn"><Clock className="h-3 w-3" />Awaiting</Badge>}
                  </td>
                  <td className="px-4 py-2.5 text-right">
                    <button
                      onClick={async () => { await removeFromRoster(cls.id, s.roll); onChange(); }}
                      className="rounded-md border border-white/10 p-1 text-slate-600
                                 transition hover:border-rose-400/40 hover:text-rose-400"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
