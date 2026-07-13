import React, { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Camera, ScanFace, CheckCircle2, Loader2, Users, EyeOff, Ruler,
  HelpCircle, ShieldCheck, RotateCcw,
} from "lucide-react";
import { Card, CardTitle, Button, Badge, Empty } from "../components/ui";
import { predictFace, getClasses } from "../utils/api";

/**
 * "Point the camera at the room and press the button" attendance.
 *
 * It deliberately does NOT let you upload a photo. An uploaded image cannot be
 * liveness-checked — you could photograph the class once and mark everyone present for the
 * rest of term, which is the exact attack this project exists to stop. So a "capture" is a
 * short BURST of live frames instead: the same one-click experience, but liveness and the
 * three-frame vote still apply to every face.
 */
const BURST_FRAMES = 8;      // ~5.5s at 700ms — enough for liveness + the 3-frame vote
const FRAME_MS = 700;

const VERDICTS = {
  face_too_small: { label: "Too far", tone: "warn", icon: Ruler },
  low_detection_quality: { label: "Poor detection", tone: "warn", icon: HelpCircle },
  below_threshold: { label: "Unknown", tone: "bad", icon: HelpCircle },
  ambiguous: { label: "Uncertain", tone: "warn", icon: HelpCircle },
  checking: { label: "Verifying", tone: "brand", icon: Loader2 },
  spoof_suspected: { label: "Not live", tone: "bad", icon: EyeOff },
};

