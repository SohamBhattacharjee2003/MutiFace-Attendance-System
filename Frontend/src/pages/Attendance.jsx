import React, { useState } from "react";
import CameraCapture from "../components/CameraCapture";
import axios from "axios";
import { motion } from "framer-motion";

export default function Attendance() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleCapture = async (img) => {
    try {
      setLoading(true);
      const res = await axios.post("http://127.0.0.1:5000/predict", { image: img });
      setResults(res.data.results || []);
    } catch (error) {
      console.log("Error:", error);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen px-6 md:px-16 mt-24 mb-20 relative overflow-hidden text-white bg-[#070c24]">

      {/* Background Glows */}
      <div className="absolute w-[600px] h-[600px] bg-blue-900/20 blur-[200px] -top-32 left-10 rounded-full" />
      <div className="absolute w-[500px] h-[500px] bg-indigo-800/20 blur-[200px] bottom-10 right-10 rounded-full" />

      {/* Title */}
      <motion.h2
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-4xl font-bold text-center tracking-wide"
      >
        AI Attendance Scanner
      </motion.h2>

      <p className="text-gray-400 text-center mt-2">
        Capture your image and let PresenceAI detect & mark attendance.
      </p>

      {/* CAMERA BOX */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="
          max-w-4xl mx-auto bg-white/5 backdrop-blur-xl 
          border border-white/10 rounded-2xl p-8 mt-10
          shadow-[0_0_30px_rgba(0,110,255,0.2)]
        "
      >
        {/* Camera Component */}
        <CameraCapture onCapture={handleCapture} />

        {/* Animated Border */}
        <motion.div
          className="absolute inset-0 border-2 border-blue-500/20 rounded-2xl pointer-events-none"
          animate={{ opacity: [0.3, 1, 0.3] }}
          transition={{ duration: 2, repeat: Infinity }}
        />
      </motion.div>

      {/* RESULTS SECTION */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="
          max-w-4xl mx-auto bg-white/5 backdrop-blur-xl 
          border border-white/10 rounded-2xl p-6 mt-10
          shadow-[0_0_25px_rgba(255,255,255,0.05)]
        "
      >
        <h3 className="text-xl font-bold mb-4">Detected Faces</h3>

        {results.length === 0 ? (
          <p className="text-gray-400">No faces detected yet.</p>
        ) : (
          <div className="space-y-3">
            {results.map((r, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex justify-between items-center bg-white/5 border border-white/10 p-4 rounded-xl"
              >
                <span className="text-lg font-medium">{r.name}</span>
                <span className="text-blue-400 text-xl font-bold">
                  {Math.round(r.confidence * 100)}%
                </span>
              </motion.div>
            ))}
          </div>
        )}
      </motion.div>
    </div>
  );
}
