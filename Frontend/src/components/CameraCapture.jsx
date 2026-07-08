import React, { useRef, useState, useEffect } from "react";
import Webcam from "react-webcam";
import { motion } from "framer-motion";
import { FiCamera, FiVideo, FiVideoOff } from "react-icons/fi";

export default function CameraCapture({ onCapture, loading = false }) {
  const ref = useRef(null);
  const [camOn, setCamOn] = useState(true);

  const capture = () => {
    if (loading || !camOn || !ref.current) return;
    const imgSrc = ref.current.getScreenshot();
    if (imgSrc) onCapture(imgSrc);
  };

  const toggleCamera = () => {
    if (camOn) {
      // explicitly stop the physical camera (react-webcam won't always release it)
      const stream = ref.current && ref.current.stream;
      if (stream) stream.getTracks().forEach((t) => t.stop());
      if (ref.current && ref.current.video) ref.current.video.srcObject = null;
    }
    setCamOn((v) => !v);
  };

  // ensure the camera is released if this component unmounts (page change)
  useEffect(() => {
    return () => {
      const stream = ref.current && ref.current.stream;
      if (stream) stream.getTracks().forEach((t) => t.stop());
    };
  }, []);

  return (
    <div className="flex flex-col items-center gap-4 w-full">
      {/* CAMERA FEED / PLACEHOLDER */}
      <div className="w-full aspect-video overflow-hidden rounded-2xl border border-blue-500/20
                      bg-[#05070f] shadow-[0_0_25px_rgba(0,110,255,0.20)] relative">
        {camOn ? (
          <>
            <Webcam
              ref={ref}
              mirrored
              audio={false}
              screenshotFormat="image/jpeg"
              videoConstraints={{ facingMode: "user" }}
              className="w-full h-full object-cover"
            />
            <div className="absolute top-3 right-3 flex items-center gap-2 bg-black/50 backdrop-blur-sm px-3 py-1.5 rounded-full">
              <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
              <span className="text-white text-xs font-medium">LIVE</span>
            </div>
          </>
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center text-white/40 gap-3">
            <FiVideoOff className="w-12 h-12" />
            <p className="text-sm">Camera is off</p>
          </div>
        )}
      </div>

      {/* CONTROLS */}
      <div className="flex flex-col sm:flex-row gap-3 w-full">
        <motion.button
          whileTap={{ scale: camOn && !loading ? 0.97 : 1 }}
          onClick={capture}
          disabled={loading || !camOn}
          className={`flex-1 py-3.5 rounded-xl font-semibold flex items-center justify-center gap-2
            transition-all shadow-[0_0_20px_rgba(0,110,255,0.35)]
            ${loading || !camOn
              ? "bg-gray-600/60 cursor-not-allowed opacity-70"
              : "bg-blue-600 hover:bg-blue-700 text-white"}`}
        >
          {loading ? (
            <>
              <span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Processing…
            </>
          ) : (
            <><FiCamera className="w-5 h-5" /> Capture &amp; Detect</>
          )}
        </motion.button>

        <button
          onClick={toggleCamera}
          className={`sm:w-48 py-3.5 rounded-xl font-semibold flex items-center justify-center gap-2
            border transition-colors
            ${camOn
              ? "border-red-400/30 text-red-300 hover:bg-red-500/10"
              : "border-emerald-400/30 text-emerald-300 hover:bg-emerald-500/10"}`}
        >
          {camOn ? <><FiVideoOff className="w-5 h-5" /> Turn Camera Off</>
                 : <><FiVideo className="w-5 h-5" /> Turn Camera On</>}
        </button>
      </div>
    </div>
  );
}
