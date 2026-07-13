import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ResponsiveContainer, BarChart, Bar, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Cell,
} from "recharts";
import {
  GraduationCap, Users, CheckCircle2, Clock, Plus, ArrowRight,
  Link2, Camera, TrendingUp,
} from "lucide-react";
import { Card, CardTitle, Button, Badge, Empty, Stat, stagger, riseIn } from "../components/ui";
import { getClasses, getClassAttendance, getClassHistory } from "../utils/api";

/**
 * The dashboard is per-teacher and per-class.
 *
 * A teacher with no classes now sees an empty state and the three steps to get started —
 * not somebody else's leftover demo students, which is what the flat pre-class version
 * showed. Everything here is derived from that teacher's own classes.
 */
export default function Dashboard() {
  const [classes, setClasses] = useState(null);
  const [today, setToday] = useState({});
  const [hist, setHist] = useState({});

  const load = async () => {
    try {
      const cs = await getClasses();
      setClasses(cs);
      const t = {}, h = {};
      await Promise.all(cs.map(async (c) => {
        t[c.id] = await getClassAttendance(c.id).catch(() => null);
        h[c.id] = await getClassHistory(c.id, 14).catch(() => null);
      }));
      setToday(t); setHist(h);
    } catch (e) { console.error(e); }
  };

  useEffect(() => { load(); const i = setInterval(load, 8000); return () => clearInterval(i); }, []);

  if (!classes) {
    return <div className="min-h-screen pt-24 text-center text-sm text-[--muted]">Loading…</div>;
  }
  if (classes.length === 0) return <FirstRun />;

  const totals = classes.reduce((a, c) => ({
    students: a.students + c.total,
    enrolled: a.enrolled + c.enrolled,
    pending: a.pending + c.pending,
  }), { students: 0, enrolled: 0, pending: 0 });

  const presentToday = classes.reduce((a, c) => a + (today[c.id]?.present ?? 0), 0);

  const byClass = classes.map((c) => ({
    name: c.name.length > 14 ? c.name.slice(0, 13) + "…" : c.name,
    percent: today[c.id]?.percent ?? 0,
    present: today[c.id]?.present ?? 0,
  }));

  // one trend line, merged across every class the teacher takes
  const merged = {};
  classes.forEach((c) => (hist[c.id]?.daily ?? []).forEach((d) => {
    merged[d.date] = merged[d.date] || { date: d.date, present: 0, total: 0 };
    merged[d.date].present += d.present;
    merged[d.date].total += d.total;
  }));
  const trend = Object.values(merged)
    .sort((a, b) => a.date.localeCompare(b.date))
    .map((d) => ({ day: d.date.slice(5), percent: d.total ? Math.round(100 * d.present / d.total) : 0 }));

  const axis = { stroke: "#64748b", fontSize: 11 };
  const tip = { contentStyle: {
    background: "rgba(10,15,36,0.96)", border: "1px solid rgba(255,255,255,0.12)",
    borderRadius: 10, color: "#e2e8f0", fontSize: 12 } };
  const tone = (p) => (p >= 75 ? "#10b981" : p >= 50 ? "#f59e0b" : "#ef4444");

  return (
    <div className="min-h-screen w-full mx-auto max-w-6xl px-4 pt-24 pb-16 sm:px-6 lg:px-8">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="display-lg text-white">Dashboard</h1>
          <p className="mt-1.5 text-sm text-[--muted]">
            Across {classes.length} {classes.length === 1 ? "class" : "classes"} · live
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button as={Link} to="/live" size="sm"><Camera className="h-4 w-4" />Take attendance</Button>
          <Button as={Link} to="/classes" variant="ghost" size="sm">
            <GraduationCap className="h-4 w-4" />Classes
          </Button>
        </div>
      </div>

      <motion.div variants={stagger} initial="hidden" animate="show"
                  className="mb-4 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <motion.div variants={riseIn}>
          <Stat icon={GraduationCap} label="Classes" value={classes.length} tone="brand" />
        </motion.div>
        <motion.div variants={riseIn}>
          <Stat icon={Users} label="On roster" value={totals.students} tone="brand"
                hint={`${totals.enrolled} have enrolled`} />
        </motion.div>
        <motion.div variants={riseIn}>
          <Stat icon={CheckCircle2} label="Present today" value={presentToday} tone="good"
                hint={totals.enrolled ? `of ${totals.enrolled} enrolled` : "nobody enrolled yet"} />
        </motion.div>
        <motion.div variants={riseIn}>
          <Stat icon={Clock} label="Yet to enrol" value={totals.pending}
                tone={totals.pending ? "warn" : "good"}
                hint={totals.pending ? "share the class link" : "everyone is enrolled"} />
        </motion.div>
      </motion.div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card pad="p-4 sm:p-5">
          <CardTitle right={<Badge tone="muted">today</Badge>}>Attendance by class</CardTitle>
          {byClass.every((c) => !c.present) ? (
            <Empty icon={Camera} title="No attendance yet today"
                   sub="Open Live and point the camera at the room." />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={byClass} margin={{ top: 8, right: 8, left: -24, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="name" {...axis} tickLine={false} />
                <YAxis {...axis} tickLine={false} unit="%" domain={[0, 100]} />
                <Tooltip {...tip} formatter={(v) => [`${v}%`, "Present"]} />
                <Bar dataKey="percent" radius={[6, 6, 0, 0]} barSize={42}>
                  {byClass.map((c, i) => <Cell key={i} fill={tone(c.percent)} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>

        <Card pad="p-4 sm:p-5">
          <CardTitle right={<Badge tone="muted"><TrendingUp className="h-3 w-3" />14 days</Badge>}>
            Attendance trend
          </CardTitle>
          {trend.length < 2 ? (
            <Empty icon={TrendingUp} title="Not enough history yet"
                   sub="The trend appears once attendance has been taken on two or more days." />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={trend} margin={{ top: 8, right: 8, left: -24, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="day" {...axis} tickLine={false} />
                <YAxis {...axis} tickLine={false} unit="%" domain={[0, 100]} />
                <Tooltip {...tip} formatter={(v) => [`${v}%`, "Present"]} />
                <Line type="monotone" dataKey="percent" stroke="#4f8bff" strokeWidth={2.5}
                      dot={{ r: 3, fill: "#4f8bff" }} activeDot={{ r: 5 }} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </Card>
      </div>

      <h2 className="mb-3 mt-6 text-sm font-semibold uppercase tracking-wide text-white/90">
        Your classes
      </h2>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {classes.map((c) => {
          const t = today[c.id];
          return (
            <Card key={c.id} hover pad="p-4">
              <div className="mb-3 flex items-start justify-between gap-2">
                <Link to={`/classes/${c.id}`}
                      className="truncate text-sm font-semibold text-white hover:text-[--brand]">
                  {c.name}
                </Link>
                {t && (
                  <Badge tone={t.percent >= 75 ? "good" : t.percent >= 50 ? "warn" : "bad"}>
                    {t.percent}%
                  </Badge>
                )}
              </div>
              <div className="mb-3 grid grid-cols-3 gap-1.5 text-center">
                {[["Roster", c.total], ["Enrolled", c.enrolled], ["Present", t?.present ?? 0]]
                  .map(([k, v]) => (
                    <div key={k} className="rounded-lg border border-white/10 bg-black/20 p-2">
                      <div className="text-sm font-bold tabular-nums text-white">{v}</div>
                      <div className="text-[9px] uppercase tracking-wide text-slate-600">{k}</div>
                    </div>
                  ))}
              </div>
              {c.pending > 0 && (
                <p className="mb-2 flex items-center gap-1.5 text-[11px] text-amber-300">
                  <Link2 className="h-3 w-3" /> {c.pending} still to enrol
                </p>
              )}
              <Button as={Link} to={`/classes/${c.id}`} variant="ghost" size="sm"
                      className="mt-auto w-full">
                Open <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </Card>
          );
        })}
      </div>
    </div>
  );
}

/* ══════════════════ first run — no classes yet ══════════════════ */
function FirstRun() {
  const steps = [
    { icon: GraduationCap, title: "Create a class",
      body: "e.g. IT-B 4th Year. Each class keeps its own roster and its own attendance." },
    { icon: Users, title: "Paste your roster",
      body: "One line per student — roll number, name. Straight from your spreadsheet." },
    { icon: Link2, title: "Share the enrolment link",
      body: "Students open it on their phone and capture their own face. No account needed — and only roll numbers on your roster can use it." },
  ];
  return (
    <div className="min-h-screen w-full mx-auto max-w-3xl px-4 pt-24 pb-16 sm:px-6">
      <div className="mb-8 text-center">
        <span className="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-2xl
                         border border-white/10 bg-gradient-to-br from-[--brand]/25 to-violet-500/20">
          <GraduationCap className="h-6 w-6 text-sky-300" />
        </span>
        <h1 className="display-lg text-white">Set up your first class</h1>
        <p className="mx-auto mt-2 max-w-md text-sm text-[--muted]">
          Three steps. Students enrol themselves — you never sit through sixty face captures.
        </p>
      </div>

      <div className="mb-6 grid gap-3 sm:grid-cols-3">
        {steps.map((s, i) => (
          <motion.div key={s.title} initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.08 }}>
            <Card pad="p-4">
              <div className="mb-3 flex items-center gap-2">
                <span className="grid h-6 w-6 place-items-center rounded-md bg-[--brand]
                                 text-xs font-bold text-white">{i + 1}</span>
                <s.icon className="h-4 w-4 text-sky-300" />
              </div>
              <h3 className="mb-1.5 text-sm font-semibold text-white">{s.title}</h3>
              <p className="text-[12px] leading-relaxed text-[--muted]">{s.body}</p>
            </Card>
          </motion.div>
        ))}
      </div>

      <div className="text-center">
        <Button as={Link} to="/classes" size="lg">
          <Plus className="h-4 w-4" /> Create your first class
        </Button>
      </div>
    </div>
  );
}
