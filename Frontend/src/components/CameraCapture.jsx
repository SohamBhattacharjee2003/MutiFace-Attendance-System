import React, { useRef } from "react";
import Webcam from "react-webcam";
import { motion } from "framer-motion";

export default function CameraCapture({ onCapture }) {
  const ref = useRef(null);

  const capture = () => {
    const imgSrc = ref.current.getScreenshot();
    onCapture(imgSrc);
  };

  return (
    <div className="flex flex-col items-center gap-6">
      {/* CAMERA FEED */}
      <div
        className="
          w-full overflow-hidden rounded-2xl 
          border border-blue-500/20 
          shadow-[0_0_25px_rgba(0,110,255,0.25)]
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
      </div>

      {/* Capture Button */}
      <motion.button
        whileTap={{ scale: 0.95 }}
        onClick={capture}
        className="
          w-full py-4 
          bg-blue-600 hover:bg-blue-700 
          text-white text-lg font-semibold 
          rounded-xl transition 
          shadow-[0_0_25px_rgba(0,110,255,0.45)]
        "
      >
        Capture Image
      </motion.button>
    </div>
  );
}
