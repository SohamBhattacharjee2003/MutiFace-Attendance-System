import React, { useState } from "react";
import { motion } from "framer-motion";
import CameraCapture from "../components/CameraCapture";
import axios from "axios";

export default function RegisterStudent() {
  const [name, setName] = useState("");
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const handleCapture = (img) => {
    setImages((prev) => [...prev, img]);
  };

  const registerNow = async () => {
    if (!name || images.length < 5) {
      alert("Please enter a name & capture at least 5 images.");
      return;
    }

    setLoading(true);
    try {
      await axios.post("http://127.0.0.1:5001/register-student", {
        name,
        images,
      });

      setMsg("🎉 Student registered successfully! Retrain model.");
      setName("");
      setImages([]);
    } catch (err) {
      console.error(err);
      setMsg("❌ Error registering student.");
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-[#060b23] px-10 py-10 relative overflow-hidden">

      {/* Background Glow */}
      <div className="absolute w-[900px] h-[900px] bg-blue-900/20 blur-[200px] -top-40 -left-40 rounded-full"></div>
      <div className="absolute w-[700px] h-[700px] bg-purple-600/10 blur-[200px] bottom-0 right-0 rounded-full"></div>

      <motion.h1
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-white text-4xl font-bold mb-12"
      >
        Register <span className="text-blue-400">New Student</span>
      </motion.h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">

        {/* --------- LEFT: CAMERA PANEL --------- */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="relative p-6 bg-white/10 border border-blue-400/40 backdrop-blur-xl rounded-2xl shadow-[0_0_25px_rgba(0,150,255,0.5)]"
        >
          <h2 className="text-2xl text-white font-semibold mb-6">
            Capture Images (5+)
          </h2>

          <div className="rounded-xl overflow-hidden border border-white/20 shadow-lg">
            <CameraCapture onCapture={handleCapture} />
          </div>

          {/* Image Count */}
          <p className="mt-4 text-blue-300 font-medium">
            Captured Images: {images.length}
          </p>

          {/* Thumbnails */}
          <div className="mt-4 flex flex-wrap gap-3">
            {images.map((img, i) => (
              <motion.img
                key={i}
                src={img}
                className="w-20 h-20 rounded-lg border border-white/20 shadow-[0_0_10px_rgba(255,255,255,0.3)] object-cover"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
              />
            ))}
          </div>
        </motion.div>

        {/* --------- RIGHT: FORM PANEL --------- */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="p-8 bg-white/10 border border-white/20 backdrop-blur-xl rounded-2xl shadow-[0_0_25px_rgba(255,255,255,0.2)]"
        >
          <h2 className="text-2xl text-white font-semibold mb-6">
            Student Details
          </h2>

          {/* Name Input */}
          <input
            type="text"
            placeholder="Enter student name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full p-3 rounded-lg bg-[#0a1130] text-white border border-blue-400/40 focus:ring-2 focus:ring-blue-500 outline-none"
          />

          {/* Register Button */}
          <motion.button
            whileTap={{ scale: 0.95 }}
            onClick={registerNow}
            disabled={loading}
            className="mt-6 w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-[0_0_20px_rgba(0,150,255,0.5)]"
          >
            {loading ? "Registering..." : "Register Student"}
          </motion.button>

          {/* Status Message */}
          {msg && (
            <p className="mt-4 text-center text-blue-300 font-medium">
              {msg}
            </p>
          )}
        </motion.div>
      </div>
    </div>
  );
}
