import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import axios from "axios";
import {
  ScanFace, CheckCircle2, HelpCircle, EyeOff, Ruler, Loader2, Users,
} from "lucide-react";
import CameraCapture from "../components/CameraCapture";
import { Card, CardTitle, Badge, Empty } from "../components/ui";

/**
 * A face can be recognized and STILL not be marked present — it has to clear the size,
 * threshold, margin and liveness gates first. The old UI collapsed all of that into
 * "Recognized / Unknown", which hid the single most interesting thing the system does.
 * Each gate now gets its own verdict, so a rejected face says WHY.
 */
function verdict(r) {
  if (r.reason === "face_too_small")
    return { label: "Too far away", tone: "warn", icon: Ruler,
             note: `face is ${r.faceWidth}px wide — needs 40px` };
  if (r.reason === "low_detection_quality")
    return { label: "Poor detection", tone: "warn", icon: HelpCircle,
             note: "face the camera, check the lighting" };
  if (r.reason === "below_threshold")
    return { label: "Unknown", tone: "bad", icon: HelpCircle,
             note: "no enrolled student is close enough" };
  if (r.reason === "ambiguous")
    return { label: "Ambiguous", tone: "warn", icon: HelpCircle,
             note: `too close to call: ${(r.candidates || []).join(" / ")}` };
  if (r.reason === "checking")
    return { label: "Verifying liveness", tone: "brand", icon: Loader2,
             note: "watching for facial motion — a photo can't move" };
  if (r.reason === "spoof_suspected")
    return { label: "Not live", tone: "bad", icon: EyeOff,
             note: "rigid face — this looks like a photograph" };
  if (r.logged)
    return { label: "Marked present", tone: "good", icon: CheckCircle2,
             note: "identity and liveness both confirmed" };
  return { label: "Recognized", tone: "good", icon: CheckCircle2,
           note: "awaiting enough frames to commit" };
}

const barTone = (c) =>
  c >= 0.5 ? "bg-emerald-400" : c >= 0.3 ? "bg-amber-400" : "bg-rose-400";

function FaceRow({ r, i }) {
  const v = verdict(r);
  const Icon = v.icon;
  const pct = Math.round((r.confidence || 0) * 100);

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: i * 0.05 }}
      className="rounded-xl border border-white/10 bg-black/20 p-3.5"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg
                           bg-gradient-to-br from-[--brand]/30 to-violet-500/25
                           text-sm font-bold text-white">
            {(r.name || "?").charAt(0).toUpperCase()}
          </span>
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold text-white">{r.name}</div>
            <div className="mt-0.5 truncate text-[11px] text-slate-500">{v.note}</div>
          </div>
        </div>
        <Badge tone={v.tone} className="shrink-0">
          <Icon className={`h-3 w-3 ${v.icon === Loader2 ? "animate-spin" : ""}`} />
          {v.label}
        </Badge>
      </div>

      {/* cosine similarity to the matched centroid — the number the decision rests on */}
      <div className="mt-3 flex items-center gap-2.5">
        <div className="h-1 flex-1 overflow-hidden rounded-full bg-white/10">
          <motion.div
            className={`h-full rounded-full ${barTone(r.confidence)}`}
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(pct, 100)}%` }}
            transition={{ duration: 0.6, delay: i * 0.05 }}
          />
        </div>
        <span className="w-9 text-right font-mono text-[11px] tabular-nums text-slate-400">
          {pct}%
        </span>
      </div>

      <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 font-mono text-[10px] text-slate-600">
        <span>cos {(r.confidence ?? 0).toFixed(3)}</span>
        {r.margin != null && <span>margin {r.margin.toFixed(3)}</span>}
        {r.faceWidth != null && <span>{r.faceWidth}px</span>}
        {r.det_score != null && <span>det {r.det_score}</span>}
      </div>
    </motion.div>
  );
}

export default function Attendance() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [scanned, setScanned] = useState(false);

  const handleCapture = async (img) => {
    try {
      setLoading(true);
      const res = await axios.post("http://127.0.0.1:5000/predict", { image: img });
      setResults(res.data.results || []);
      setScanned(true);
    } catch (err) {
      console.error("Prediction failed:", err.response?.data || err.message);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const present = results.filter((r) => r.logged).length;
  const known = results.filter((r) => r.isKnown).length;

  return (
    <div className="min-h-screen w-full mx-auto max-w-6xl px-5 sm:px-8 pt-24 pb-16">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="display-lg text-white">
            Attendance <span className="text-[--brand]">Scanner</span>
          </h1>
          <p className="mt-1.5 text-sm text-[--muted]">
            Capture a frame — every face in it is detected, identified and liveness-checked.
          </p>
        </div>
        {results.length > 0 && (
          <div className="flex gap-2">
            <Badge tone="muted"><Users className="h-3 w-3" />{results.length} detected</Badge>
            <Badge tone="good"><CheckCircle2 className="h-3 w-3" />{present} marked</Badge>
          </div>
        )}
      </div>

      {/* camera left, verdicts right — the results are the point, so they get real estate */}
      <div className="grid gap-4 lg:grid-cols-[1.35fr_1fr] lg:items-start">
        <Card pad="p-4" className="relative">
          <div className="relative overflow-hidden rounded-xl border border-white/10 bg-black/40">
            <CameraCapture onCapture={handleCapture} loading={loading} />
            <AnimatePresence>
              {loading && (
                <motion.div
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                  className="absolute inset-0 grid place-items-center bg-black/60 backdrop-blur-sm"
                >
                  <div className="flex flex-col items-center gap-2.5">
                    <Loader2 className="h-6 w-6 animate-spin text-[--brand]" />
                    <span className="text-xs font-medium text-slate-300">
                      Detecting, embedding, matching…
                    </span>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </Card>

        <Card pad="p-4">
          <CardTitle right={known > 0 && <Badge tone="brand">{known} identified</Badge>}>
            Detection results
          </CardTitle>

          {loading ? (
            <div className="flex flex-col items-center justify-center py-14">
              <Loader2 className="mb-3 h-5 w-5 animate-spin text-[--brand]" />
              <p className="text-xs text-[--muted]">Processing frame…</p>
            </div>
          ) : results.length === 0 ? (
            <Empty
              icon={ScanFace}
              title={scanned ? "No faces found in that frame" : "Nothing scanned yet"}
              sub={scanned
                ? "Move into the frame and try again."
                : "Capture a frame to detect and identify every face in it."}
            />
          ) : (
            <>
              <div className="scroll-x max-h-[420px] space-y-2.5 overflow-y-auto pr-1">
                {results.map((r, i) => <FaceRow key={i} r={r} i={i} />)}
              </div>

              <div className="mt-4 grid grid-cols-3 gap-2 border-t border-white/10 pt-3.5 text-center">
                {[
                  ["Detected", results.length, "text-slate-200"],
                  ["Identified", known, "text-sky-300"],
                  ["Marked", present, "text-emerald-300"],
                ].map(([k, v, c]) => (
                  <div key={k}>
                    <div className={`text-base font-bold tabular-nums ${c}`}>{v}</div>
                    <div className="text-[10px] uppercase tracking-wide text-slate-600">{k}</div>
                  </div>
                ))}
              </div>
            </>
          )}
        </Card>
      </div>
    </div>
  );
}
