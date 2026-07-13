import React from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import {
  ResponsiveContainer, LineChart, Line, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ReferenceLine, Cell,
} from "recharts";
import { ArrowLeft, FlaskConical, TriangleAlert, CircleCheck } from "lucide-react";
import Aurora from "../components/Aurora";

/*
 * Everything on this page is a measurement produced by this repository:
 *   results/evaluation.json  (scripts/evaluate.py)   — ablation + degradation
 *   scripts/test_spoof.py                            — presentation attack
 *   results/benchmark.json   (scripts/benchmark.py)  — throughput
 *
 * Protocol: 96 VGGFace2 identities split into 30 "students" and 66 "strangers".
 * Student images split 70/30 into enrollment vs held-out probes. Strangers split in
 * half: one half calibrates the threshold, the other half measures it. Neither split
 * is optional — scoring a face against a centroid built from that same face gives
 * 100% and proves nothing.
 */

const ABLATION = [
  { name: "Baseline", accuracy: 87.4, far: 0.81, falseLog: 3.54 },
  { name: "+ Calibrated threshold", accuracy: 86.7, far: 0.20, falseLog: 1.01 },
  { name: "+ Top-2 margin", accuracy: 86.3, far: 0.20, falseLog: 1.01 },
  { name: "+ Temporal voting", accuracy: 86.3, far: 0.20, falseLog: 0.0 },
];

const DEGRADATION = [
  { px: 16, accuracy: 63.9 }, { px: 24, accuracy: 83.3 }, { px: 32, accuracy: 86.1 },
  { px: 40, accuracy: 88.9 }, { px: 48, accuracy: 88.9 }, { px: 64, accuracy: 88.9 },
  { px: 80, accuracy: 88.9 }, { px: 96, accuracy: 88.9 }, { px: 112, accuracy: 88.9 },
];

const SPOOF = [
  { name: "Recognition only", success: 100 },
  { name: "+ Liveness", success: 0 },
];

const THROUGHPUT = [
  { faces: 1, ms: 249 }, { faces: 2, ms: 331 }, { faces: 4, ms: 548 },
  { faces: 8, ms: 934 }, { faces: 16, ms: 1271 },
];

// one surface, shared with every other page (see index.css / components/ui.jsx)
const card = "card-glass p-5";

const axis = { stroke: "#64748b", fontSize: 12 };
const tooltipStyle = {
  contentStyle: {
    background: "rgba(6,11,35,0.95)", border: "1px solid rgba(255,255,255,0.12)",
    borderRadius: 12, color: "#e2e8f0", fontSize: 12,
  },
};

function Section({ title, kicker, children, delay = 0 }) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}
      className="mb-10"
    >
      <h2 className="display-lg text-white">{title}</h2>
      {kicker && <p className="mt-2 mb-5 max-w-2xl text-[13px] leading-relaxed text-[--muted]">{kicker}</p>}
      {children}
    </motion.section>
  );
}

