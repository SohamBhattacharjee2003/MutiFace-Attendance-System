import React from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import {
  ShieldCheck, Zap, ScanFace, EyeOff, Users, Gauge,
  ArrowRight, Github, Cpu, Lock, Ruler, TriangleAlert,
} from "lucide-react";
import Aurora from "../components/Aurora";
import FaceScan from "../components/FaceScan";
import { Card, Badge, Button, stagger, riseIn } from "../components/ui";

/* Every number here is measured by this repository, not marketing copy:
     spoof      -> scripts/test_spoof.py
     FAR / logs -> scripts/evaluate.py   (results/evaluation.json)
     enrollment -> trainer.retrain, cold vs warm embedding cache
     throughput -> scripts/benchmark.py  (results/benchmark.json)  */
const STATS = [
  { value: "100% → 0%", label: "Photo-attack success", sub: "with liveness detection", tone: "text-rose-300" },
  { value: "0.20%", label: "Strangers admitted", sub: "was 0.81% before calibration", tone: "text-sky-300" },
  { value: "0%", label: "Wrong attendance records", sub: "was 3.54%", tone: "text-emerald-300" },
  { value: "1.4s", label: "To enroll a student", sub: "was 607s", tone: "text-violet-300" },
];

const PIPELINE = [
  { icon: ScanFace, k: "Detect", v: "RetinaFace finds every face in the frame" },
  { icon: Cpu, k: "Embed", v: "ArcFace → a 512-d vector per face" },
  { icon: Users, k: "Match", v: "cosine against each student's centroid" },
  { icon: EyeOff, k: "Verify", v: "person, or a photo of a person?" },
  { icon: Lock, k: "Commit", v: "evidence across frames → attendance" },
];

const FEATURES = [
  {
    icon: EyeOff, tone: "bad",
    title: "It knows a photo isn't you",
    body: "Face recognition is built to match a photo of you to you — so recognition alone marks a printed photo present, every time. We measure facial motion from landmarks the detector already produces: a live face keeps deforming, a photograph is rigid. Waving the photo around doesn't help, because rotation and scale are normalised away first.",
  },
  {
    icon: ShieldCheck, tone: "brand",
    title: "It can answer “nobody”",
    body: "A softmax classifier must always name someone; it has no way to abstain. We match against identity centroids and calibrate the cutoff against 2,880 held-out impostor faces at a 1% target false-accept rate. The threshold is derived from data, not guessed.",
  },
  {
    icon: Lock, tone: "good",
    title: "Recognition ≠ attendance",
    body: "Attendance is written once a day and is irreversible — one bad frame marks the wrong student present until tomorrow. So committing is a separate decision that accumulates evidence across frames before it writes anything.",
  },
  {
    icon: Zap, tone: "violet",
    title: "Enrolling is instant",
    body: "The deep model is frozen and never retrained. Adding a student means embedding their photos and storing a centroid — a table insert, not a training run. Embeddings are cached, so only the new student is ever computed.",
  },
];

const CAPACITY = [
  { icon: Users, k: "16 faces", v: "recognised in a single frame in 1.27s — laptop CPU, no GPU" },
  { icon: Gauge, k: "10,000 students", v: "adds 1.2ms to a match. Scale is a matrix multiply" },
  { icon: Ruler, k: "7 metres", v: "range on one 1080p camera — covers a classroom" },
];

const toneRing = {
  bad: "border-rose-400/25 bg-rose-500/10 text-rose-300",
  brand: "border-sky-400/25 bg-sky-500/10 text-sky-300",
  good: "border-emerald-400/25 bg-emerald-500/10 text-emerald-300",
  violet: "border-violet-400/25 bg-violet-500/10 text-violet-300",
};