export default function Capture() {
  const [classes, setClasses] = useState([]);
  const [classId, setClassId] = useState("");
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const [cameraOn, setCameraOn] = useState(false);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState(0);
  const [seen, setSeen] = useState({});      // key -> best result across the burst
  const [done, setDone] = useState(false);

  useEffect(() => {
    start();
    getClasses().then((cs) => {
      setClasses(cs);
      if (cs.length === 1) setClassId(cs[0].id);   // one class: no reason to ask
    }).catch(console.error);
    return () => stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const start = async () => {
    try {
      const s = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 } });
      streamRef.current = s;
      if (videoRef.current) videoRef.current.srcObject = s;
      setCameraOn(true);
    } catch {
      alert("Could not access the camera.");
    }
  };

  const stop = () => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setCameraOn(false);
  };

  const grab = () => {
    const v = videoRef.current, c = canvasRef.current;
    c.width = v.videoWidth; c.height = v.videoHeight;
    c.getContext("2d").drawImage(v, 0, 0);
    return c.toDataURL("image/jpeg", 0.8);
  };

  const run = async () => {
    setBusy(true); setDone(false); setSeen({}); setProgress(0);
    const found = {};

    for (let i = 0; i < BURST_FRAMES; i++) {
      try {
        const res = await predictFace(grab(), classId);
        (res?.results ?? []).forEach((f) => {
          const key = f.key || f.name;
          // keep the BEST state we ever saw for a face across the burst: once someone is
          // marked present, a later frame where they turned away must not undo it
          const prev = found[key];
          if (!prev || (f.logged && !prev.logged) || f.confidence > prev.confidence) {
            found[key] = f;
          }
        });
        setSeen({ ...found });
      } catch (e) {
        console.error(e);
      }
      setProgress(i + 1);
      if (i < BURST_FRAMES - 1) await new Promise((r) => setTimeout(r, FRAME_MS));
    }
    setBusy(false); setDone(true);
  };

  const faces = Object.values(seen);
  const marked = faces.filter((f) => f.logged);
  const rejected = faces.filter((f) => !f.logged);

  return (
    <div className="min-h-screen w-full mx-auto max-w-6xl px-4 pt-20 pb-12 sm:px-6 sm:pt-24 lg:px-8">
      <div className="mb-5">
        <h1 className="display-lg text-white">Capture <span className="text-[--brand]">Attendance</span></h1>
        <p className="mt-1.5 text-sm text-[--muted]">
          Point the camera at the room and press capture. Everyone in frame is marked at once.
        </p>
      </div>

      <Card pad="p-4" className="mb-4">
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-xs font-medium text-[--muted]">Taking attendance for</span>
          <select
            value={classId}
            onChange={(e) => setClassId(e.target.value)}
            className="rounded-lg border border-white/12 bg-black/25 px-3 py-2 text-sm text-white
                       focus:border-[--brand] focus:outline-none"
          >
            <option value="">Select a class…</option>
            {classes.map((c) => (
              <option key={c.id} value={c.id}>{c.name} ({c.enrolled} enrolled)</option>
            ))}
          </select>
          {!classId && (
            <span className="text-[11px] text-amber-300">
              Pick a class — attendance is written to that class's register.
            </span>
          )}
        </div>
      </Card>

      <div className="grid gap-4 lg:grid-cols-[1.7fr_1fr] lg:items-start">
        <Card pad="p-3 sm:p-4">
          <div className="relative w-full overflow-hidden rounded-xl border border-white/10 bg-black/50"
               style={{ aspectRatio: "16/9" }}>
            <video ref={videoRef} autoPlay playsInline muted className="h-full w-full object-cover" />
            <canvas ref={canvasRef} className="hidden" />

            <AnimatePresence>
              {busy && (
                <motion.div
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                  className="absolute inset-0 grid place-items-center bg-black/55 backdrop-blur-[2px]"
                >
                  <div className="w-56 text-center">
                    <Loader2 className="mx-auto mb-3 h-6 w-6 animate-spin text-[--brand]" />
                    <p className="mb-2 text-xs font-medium text-slate-200">
                      Capturing… frame {progress} of {BURST_FRAMES}
                    </p>
                    <div className="h-1 overflow-hidden rounded-full bg-white/15">
                      <motion.div
                        className="h-full rounded-full bg-gradient-to-r from-[--brand] to-emerald-400"
                        animate={{ width: `${(progress / BURST_FRAMES) * 100}%` }}
                      />
                    </div>
                    <p className="mt-2 text-[10px] leading-relaxed text-slate-400">
                      Several frames, so a photograph can't pass.
                    </p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <div className="mt-3 flex flex-wrap gap-2">
            <Button onClick={run} disabled={!cameraOn || busy || !classId} className="flex-1">
              {busy
                ? <><Loader2 className="h-4 w-4 animate-spin" /> Capturing…</>
                : <><Camera className="h-4 w-4" /> Capture attendance</>}
            </Button>
            {done && (
              <Button variant="ghost" onClick={() => { setSeen({}); setDone(false); }}>
                <RotateCcw className="h-4 w-4" /> Again
              </Button>
            )}
          </div>

          <p className="mt-3 flex items-start gap-2 text-[11px] leading-relaxed text-slate-600">
            <ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            You cannot upload a photo here, by design — an uploaded image can't be
            liveness-checked, so one photo of the class would mark everyone present forever.
            Capture takes {BURST_FRAMES} live frames instead, and every face still has to
            pass liveness and be confirmed across three of them.
          </p>
        </Card>

        <Card pad="p-4">
          <CardTitle right={faces.length > 0 && <Badge tone="muted">{faces.length} in frame</Badge>}>
            Result
          </CardTitle>

          {!done && !busy && faces.length === 0 && (
            <Empty icon={ScanFace} title="Nothing captured yet"
                   sub="Press capture with the class in frame." />
          )}

          {(busy || faces.length > 0) && (
            <>
              <div className="mb-4 grid grid-cols-3 gap-2 text-center">
                {[["Detected", faces.length, "text-slate-200"],
                  ["Marked", marked.length, "text-emerald-300"],
                  ["Rejected", rejected.length, rejected.length ? "text-rose-300" : "text-slate-500"],
                ].map(([k, v, c]) => (
                  <div key={k} className="rounded-lg border border-white/10 bg-black/20 p-2.5">
                    <div className={`text-lg font-bold tabular-nums ${c}`}>{v}</div>
                    <div className="text-[10px] uppercase tracking-wide text-slate-600">{k}</div>
                  </div>
                ))}
              </div>

              <div className="max-h-[380px] space-y-2 overflow-y-auto pr-1">
                {faces.map((f, i) => {
                  const v = f.logged
                    ? { label: "Marked present", tone: "good", icon: CheckCircle2 }
                    : (VERDICTS[f.reason] ?? { label: "Pending", tone: "warn", icon: Loader2 });
                  const Icon = v.icon;
                  return (
                    <motion.div
                      key={f.key || i}
                      initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }}
                      className="rounded-xl border border-white/10 bg-black/20 p-3"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div className="min-w-0">
                          <div className="truncate text-sm font-semibold text-white">{f.name}</div>
                          {f.roll && (
                            <div className="truncate font-mono text-[10px] text-slate-600">
                              {f.roll}{f.class ? ` · ${f.class}` : ""}
                            </div>
                          )}
                        </div>
                        <Badge tone={v.tone} className="shrink-0">
                          <Icon className={`h-3 w-3 ${Icon === Loader2 ? "animate-spin" : ""}`} />
                          {v.label}
                        </Badge>
                      </div>
                    </motion.div>
                  );
                })}
              </div>

              {done && (
                <div className="mt-4 rounded-lg border border-white/10 bg-black/20 p-3">
                  <p className="flex items-center gap-2 text-xs text-slate-300">
                    <Users className="h-3.5 w-3.5 text-emerald-400" />
                    <span className="font-semibold text-emerald-300">{marked.length}</span>
                    marked present. Open the class to see the register.
                  </p>
                </div>
              )}
            </>
          )}
        </Card>
      </div>
    </div>
  );
}