export default function Research() {
  return (
    <div className="relative min-h-screen">
      <Aurora variant="soft" />

      <div className="relative z-10 mx-auto max-w-6xl px-5 py-10 sm:px-8">
        <Link
          to="/"
          className="mb-8 inline-flex items-center gap-2 text-sm text-[--muted] transition hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" /> Back
        </Link>

        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
          className="mb-10"
        >
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-violet-400/30
                          bg-violet-500/10 px-3.5 py-1.5 text-xs font-medium text-violet-300">
            <FlaskConical className="h-3.5 w-3.5" />
            Evaluation
          </div>
          <h1 className="display-xl">
            What we measured
          </h1>
          <p className="mt-4 max-w-2xl text-[15px] leading-relaxed text-[--muted]">
            30 simulated students, 66 strangers, held-out test images, and a separate
            calibration split. A face is never scored against a centroid built from that
            same face — that would give 100% and mean nothing.
          </p>
        </motion.div>

        {/* ── spoof ──────────────────────────────────────────────────────── */}
        <Section
          title="1 · Can a photograph fool it?"
          kicker="Face recognition is designed to give a photo of you the same embedding as you — that is what makes it good. So recognition alone cannot prevent proxy attendance, and every paper that claims it does is wrong. We held a photo to the camera and counted."
        >
          <div className="grid gap-5 md:grid-cols-[1fr_1.2fr]">
            <div className={card}>
              <ResponsiveContainer width="100%" height={230}>
                <BarChart data={SPOOF} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="name" {...axis} tickLine={false} />
                  <YAxis {...axis} tickLine={false} unit="%" domain={[0, 100]} />
                  <Tooltip {...tooltipStyle} formatter={(v) => [`${v}%`, "Attack success"]} />
                  <Bar dataKey="success" radius={[8, 8, 0, 0]} barSize={70}>
                    <Cell fill="#f43f5e" />
                    <Cell fill="#10b981" />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className={`${card} flex flex-col justify-center`}>
              <div className="mb-4 flex items-start gap-3">
                <TriangleAlert className="mt-0.5 h-5 w-5 shrink-0 text-rose-400" />
                <p className="text-sm leading-relaxed text-slate-300">
                  <span className="font-semibold text-rose-300">Without liveness, every photo got in.</span>{" "}
                  100% attack success. The model recognised the photo perfectly — which is exactly
                  the problem.
                </p>
              </div>
              <div className="flex items-start gap-3">
                <CircleCheck className="mt-0.5 h-5 w-5 shrink-0 text-emerald-400" />
                <p className="text-sm leading-relaxed text-slate-300">
                  <span className="font-semibold text-emerald-300">With liveness, none did.</span>{" "}
                  A live face keeps deforming; a photo is rigid. We divide out translation, rotation
                  and scale first, so shaking the photo about does not help.
                </p>
              </div>
              <div className="mt-5 rounded-xl border border-white/10 bg-black/20 p-3 font-mono text-xs text-slate-400">
                photo (hand-held) 0.015 · Arnab 0.066 · Soham 0.135 · threshold 0.035
              </div>
            </div>
          </div>
        </Section>

        {/* ── ablation ───────────────────────────────────────────────────── */}
        <Section
          title="2 · What does each guard actually buy?"
          kicker="Each row switches on one more guard. If a guard doesn't help, it stays in the table anyway — that is the whole point of running the experiment."
          delay={0.05}
        >
          <div className={card}>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={ABLATION} margin={{ top: 10, right: 10, left: -18, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="name" {...axis} tickLine={false} interval={0} tick={{ fontSize: 10, fill: "#94a3b8" }} />
                <YAxis {...axis} tickLine={false} unit="%" />
                <Tooltip {...tooltipStyle} />
                <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
                <Bar dataKey="far" name="Strangers admitted (FAR)" fill="#38bdf8" radius={[6, 6, 0, 0]} />
                <Bar dataKey="falseLog" name="Wrong attendance records" fill="#a78bfa" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>

            <div className="mt-6 grid gap-3 sm:grid-cols-3">
              <div className="rounded-xl border border-sky-400/25 bg-sky-500/10 p-4">
                <div className="text-sm font-semibold text-sky-300">Calibrated threshold</div>
                <div className="mt-1 text-xs leading-relaxed text-slate-400">
                  Strangers admitted fell 4× (0.81% → 0.20%) for under 1 point of accuracy.
                </div>
              </div>
              <div className="rounded-xl border border-emerald-400/25 bg-emerald-500/10 p-4">
                <div className="text-sm font-semibold text-emerald-300">Temporal voting</div>
                <div className="mt-1 text-xs leading-relaxed text-slate-400">
                  Wrong attendance records → 0%. A stranger may fool one frame, not three.
                </div>
              </div>
              <div className="rounded-xl border border-amber-400/25 bg-amber-500/10 p-4">
                <div className="text-sm font-semibold text-amber-300">Top-2 margin — no effect</div>
                <div className="mt-1 text-xs leading-relaxed text-slate-400">
                  Built to catch look-alikes. It changed nothing, and we report it.
                </div>
              </div>
            </div>
          </div>
        </Section>

        {/* ── degradation ────────────────────────────────────────────────── */}
        <Section
          title="3 · How far away can a student sit?"
          kicker="We shrink the face to simulate distance and re-measure. This gives a hard camera specification instead of a guess — and our first guess (60px) was wrong, throwing away faces that work perfectly well."
          delay={0.1}
        >
          <div className="grid gap-5 md:grid-cols-[1.4fr_1fr]">
            <div className={card}>
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={DEGRADATION} margin={{ top: 10, right: 14, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="px" {...axis} tickLine={false} unit="px" />
                  <YAxis {...axis} tickLine={false} unit="%" domain={[55, 95]} />
                  <Tooltip {...tooltipStyle} formatter={(v) => [`${v}%`, "Accuracy"]}
                           labelFormatter={(l) => `Face width ${l}px`} />
                  <ReferenceLine x={40} stroke="#f59e0b" strokeDasharray="4 4"
                                 label={{ value: "gate: 40px", fill: "#f59e0b", fontSize: 11, position: "top" }} />
                  <Line type="monotone" dataKey="accuracy" stroke="#38bdf8" strokeWidth={2.5}
                        dot={{ r: 4, fill: "#38bdf8" }} activeDot={{ r: 6 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className={`${card} flex flex-col justify-center gap-3 text-sm leading-relaxed text-slate-300`}>
              <p>
                Accuracy collapses below <span className="font-semibold text-rose-300">24px</span> and
                is fully recovered by <span className="font-semibold text-emerald-300">40px</span>.
              </p>
              <p className="text-slate-400">
                Below the gate the classifier still confidently names <em>someone</em> — a softmax has
                no way to abstain. That is why the gate exists: a face too small to identify must be
                refused, not guessed at.
              </p>
              <div className="mt-1 rounded-xl border border-white/10 bg-black/20 p-3 text-xs text-slate-400">
                40px ⇒ <span className="text-sky-300">1080p camera covers ~7 m</span> · 720p only ~5 m
              </div>
            </div>
          </div>
        </Section>

        {/* ── throughput ─────────────────────────────────────────────────── */}
        <Section
          title="4 · Does it scale to a classroom?"
          kicker="Detection is a fixed ~200ms per frame; each extra face adds only ~65ms. The system gets more efficient per student as the room fills."
          delay={0.15}
        >
          <div className={card}>
            <ResponsiveContainer width="100%" height={230}>
              <LineChart data={THROUGHPUT} margin={{ top: 10, right: 14, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="faces" {...axis} tickLine={false}
                       label={{ value: "faces in frame", fill: "#64748b", fontSize: 11, dy: 12 }} />
                <YAxis {...axis} tickLine={false} unit="ms" />
                <Tooltip {...tooltipStyle} formatter={(v) => [`${v} ms`, "Latency"]}
                         labelFormatter={(l) => `${l} face${l > 1 ? "s" : ""}`} />
                <Line type="monotone" dataKey="ms" stroke="#a78bfa" strokeWidth={2.5}
                      dot={{ r: 4, fill: "#a78bfa" }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
            <p className="mt-4 text-xs text-slate-500">
              MacBook Air, CPU only, no GPU. 16 faces in 1.27s. Enrolling 10,000 students adds
              1.2ms to a match — the model is frozen, so scale is a matrix multiply, not a retrain.
            </p>
          </div>
        </Section>

        {/* ── limits ─────────────────────────────────────────────────────── */}
        <Section title="5 · Limitations" delay={0.2}>
          <div className="rounded-[--r-lg] border border-amber-400/20 bg-amber-500/[0.06] p-5 backdrop-blur-xl">
            <ul className="space-y-2.5 text-[13px] leading-relaxed text-amber-100/75">
              <li>
                <span className="font-semibold text-amber-200">Video replay defeats liveness.</span>{" "}
                A recorded face genuinely moves. We raise the attack cost from “print a photo” to
                “record and replay a video” — a real gain, not a complete defence.
              </li>
              <li>
                <span className="font-semibold text-amber-200">The cohort is photographic.</span>{" "}
                VGGFace2 images are cleaner than a classroom webcam, so real-world numbers will be
                worse than these.
              </li>
              <li>
                <span className="font-semibold text-amber-200">The look-alike guard is untested.</span>{" "}
                The cohort contains no look-alike pairs, so the top-2 margin had nothing to catch.
                We cannot claim it works.
              </li>
              <li>
                <span className="font-semibold text-amber-200">Two real enrolled users.</span>{" "}
                The live deployment is a feasibility demo. Every quantitative claim above comes from
                the 30-identity cohort, not from those two.
              </li>
            </ul>
          </div>
        </Section>
      </div>
    </div>
  );
}
