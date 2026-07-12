import React from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import {
  ShieldCheck, Zap, ScanFace, EyeOff, Users, Gauge,
  ArrowRight, Github, Cpu, Lock,
} from "lucide-react";
import Aurora from "../components/Aurora";
import FaceScan from "../components/FaceScan";

// Every number on this page is measured, not marketing. Sources:
//   spoof      -> scripts/test_spoof.py
//   FAR / logs -> scripts/evaluate.py  (results/evaluation.json)
//   enrollment -> trainer.retrain, cold vs warm embedding cache
//   throughput -> scripts/benchmark.py (results/benchmark.json)
const HEADLINE_STATS = [
  { value: "100% → 0%", label: "Photo-attack success", sub: "liveness detection", accent: "text-rose-300" },
  { value: "0.20%", label: "Strangers admitted", sub: "was 0.81% before calibration", accent: "text-sky-300" },
  { value: "0%", label: "Wrong attendance records", sub: "was 3.54%", accent: "text-emerald-300" },
  { value: "1.4s", label: "To enroll a student", sub: "was 607s", accent: "text-violet-300" },
];

const FEATURES = [
  {
    icon: EyeOff,
    title: "It knows a photo isn't you",
    body:
      "Face recognition is built to match a photo of you to you — so recognition alone marks a printed photo present, every single time. We measure facial motion the detector already gives us for free: a live face keeps deforming, a photograph is rigid. Waving the photo around doesn't help, because rotation and scale are normalised away.",
    tone: "from-rose-500/20 to-orange-500/10 border-rose-400/30",
  },
  {
    icon: ShieldCheck,
    title: "It can say “nobody”",
    body:
      "A softmax classifier must always name someone — it has no option to reject. We match against identity centroids and calibrate the cutoff against 2,880 held-out impostor faces at a 1% target false-accept rate. The threshold comes from data, not a guess.",
    tone: "from-sky-500/20 to-cyan-500/10 border-sky-400/30",
  },
  {
    icon: Lock,
    title: "Recognition ≠ attendance",
    body:
      "Attendance is written once a day and is irreversible: one bad frame marks the wrong student present until tomorrow. So the commit is a separate decision that accumulates evidence over several frames before it writes anything.",
    tone: "from-emerald-500/20 to-teal-500/10 border-emerald-400/30",
  },
  {
    icon: Zap,
    title: "Enrolling is instant",
    body:
      "The deep model is frozen and never retrained. Adding a student means embedding their photos and storing a centroid — so enrollment is a table insert, not a training run. Embeddings are cached, so only the new student is ever computed.",
    tone: "from-violet-500/20 to-fuchsia-500/10 border-violet-400/30",
  },
];

const PIPELINE = [
  { icon: ScanFace, k: "Detect", v: "RetinaFace finds every face in the frame" },
  { icon: Cpu, k: "Embed", v: "ArcFace → 512-d vector per face" },
  { icon: Users, k: "Match", v: "cosine vs. each student's centroid" },
  { icon: EyeOff, k: "Verify", v: "liveness: is this a person or a photo?" },
  { icon: ShieldCheck, k: "Commit", v: "evidence across frames → attendance" },
];

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  show: (i = 0) => ({
    opacity: 1, y: 0,
    transition: { delay: i * 0.08, duration: 0.6, ease: [0.22, 1, 0.36, 1] },
  }),
};

