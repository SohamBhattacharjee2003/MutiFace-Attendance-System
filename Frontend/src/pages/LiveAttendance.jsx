import React, { useState } from "react";
import { motion } from "framer-motion";
import CameraCapture from "../components/CameraCapture";
import FaceBoxOverlay from "../components/FaceBoxOverlay";
import axios from "axios";

export default function LiveAttendance() {
  const [faces, setFaces] = useState([]); // multiple face results
  const [loading, setLoading] = useState(false);

  const handleFrame = async (img) => {
    try {
      const res = await axios.post("http://127.0.0.1:5001/predict", {
        image: img,
      });

      // backend returns { results: [...] }
      setFaces(res.data.results || []);
    } catch (err) {
      console.error("Prediction error:", err);
    }
  };

  return (
    <div className="min-h-screen bg-[#060b23] px-10 py-10 relative overflow-hidden">

      {/* Background Glow Effects */}
      <div className="absolute w-[700px] h-[700px] bg-blue-900/20 blur-[180px] -top-40 left-10 rounded-full"></div>
      <div className="absolute w-[600px] h-[600px] bg-cyan-500/10 blur-[200px] bottom-0 right-0 rounded-full"></div>

      <motion.h1
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-white text-4xl font-bold text-center mb-10"
      >
        Live <span className="text-blue-400">Attendance Scanner</span>
      </motion.h1>

      <div className="flex flex-col items-center justify-center">

        {/* CAMERA SECTION */}
        <div className="relative w-[720px] h-[520px] rounded-2xl overflow-hidden border border-blue-500/40 shadow-[0_0_30px_rgba(0,150,255,0.4)] bg-[#0a1130]/40 backdrop-blur-lg">

          {/* CAMERA FEED */}
          <CameraCapture onFrame={handleFrame} />

          {/* FACE BOX OVERLAY (MULTIPLE FACES) */}
          <FaceBoxOverlay faces={faces} />

          {/* Scanning Animation */}
          <div className="absolute inset-0 pointer-events-none opacity-40">
            <div className="w-full h-full bg-[linear-gradient(transparent_90%,rgba(0,150,255,0.3)_100%)] animate-scan"></div>
          </div>
        </div>

        {/* RESULT PANEL */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-8 p-5 w-[720px] bg-white/10 border border-white/20 backdrop-blur-xl rounded-xl shadow-[0_0_20px_rgba(255,255,255,0.2)]"
        >
          {faces.length > 0 ? (
            <div>
              {faces.map((f, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between px-4 py-2 border-b border-white/10"
                >
                  <div>
                    <p className="text-white text-lg font-semibold">
                      Name: <span className="text-blue-400">{f.name}</span>
                    </p>
                    <p className="text-white text-sm opacity-80">
                      Confidence: {(f.confidence * 100).toFixed(1)}%
                    </p>
                  </div>

                  <motion.div
                    animate={{ scale: [1, 1.1, 1] }}
                    transition={{ repeat: Infinity, duration: 1.5 }}
                    className="px-5 py-2 bg-green-600 rounded-lg text-white text-lg font-bold shadow-[0_0_15px_rgba(0,255,0,0.5)]"
                  >
                    PRESENT
                  </motion.div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-white text-center opacity-60">
              No face detected… scanning...
            </p>
          )}
        </motion.div>
      </div>

      {/* SCANNING ANIMATION */}
      <style>
        {`
          @keyframes scan {
            0% { background-position-y: 0; }
            100% { background-position-y: 520px; }
          }
          .animate-scan {
            animation: scan 3s linear infinite;
          }
        `}
      </style>
    </div>
  );
}
