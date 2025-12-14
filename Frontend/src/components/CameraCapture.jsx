import React, { useRef } from "react";
import Webcam from "react-webcam";
import { motion } from "framer-motion";

export default function CameraCapture({ onCapture, loading = false }) {
  const ref = useRef(null);

  const capture = () => {
    if (loading) return; // Prevent capture while processing
    const imgSrc = ref.current.getScreenshot();
    if (imgSrc) {
      onCapture(imgSrc);
    }
  };

  return (
    <div className="flex flex-col items-center gap-6">
      {/* CAMERA FEED */}
      <div
        className="
          w-full overflow-hidden rounded-2xl 
          border border-blue-500/20 
          shadow-[0_0_25px_rgba(0,110,255,0.25)]
          relative
        "
      >
        <Webcam
          ref={ref}
          mirrored
          screenshotFormat="image/jpeg"
          videoConstraints={{
            width: 1280,
            height: 720,
            facingMode: "user",
          }}
          className="w-full rounded-2xl"
        />
        
        {/* Recording indicator */}
        <div className="absolute top-4 right-4 flex items-center gap-2 bg-black/50 backdrop-blur-sm px-3 py-2 rounded-full">
          <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
          <span className="text-white text-sm font-medium">LIVE</span>
        </div>
      </div>

      {/* Capture Button */}
      <motion.button
        whileHover={{ scale: loading ? 1 : 1.02 }}
        whileTap={{ scale: loading ? 1 : 0.95 }}
        onClick={capture}
        disabled={loading}
        className={`
          w-full py-4 
          text-white text-lg font-semibold 
          rounded-xl transition-all
          shadow-[0_0_25px_rgba(0,110,255,0.45)]
          flex items-center justify-center gap-3
          ${loading 
            ? 'bg-gray-600 cursor-not-allowed opacity-70' 
            : 'bg-blue-600 hover:bg-blue-700 cursor-pointer'
          }
        `}
      >
        {loading ? (
          <>
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            Processing...
          </>
        ) : (
          <>
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Capture & Detect Faces
          </>
        )}
      </motion.button>
    </div>
  );
}
