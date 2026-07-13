import React, { useRef, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Camera, StopCircle, Video, VideoOff, Play, ScanFace } from "lucide-react";
import { predictFace } from "../utils/api";
import { Card, CardTitle, Badge, Button, Empty } from "../components/ui";

export default function LiveAttendance() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);          // reliable handle for cleanup
  const intervalRef = useRef(null);
  const busyRef = useRef(false);           // prevents overlapping predict calls
  const [isAttendanceActive, setIsAttendanceActive] = useState(false);
  const [detectedFaces, setDetectedFaces] = useState([]);
  const [cameraOn, setCameraOn] = useState(true);

  useEffect(() => {
    startCamera();
    return () => {
      stopCamera();
      stopAttendance();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { width: 1280, height: 720 },
      });
      streamRef.current = mediaStream;
      if (videoRef.current) videoRef.current.srcObject = mediaStream;
      setCameraOn(true);
    } catch (err) {
      console.error("Camera error:", err);
      alert("Could not access camera");
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (videoRef.current) videoRef.current.srcObject = null;
    setCameraOn(false);
  };

  const toggleCamera = () => {
    if (cameraOn) {
      stopAttendance();     // can't scan without a camera
      stopCamera();
    } else {
      startCamera();
    }
  };

  const startAttendance = () => {
    if (!cameraOn) { alert("Turn the camera on first."); return; }
    setIsAttendanceActive(true);
    setDetectedFaces([]);

    // 700ms, not 1500ms. Measured (scripts/benchmark.py): one face costs ~250ms end to
    // end, so 1.5s was leaving the CPU idle most of the time — and it was the reason
    // marking someone present took ~10s (liveness needs several frames, then voting needs
    // several more). The busy-guard drops a frame rather than queueing if the backend is
    // still working, so a slower machine degrades gracefully instead of piling up.
    intervalRef.current = setInterval(() => {
      captureAndPredict();
    }, 700);
  };

  const stopAttendance = () => {
    setIsAttendanceActive(false);
    setDetectedFaces([]);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  const captureAndPredict = async () => {
    if (!videoRef.current || !canvasRef.current) return;
    if (busyRef.current || !streamRef.current) return;   // skip if a request is in flight
    busyRef.current = true;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);

    const base64Image = canvas.toDataURL("image/jpeg", 0.8);

    try {
      const response = await predictFace(base64Image);
      if (response?.results) {
        setDetectedFaces(response.results);
      }
    } catch (err) {
      console.error("Prediction error:", err);
    } finally {
      busyRef.current = false;
    }
  };

  const drawFaceBoxes = () => {
    if (!videoRef.current || detectedFaces.length === 0) return null;

    const video = videoRef.current;
    const videoWidth = video.offsetWidth;
    const videoHeight = video.offsetHeight;
    const scaleX = videoWidth / video.videoWidth;
    const scaleY = videoHeight / video.videoHeight;

    return detectedFaces.map((face, index) => {
      const [x1, y1, x2, y2] = face.box;
      const left = x1 * scaleX;
      const top = y1 * scaleY;
      const width = (x2 - x1) * scaleX;
      const height = (y2 - y1) * scaleY;

      // A face can be recognized but still NOT marked present — it must also pass the
      // liveness check (a photo held to the camera recognizes perfectly but never blinks).
      // Green is reserved for "actually logged"; amber means "we know you, now blink".
      const isKnown = face.isKnown;
      const pending = isKnown && face.logged === false;
      const color = !isKnown ? "#ef4444" : pending ? "#f59e0b" : "#10b981";

      // Liveness needs a few frames of facial motion before it can tell a person from a
      // photo, so "checking" is a normal transient state, not a failure.
      const label = !isKnown
        ? face.name                                     // Unknown / Move closer / Uncertain
        : face.reason === "checking"
          ? `${face.name} — verifying…`
          : face.reason === "spoof_suspected"
            ? `${face.name} — not live (photo?)`
            : `${face.name} (${Math.round(face.confidence * 100)}%)`;

      return (
        <div
          key={index}
          style={{
            position: "absolute",
            left: `${left}px`,
            top: `${top}px`,
            width: `${width}px`,
            height: `${height}px`,
            border: `2px solid ${color}`,
            borderRadius: "6px",
            boxShadow: `0 0 12px ${color}55`,
            pointerEvents: "none",
            zIndex: 10,
          }}
        >
          <div
            style={{
              position: "absolute",
              top: "-24px",
              left: "-1px",
              background: color,
              color: "#04070f",
              padding: "2px 8px",
              borderRadius: "5px",
              fontSize: "11px",
              fontWeight: 700,
              whiteSpace: "nowrap",
            }}
          >
            {label}
          </div>
        </div>
      );
    });
  };

  const known = detectedFaces.filter((f) => f.isKnown).length;
  const logged = detectedFaces.filter((f) => f.logged).length;

  return (
    <div className="min-h-screen w-full mx-auto max-w-[1500px] px-4 pt-20 pb-12 sm:px-6 sm:pt-24 sm:pb-16 lg:px-8">
      {/* header: title + controls on one line — it was a full-height hero before */}
      <Card pad="p-4" className="mb-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="grid h-10 w-10 place-items-center rounded-lg bg-gradient-to-br from-[--brand] to-violet-500">
              <Camera className="h-5 w-5 text-white" />
            </span>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-white">Live Face Attendance</h1>
              <p className="mt-0.5 text-xs text-[--muted]">
                {isAttendanceActive ? (
                  <span className="inline-flex items-center gap-1.5">
                    <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
                    Scanning ~1.4×/sec — every face in frame
                  </span>
                ) : (
                  "Start to begin marking attendance"
                )}
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {!isAttendanceActive ? (
              <Button onClick={startAttendance} disabled={!cameraOn}>
                <Play className="h-4 w-4" /> Start attendance
              </Button>
            ) : (
              <Button variant="danger" onClick={stopAttendance}>
                <StopCircle className="h-4 w-4" /> Stop
              </Button>
            )}
            <Button variant="ghost" onClick={toggleCamera}>
              {cameraOn ? <VideoOff className="h-4 w-4" /> : <Video className="h-4 w-4" />}
              {cameraOn ? "Camera off" : "Camera on"}
            </Button>
          </div>
        </div>
      </Card>

      <div className="grid gap-4 lg:grid-cols-[2fr_minmax(300px,1fr)] lg:items-start">
        {/* video: capped by aspect ratio, not left to fill the viewport */}
        <Card pad="p-3">
          <div className="relative w-full overflow-hidden rounded-xl border border-white/10 bg-black/50"
               style={{ aspectRatio: "16/9" }}>
            <video ref={videoRef} autoPlay playsInline muted
                   className="h-full w-full object-cover" />
            {isAttendanceActive && (
              <div className="pointer-events-none absolute inset-0">{drawFaceBoxes()}</div>
            )}
            {!cameraOn && (
              <div className="absolute inset-0 flex flex-col items-center justify-center gap-2.5 bg-black/70">
                <VideoOff className="h-8 w-8 text-slate-600" />
                <p className="text-xs text-slate-500">Camera is off</p>
              </div>
            )}
            {isAttendanceActive && (
              <div className="absolute left-3 top-3 inline-flex items-center gap-1.5 rounded-full
                              bg-black/70 px-2.5 py-1 text-[10px] font-semibold text-rose-300 backdrop-blur">
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-rose-500" /> LIVE
              </div>
            )}
          </div>
          <canvas ref={canvasRef} className="hidden" />

          <div className="mt-3 flex flex-wrap items-center justify-center gap-4 text-[11px] text-slate-500">
            {[["#10b981", "Marked present"], ["#f59e0b", "Verifying liveness"], ["#ef4444", "Unknown / not live"]]
              .map(([c, label]) => (
                <span key={label} className="inline-flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-sm" style={{ background: c }} />
                  {label}
                </span>
              ))}
          </div>
        </Card>

        {/* the live verdicts — this is what the operator actually watches */}
        <Card pad="p-4">
          <CardTitle right={
            detectedFaces.length > 0 && <Badge tone="muted">{detectedFaces.length} in frame</Badge>
          }>
            Live detections
          </CardTitle>

          {!isAttendanceActive ? (
            <Empty icon={ScanFace} title="Not scanning"
                   sub="Press Start — every face in the frame is detected and checked for liveness." />
          ) : detectedFaces.length === 0 ? (
            <Empty icon={ScanFace} title="No faces in frame"
                   sub="Step into view. Faces under 40px wide are refused rather than guessed at." />
          ) : (
            <>
              <div className="max-h-[46vh] min-h-[180px] space-y-2 overflow-y-auto pr-1">
                {detectedFaces.map((f, i) => {
                  const tone = !f.isKnown ? "bad" : f.logged ? "good" : "warn";
                  const status = !f.isKnown
                    ? f.name
                    : f.logged
                      ? "Marked present"
                      : f.reason === "spoof_suspected"
                        ? "Not live — photo?"
                        : "Verifying liveness…";
                  return (
                    <motion.div key={i}
                      initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }}
                      className="flex items-center justify-between gap-3 rounded-xl border border-white/10 bg-black/20 p-3">
                      <div className="flex min-w-0 items-center gap-2.5">
                        <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg
                                         bg-gradient-to-br from-[--brand]/30 to-violet-500/25 text-xs font-bold">
                          {(f.name || "?").charAt(0).toUpperCase()}
                        </span>
                        <div className="min-w-0">
                          <div className="truncate text-sm font-semibold text-white">{f.name}</div>
                          <div className="truncate text-[10px] text-slate-500">{status}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-mono text-xs tabular-nums text-slate-300">
                          {Math.round((f.confidence || 0) * 100)}%
                        </div>
                        <Badge tone={tone} className="mt-1">
                          {f.logged ? "present" : f.isKnown ? "pending" : "rejected"}
                        </Badge>
                      </div>
                    </motion.div>
                  );
                })}
              </div>

              <div className="mt-4 grid grid-cols-3 gap-2 border-t border-white/10 pt-3.5 text-center">
                {[["In frame", detectedFaces.length, "text-slate-200"],
                  ["Identified", known, "text-sky-300"],
                  ["Marked", logged, "text-emerald-300"]].map(([k, v, c]) => (
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
