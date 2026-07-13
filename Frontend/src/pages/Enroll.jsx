import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  ScanFace, CheckCircle2, Loader2, TriangleAlert, Camera, IdCard,
} from "lucide-react";
import CameraCapture from "../components/CameraCapture";
import Aurora from "../components/Aurora";
import { Card, Button, Badge, Field } from "../components/ui";
import { getEnrollInfo, submitEnroll } from "../utils/api";

/**
 * PUBLIC self-enrolment — the page a student opens from the link their teacher shares.
 * No account, no password, no login.
 *
 * It is public, but it is NOT open: the roll number must already be on the roster the
 * teacher published. A stranger who merely has the link has no roll number to claim.
 * That roster is the whole security model, and it is why the link can be shared in a
 * WhatsApp group without letting outsiders add themselves as students.
 */

// The backend drops any identity with fewer than 8 embeddable images. 15 leaves headroom
// for captures where no face is found, and gives the centroid enough angles to average.
const NEEDED = 15;

export default function Enroll() {
  const { code } = useParams();
  const [info, setInfo] = useState(null);
  const [error, setError] = useState("");
  const [roll, setRoll] = useState("");
  const [images, setImages] = useState([]);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(null);

  useEffect(() => {
    getEnrollInfo(code).then(setInfo).catch((e) => setError(e.message));
  }, [code]);

  const me = info?.awaiting?.find((s) => s.roll === roll.trim());

  const submit = async () => {
    setBusy(true);
    setError("");
    try {
      setDone(await submitEnroll(code, roll.trim(), images));
    } catch (e) {
      setError(e.message);
    }
    setBusy(false);
  };

  /* ── invalid link ─────────────────────────────────────────────────────── */
  if (error && !info) {
    return (
      <Shell>
        <Card pad="p-8" className="items-center text-center">
          <TriangleAlert className="mb-3 h-8 w-8 text-rose-400" />
          <h1 className="text-lg font-semibold text-white">This link isn't valid</h1>
          <p className="mt-2 text-sm text-[--muted]">{error}</p>
        </Card>
      </Shell>
    );
  }

  if (!info) {
    return (
      <Shell>
        <Card pad="p-8" className="items-center">
          <Loader2 className="h-6 w-6 animate-spin text-[--brand]" />
        </Card>
      </Shell>
    );
  }

  /* ── enrolled ─────────────────────────────────────────────────────────── */
  if (done) {
    return (
      <Shell>
        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}>
          <Card pad="p-8" className="items-center text-center">
            <span className="mb-4 grid h-14 w-14 place-items-center rounded-2xl
                             border border-emerald-400/30 bg-emerald-500/10">
              <CheckCircle2 className="h-7 w-7 text-emerald-400" />
            </span>
            <h1 className="text-xl font-bold text-white">You're enrolled, {done.name}</h1>
            <p className="mt-2 max-w-sm text-sm text-[--muted]">
              {done.samples} images captured. The model is training now — you'll be
              recognised in class within a few seconds.
            </p>
            <p className="mt-5 text-xs text-slate-600">
              You can close this page. You do not need to do this again.
            </p>
          </Card>
        </motion.div>
      </Shell>
    );
  }

  /* ── enrol ────────────────────────────────────────────────────────────── */
  return (
    <Shell>
      <div className="mb-5 text-center">
        <Badge tone="brand" className="mb-3">
          <ScanFace className="h-3 w-3" /> Student enrolment
        </Badge>
        <h1 className="display-lg text-white">{info.class}</h1>
        <p className="mt-1.5 text-sm text-[--muted]">
          {info.enrolled} of {info.total} students enrolled
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_1.3fr] lg:items-start">
        {/* step 1 — prove who you are */}
        <Card pad="p-5">
          <div className="mb-4 flex items-center gap-2">
            <span className="grid h-6 w-6 place-items-center rounded-md bg-[--brand] text-xs font-bold text-white">1</span>
            <span className="text-sm font-semibold text-white">Your roll number</span>
          </div>

          <Field
            label="Roll number"
            value={roll}
            onChange={(e) => setRoll(e.target.value)}
            placeholder="e.g. 13000222065"
            inputMode="numeric"
          />

          <AnimatePresence mode="wait">
            {roll.trim() && (
              <motion.div
                key={me ? "ok" : "no"}
                initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                className={`mt-3 rounded-lg border p-3 text-xs ${
                  me
                    ? "border-emerald-400/30 bg-emerald-500/10 text-emerald-300"
                    : "border-rose-400/30 bg-rose-500/10 text-rose-300"
                }`}
              >
                {me ? (
                  <>Hi <span className="font-semibold">{me.name}</span> — capture your face below.</>
                ) : (
                  <>That roll number isn't on this class roster, or it has already
                    enrolled. Ask your teacher to add you.</>
                )}
              </motion.div>
            )}
          </AnimatePresence>

          <div className="mt-auto pt-5">
            <p className="flex items-start gap-2 text-[11px] leading-relaxed text-slate-600">
              <IdCard className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              Only roll numbers your teacher has added can enrol here. Your photos stay on
              the college machine — they are never uploaded to any cloud service.
            </p>
          </div>
        </Card>

        {/* step 2 — capture */}
        <Card pad="p-5">
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className={`grid h-6 w-6 place-items-center rounded-md text-xs font-bold ${
                me ? "bg-[--brand] text-white" : "bg-white/10 text-slate-500"}`}>2</span>
              <span className={`text-sm font-semibold ${me ? "text-white" : "text-slate-600"}`}>
                Capture your face
              </span>
            </div>
            <Badge tone={images.length >= NEEDED ? "good" : "muted"}>
              {images.length} / {NEEDED}
            </Badge>
          </div>

          <div className={`overflow-hidden rounded-xl border border-white/10 bg-black/40
                           ${me ? "" : "pointer-events-none opacity-40"}`}>
            <CameraCapture onCapture={(img) => setImages((p) => [...p, img])} />
          </div>

          <div className="mt-3 h-1 overflow-hidden rounded-full bg-white/10">
            <motion.div
              className="h-full rounded-full bg-gradient-to-r from-[--brand] to-emerald-400"
              animate={{ width: `${Math.min(100, (images.length / NEEDED) * 100)}%` }}
            />
          </div>
          <p className="mt-2 text-[11px] text-slate-600">
            Turn your head slowly left and right while capturing — different angles make
            the model far more reliable than {NEEDED} near-identical photos.
          </p>

          {images.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {images.slice(-10).map((img, i) => (
                <motion.img
                  key={i} src={img} initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }}
                  className="h-9 w-9 rounded-md border border-white/12 object-cover"
                />
              ))}
            </div>
          )}

          {error && (
            <p className="mt-3 rounded-lg border border-rose-400/30 bg-rose-500/10 p-2.5
                          text-xs text-rose-300">{error}</p>
          )}

          <Button
            className="mt-4 w-full"
            size="lg"
            disabled={!me || images.length < NEEDED || busy}
            onClick={submit}
          >
            {busy ? (
              <><Loader2 className="h-4 w-4 animate-spin" /> Enrolling…</>
            ) : (
              <><Camera className="h-4 w-4" /> Enrol{me ? ` as ${me.name.split(" ")[0]}` : ""}</>
            )}
          </Button>
        </Card>
      </div>
    </Shell>
  );
}

function Shell({ children }) {
  return (
    <div className="relative flex min-h-screen items-center justify-center px-5 py-12">
      <Aurora />
      <div className="relative z-10 w-full max-w-4xl">{children}</div>
    </div>
  );
}