export default function Home() {
  return (
    <div className="relative min-h-screen">
      <Aurora />

      {/* ── nav ──────────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-30 border-b border-white/[0.06] backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-3.5 sm:px-8">
          <Link to="/" className="flex items-center gap-2.5">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-[--brand] to-violet-500">
              <ScanFace className="h-4 w-4 text-white" />
            </span>
            <span className="text-base font-semibold tracking-tight">
              Presence<span className="text-[--brand]">AI</span>
            </span>
          </Link>
          <nav className="hidden items-center gap-7 text-sm text-[--muted] md:flex">
            <a href="#how" className="transition hover:text-white">How it works</a>
            <a href="#results" className="transition hover:text-white">Results</a>
            <Link to="/research" className="transition hover:text-white">Research</Link>
          </nav>
          <Button as={Link} to="/login" variant="ghost" size="sm">Sign in</Button>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-5 sm:px-8">
        {/* ── hero ───────────────────────────────────────────────────── */}
        <section className="grid items-center gap-12 py-14 lg:grid-cols-[1.05fr_0.95fr] lg:py-20">
          <motion.div variants={stagger} initial="hidden" animate="show">
            <motion.div variants={riseIn}>
              <Badge tone="brand">
                <span className="relative flex h-1.5 w-1.5">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-sky-400 opacity-75" />
                  <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-sky-400" />
                </span>
                ArcFace · 512-d embeddings · liveness verified
              </Badge>
            </motion.div>

            <motion.h1 variants={riseIn} className="display-xl mt-5">
              Attendance that
              <span className="block bg-gradient-to-r from-sky-300 via-indigo-300 to-violet-400 bg-clip-text text-transparent">
                a photo can’t fake.
              </span>
            </motion.h1>

            <motion.p variants={riseIn} className="mt-5 max-w-lg text-[15px] leading-relaxed text-[--muted]">
              Multiple faces, one frame, marked in seconds. We found that a
              state-of-the-art face model still marks a{" "}
              <span className="text-rose-300">printed photograph present 100% of the time</span> —
              so we built the decision layer that stops it, and measured every part of it.
            </motion.p>

            <motion.div variants={riseIn} className="mt-8 flex flex-wrap gap-3">
              <Button as={Link} to="/login" size="lg" className="group">
                Launch the system
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
              </Button>
              <Button as={Link} to="/research" variant="ghost" size="lg">
                <Gauge className="h-4 w-4" />
                See the measurements
              </Button>
            </motion.div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.94 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
            className="mx-auto w-full max-w-sm"
          >
            <Card pad="p-6" className="shadow-2xl shadow-sky-950/40">
              <FaceScan />
            </Card>
          </motion.div>
        </section>

        {/* ── headline numbers ───────────────────────────────────────── */}
        <section id="results" className="pb-16">
          <motion.div
            variants={stagger} initial="hidden" whileInView="show" viewport={{ once: true, margin: "-60px" }}
            className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"
          >
            {STATS.map((s) => (
              <motion.div key={s.label} variants={riseIn}>
                <Card hover pad="p-4">
                  <div className={`text-xl font-bold tracking-tight ${s.tone}`}>{s.value}</div>
                  <div className="mt-1.5 text-[13px] font-medium text-slate-200">{s.label}</div>
                  <div className="mt-auto pt-2 text-[11px] text-slate-500">{s.sub}</div>
                </Card>
              </motion.div>
            ))}
          </motion.div>
          <p className="mt-4 text-center text-[11px] text-slate-500">
            Measured on a 30-identity cohort with held-out test images and 2,880 impostor faces.
          </p>
        </section>

        {/* ── pipeline ───────────────────────────────────────────────── */}
        <section id="how" className="pb-16">
          <motion.div
            variants={stagger} initial="hidden" whileInView="show" viewport={{ once: true, margin: "-60px" }}
          >
            <motion.h2 variants={riseIn} className="display-lg text-center">
              Five decisions per face
            </motion.h2>
            <motion.p variants={riseIn} className="mx-auto mt-2.5 mb-9 max-w-lg text-center text-sm text-[--muted]">
              Every face runs the full gauntlet. Any gate can refuse — and refusing is the point.
            </motion.p>

            <div className="relative grid gap-3 sm:grid-cols-3 lg:grid-cols-5">
              <div className="absolute inset-x-6 top-[34px] hidden h-px bg-gradient-to-r
                              from-transparent via-sky-400/25 to-transparent lg:block" />
              {PIPELINE.map((s) => (
                <motion.div key={s.k} variants={riseIn}>
                  <Card pad="p-4" className="items-center text-center">
                    <span className="mb-3 grid h-10 w-10 place-items-center rounded-lg
                                     border border-white/10 bg-gradient-to-br from-sky-500/20 to-violet-500/20">
                      <s.icon className="h-4 w-4 text-sky-300" />
                    </span>
                    <div className="text-[13px] font-semibold text-white">{s.k}</div>
                    <div className="mt-1 text-[11px] leading-relaxed text-slate-500">{s.v}</div>
                  </Card>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </section>

        {/* ── what makes it different ────────────────────────────────── */}
        <section className="pb-16">
          <motion.div
            variants={stagger} initial="hidden" whileInView="show" viewport={{ once: true, margin: "-60px" }}
            className="grid gap-3 md:grid-cols-2"
          >
            {FEATURES.map((f) => (
              <motion.div key={f.title} variants={riseIn}>
                <Card hover pad="p-5">
                  <span className={`mb-3.5 grid h-9 w-9 place-items-center rounded-lg border ${toneRing[f.tone]}`}>
                    <f.icon className="h-4 w-4" />
                  </span>
                  <h3 className="mb-2 text-base font-semibold tracking-tight text-white">{f.title}</h3>
                  <p className="text-[13px] leading-relaxed text-[--muted]">{f.body}</p>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        </section>

        {/* ── capacity ───────────────────────────────────────────────── */}
        <section className="pb-16">
          <motion.div
            variants={stagger} initial="hidden" whileInView="show" viewport={{ once: true, margin: "-60px" }}
            className="grid gap-3 md:grid-cols-3"
          >
            {CAPACITY.map((c) => (
              <motion.div key={c.k} variants={riseIn}>
                <Card pad="p-5">
                  <c.icon className="mb-3 h-4 w-4 text-sky-300" />
                  <div className="bg-gradient-to-r from-sky-300 to-violet-300 bg-clip-text text-lg
                                  font-bold text-transparent">
                    {c.k}
                  </div>
                  <div className="mt-1.5 text-[12px] leading-relaxed text-[--muted]">{c.v}</div>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        </section>

        {/* ── honesty ────────────────────────────────────────────────── */}
        <section className="pb-16">
          <motion.div
            initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }} transition={{ duration: 0.5 }}
            className="rounded-[--r-lg] border border-amber-400/20 bg-amber-500/[0.06] p-5 backdrop-blur-xl"
          >
            <h3 className="mb-2.5 flex items-center gap-2 text-sm font-semibold text-amber-200">
              <TriangleAlert className="h-4 w-4" />
              What this does not do
            </h3>
            <p className="text-[13px] leading-relaxed text-amber-100/70">
              Liveness stops a <em>printed photo</em> and a still phone screen. A <em>video replay</em>{" "}
              of a real person would still pass, because the recorded face genuinely moves — beating
              that needs a depth or texture based anti-spoof model, and it is the next step. We also
              tested a top-2 margin guard against look-alike students and{" "}
              <span className="text-amber-200">it did not help</span>, so we report that too. Numbers
              that only ever go your way are numbers nobody should believe.
            </p>
          </motion.div>
        </section>
      </main>

      <footer className="border-t border-white/[0.06]">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-5
                        py-7 text-xs text-slate-500 sm:flex-row sm:px-8">
          <span>PresenceAI — Automatic Attendance using Multiple Face Recognition</span>
          <a
            href="https://github.com/SohamBhattacharjee2003/MutiFace-Attendance-System"
            target="_blank" rel="noreferrer"
            className="inline-flex items-center gap-1.5 transition hover:text-slate-300"
          >
            <Github className="h-3.5 w-3.5" /> Source
          </a>
        </div>
      </footer>
    </div>
  );
}
