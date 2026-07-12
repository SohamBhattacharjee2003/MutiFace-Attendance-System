import React, { useState } from "react";
import { motion } from "framer-motion";
import CameraCapture from "../components/CameraCapture";
import { getTrainingStatus } from "../utils/api";
import axios from "axios";

// The backend drops any identity with fewer than 8 embeddable images, so a student
// registered with fewer would be saved to disk but never enter the model.
const MIN_IMAGES = 10;

export default function RegisterStudent() {
  const [name, setName] = useState("");
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const handleCapture = (img) => {
    setImages((prev) => [...prev, img]);
  };

  // Registering only writes images to disk; the student isn't recognizable until the
  // retrain it kicks off finishes. Poll so the UI says "ready" only when it's true.
  const waitForTraining = async (student) => {
    for (let i = 0; i < 150; i++) {          // ~5 min ceiling
      await new Promise((r) => setTimeout(r, 2000));
      try {
        const s = await getTrainingStatus();
        if (s.status === "training") {
          setMsg(`⏳ Training the model… ${s.message || ""}`);
        } else if (s.status === "done") {
          const dropped = (s.skipped || []).find((x) => x.name === student);
          if (dropped) {
            setMsg(`⚠️ ${student} was saved but left out of the model (${dropped.reason}). Add more images.`);
          } else {
            setMsg(`✅ ${student} is trained in and can be recognized now (${s.identities} identities).`);
          }
          return;
        } else if (s.status === "error") {
          setMsg(`❌ Training failed: ${s.message}`);
          return;
        }
      } catch {
        /* keep polling — the server may be busy embedding */
      }
    }
    setMsg("⚠️ Training is taking unusually long. Check the server logs.");
  };

  const registerNow = async () => {
    if (!name || images.length < MIN_IMAGES) {
      alert(`Please enter a name & capture at least ${MIN_IMAGES} images.`);
      return;
    }

    setLoading(true);
    const student = name;
    try {
      await axios.post("http://127.0.0.1:5000/register", {
        name: student,
        images,
      });

      setMsg(`🎉 ${student} registered. Training the model…`);
      setName("");
      setImages([]);
      await waitForTraining(student);
    } catch (err) {
      console.error(err);
      setMsg("❌ Error registering student.");
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen w-full mx-auto max-w-[1400px] px-5 sm:px-8 pt-24 pb-16 relative">

      <motion.h1
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="display-lg text-white mb-8"
      >
        Register <span className="text-blue-400">New Student</span>
      </motion.h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 items-start">

        {/* --------- LEFT: CAMERA PANEL --------- */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="card-glass p-5"
        >
          <h2 className="text-sm font-semibold uppercase tracking-wide text-white/90 mb-4">
            Capture images ({MIN_IMAGES}+ needed)
          </h2>

          <div className="rounded-xl overflow-hidden border border-white/20 shadow-lg">
            <CameraCapture onCapture={handleCapture} />
          </div>

          {/* Image Count */}
          <p className="mt-4 text-xs text-[--muted]">
            Captured Images: {images.length}
          </p>

          {/* Thumbnails */}
          <div className="mt-4 flex flex-wrap gap-3">
            {images.map((img, i) => (
              <motion.img
                key={i}
                src={img}
                className="h-14 w-14 rounded-lg border border-white/12 object-cover"
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
          className="card-glass p-5"
        >
          <h2 className="text-sm font-semibold uppercase tracking-wide text-white/90 mb-4">
            Student details
          </h2>

          {/* Name Input */}
          <input
            type="text"
            placeholder="Enter student name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-lg border border-white/12 bg-black/25 px-3.5 py-2.5 text-sm text-white placeholder:text-slate-500 focus:border-[--brand] focus:outline-none"
          />

          {/* Register Button */}
          <motion.button
            whileTap={{ scale: 0.95 }}
            onClick={registerNow}
            disabled={loading}
            className="mt-5 w-full rounded-lg bg-gradient-to-r from-[--brand] to-indigo-500 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-900/30 transition hover:brightness-110 disabled:opacity-50"
          >
            {loading ? "Registering..." : "Register Student"}
          </motion.button>

          {/* Status Message */}
          {msg && (
            <p className="mt-4 rounded-lg border border-white/10 bg-black/20 p-3 text-center text-xs leading-relaxed text-slate-300">
              {msg}
            </p>
          )}
        </motion.div>
      </div>
    </div>
  );
}