export default function Home() {
  return (
    <div className="relative min-h-screen text-slate-100">
      <Aurora />

      {/* ── nav ─────────────────────────────────────────────────────────── */}
      <header className="relative z-10 mx-auto flex max-w-7xl items-center justify-between px-6 py-6">
        <div className="flex items-center gap-2.5">
          <div className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-sky-400 to-violet-500 shadow-lg shadow-sky-500/25">
            <ScanFace className="h-5 w-5 text-white" />
          </div>
          <span className="text-lg font-semibold tracking-tight">
            Presence<span className="text-sky-400">AI</span>
          </span>
        </div>
        <nav className="hidden items-center gap-8 text-sm text-slate-300 md:flex">
          <a href="#how" className="transition hover:text-white">How it works</a>
          <a href="#results" className="transition hover:text-white">Results</a>
          <Link to="/research" className="transition hover:text-white">Research</Link>
        </nav>
        <Link
          to="/login"
          className="rounded-xl border border-white/15 bg-white/5 px-4 py-2 text-sm font-medium
                     backdrop-blur transition hover:border-sky-400/50 hover:bg-white/10"
        >
          Sign in
        </Link>
      </header>

      {/* ── hero ────────────────────────────────────────────────────────── */}
      <section className="relative z-10 mx-auto grid max-w-7xl items-center gap-16 px-6 pt-10 pb-24 lg:grid-cols-2 lg:pt-20">
        <div>
          <motion.div
            initial="hidden" animate="show" variants={fadeUp}
            className="mb-6 inline-flex items-center gap-2 rounded-full border border-sky-400/30
                       bg-sky-500/10 px-3.5 py-1.5 text-xs font-medium text-sky-300 backdrop-blur"
          >
            <span className="relative flex h-1.5 w-1.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-sky-400 opacity-75" />
              <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-sky-400" />
            </span>
            ArcFace · 512-d embeddings · liveness verified
          </motion.div>

          <motion.h1
            custom={1} initial="hidden" animate="show" variants={fadeUp}
            className="text-5xl font-bold leading-[1.05] tracking-tight sm:text-6xl lg:text-7xl"
          >
            Attendance that
            <span className="block bg-gradient-to-r from-sky-300 via-indigo-300 to-violet-400 bg-clip-text text-transparent">
              a photo can't fake.
            </span>
          </motion.h1>

          <motion.p
            custom={2} initial="hidden" animate="show" variants={fadeUp}
            className="mt-6 max-w-xl text-lg leading-relaxed text-slate-300/90"
          >
            Multiple faces, one frame, marked in seconds. We found that a
            state-of-the-art face model still marks a{" "}
            <span className="text-rose-300">printed photograph present 100% of the time</span> —
            so we built the decision layer that stops it, and measured every part of it.
          </motion.p>

          <motion.div
            custom={3} initial="hidden" animate="show" variants={fadeUp}
            className="mt-9 flex flex-wrap items-center gap-4"
          >
            <Link
              to="/login"
              className="group inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-sky-500 to-violet-500
                         px-6 py-3.5 font-semibold text-white shadow-lg shadow-violet-600/25
                         transition hover:shadow-xl hover:shadow-violet-500/40"
            >
              Launch the system
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Link>
            <Link
              to="/research"
              className="inline-flex items-center gap-2 rounded-xl border border-white/15 bg-white/5
                         px-6 py-3.5 font-semibold backdrop-blur transition hover:border-white/30 hover:bg-white/10"
            >
              <Gauge className="h-4 w-4" />
              See the measurements
            </Link>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
          className="relative mx-auto w-full max-w-md"
        >
          <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-8 backdrop-blur-xl
                          shadow-2xl shadow-sky-900/40">
            <FaceScan />
          </div>
        </motion.div>
      </section>

      {/* ── headline numbers ────────────────────────────────────────────── */}
      <section id="results" className="relative z-10 mx-auto max-w-7xl px-6 pb-24">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {HEADLINE_STATS.map((s, i) => (
            <motion.div
              key={s.label}
              custom={i}
              initial="hidden" whileInView="show" viewport={{ once: true, margin: "-80px" }}
              variants={fadeUp}
              whileHover={{ y: -4 }}
              className="rounded-2xl border border-white/10 bg-white/[0.04] p-6 backdrop-blur-xl
                         transition hover:border-white/20"
            >
              <div className={`text-3xl font-bold tracking-tight ${s.accent}`}>{s.value}</div>
              <div className="mt-2 text-sm font-medium text-slate-200">{s.label}</div>
              <div className="mt-1 text-xs text-slate-400">{s.sub}</div>
            </motion.div>
          ))}
        </div>
        <p className="mt-5 text-center text-xs text-slate-500">
          Measured on a 30-identity cohort with held-out test images and 2,880 impostor faces —
          not quoted from a paper.
        </p>
      </section>

      {/* ── pipeline ────────────────────────────────────────────────────── */}
      <section id="how" className="relative z-10 mx-auto max-w-7xl px-6 pb-24">
        <motion.h2
          initial="hidden" whileInView="show" viewport={{ once: true }} variants={fadeUp}
          className="mb-3 text-center text-4xl font-bold tracking-tight"
        >
          Five decisions per face
        </motion.h2>
        <motion.p
          custom={1} initial="hidden" whileInView="show" viewport={{ once: true }} variants={fadeUp}
          className="mx-auto mb-14 max-w-2xl text-center text-slate-400"
        >
          Every face in the frame runs the full gauntlet. Any gate can refuse — and refusing
          is the point.
        </motion.p>

        <div className="relative grid gap-4 md:grid-cols-5">
          <div className="absolute left-0 right-0 top-[38px] hidden h-px bg-gradient-to-r
                          from-transparent via-sky-400/30 to-transparent md:block" />
          {PIPELINE.map((s, i) => (
            <motion.div
              key={s.k}
              custom={i}
              initial="hidden" whileInView="show" viewport={{ once: true, margin: "-60px" }}
              variants={fadeUp}
              className="relative rounded-2xl border border-white/10 bg-white/[0.04] p-5 text-center backdrop-blur-xl"
            >
              <div className="mx-auto mb-4 grid h-12 w-12 place-items-center rounded-xl
                              bg-gradient-to-br from-sky-500/25 to-violet-500/25 ring-1 ring-white/10">
                <s.icon className="h-5 w-5 text-sky-300" />
              </div>
              <div className="text-sm font-semibold text-white">{s.k}</div>
              <div className="mt-1.5 text-xs leading-relaxed text-slate-400">{s.v}</div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── what makes it different ─────────────────────────────────────── */}
      <section className="relative z-10 mx-auto max-w-7xl px-6 pb-24">
        <div className="grid gap-5 md:grid-cols-2">
          {FEATURES.map((f, i) => (
            <motion.div
              key={f.title}
              custom={i}
              initial="hidden" whileInView="show" viewport={{ once: true, margin: "-60px" }}
              variants={fadeUp}
              whileHover={{ y: -4 }}
              className={`rounded-2xl border bg-gradient-to-br ${f.tone} p-7 backdrop-blur-xl transition`}
            >
              <f.icon className="mb-4 h-6 w-6 text-white/90" />
              <h3 className="mb-2.5 text-xl font-semibold tracking-tight">{f.title}</h3>
              <p className="text-sm leading-relaxed text-slate-300/85">{f.body}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── capacity ────────────────────────────────────────────────────── */}
      <section className="relative z-10 mx-auto max-w-7xl px-6 pb-24">
        <motion.div
          initial="hidden" whileInView="show" viewport={{ once: true }} variants={fadeUp}
          className="overflow-hidden rounded-3xl border border-white/10 bg-white/[0.04] backdrop-blur-xl"
        >
          <div className="grid divide-y divide-white/10 md:grid-cols-3 md:divide-x md:divide-y-0">
            {[
              { k: "16 faces", v: "recognised in one frame, in 1.27s on a laptop CPU — no GPU" },
              { k: "10,000 students", v: "enrolled adds 1.2ms to a match. Scale is essentially free" },
              { k: "7 metres", v: "recognition range with one 1080p camera — covers a classroom" },
            ].map((c) => (
              <div key={c.k} className="p-8">
                <div className="bg-gradient-to-r from-sky-300 to-violet-300 bg-clip-text text-2xl
                                font-bold text-transparent">
                  {c.k}
                </div>
                <div className="mt-2 text-sm leading-relaxed text-slate-400">{c.v}</div>
              </div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* ── honesty ─────────────────────────────────────────────────────── */}
      <section className="relative z-10 mx-auto max-w-4xl px-6 pb-24">
        <motion.div
          initial="hidden" whileInView="show" viewport={{ once: true }} variants={fadeUp}
          className="rounded-2xl border border-amber-400/25 bg-amber-500/[0.07] p-7 backdrop-blur-xl"
        >
          <h3 className="mb-3 flex items-center gap-2 text-lg font-semibold text-amber-200">
            <ShieldCheck className="h-5 w-5" />
            What this does not do
          </h3>
          <p className="text-sm leading-relaxed text-amber-100/70">
            Liveness stops a <em>printed photo</em> and a still phone screen. A <em>video replay</em> of a
            real person would still pass, because the recorded face genuinely moves — beating that
            needs a depth or texture based anti-spoof model, and it is our next step. We also
            tested a top-2 margin guard against look-alike students and{" "}
            <span className="text-amber-200">it did not help</span>, so we report that too. Numbers
            that only ever go your way are numbers nobody should believe.
          </p>
        </motion.div>
      </section>

      {/* ── footer ──────────────────────────────────────────────────────── */}
      <footer className="relative z-10 border-t border-white/10 px-6 py-10">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 text-sm text-slate-500 sm:flex-row">
          <span>PresenceAI — Automatic Attendance using Multiple Face Recognition</span>
          <a
            href="https://github.com/SohamBhattacharjee2003/MutiFace-Attendance-System"
            target="_blank" rel="noreferrer"
            className="inline-flex items-center gap-2 transition hover:text-slate-300"
          >
            <Github className="h-4 w-4" /> Source
          </a>
        </div>
      </footer>
    </div>
  );
}
