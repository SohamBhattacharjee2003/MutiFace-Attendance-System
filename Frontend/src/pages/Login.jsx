import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FaUser, FaLock } from "react-icons/fa";

export default function Login() {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [pass, setPass] = useState("");
  const [name, setName] = useState("");

  return (
    <div className="h-screen w-full bg-[#060b23] flex items-center justify-center relative overflow-hidden">
      {/* ===== BACKGROUND GLOW ===== */}
      <div className="absolute w-[900px] h-[900px] bg-blue-700/20 rounded-full blur-[220px] -top-40 -left-32"></div>
      <div className="absolute w-[900px] h-[900px] bg-cyan-500/15 rounded-full blur-[260px] bottom-0 right-0"></div>

      {/* ===== BRAND HEADER ===== */}
      <motion.div
        initial={{ opacity: 0, y: -25 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="absolute top-8 w-full flex flex-col items-center z-20"
      >
        <motion.h1
          animate={{
            textShadow: [
              "0 0 15px rgba(0,150,255,0.9)",
              "0 0 25px rgba(0,150,255,0.8)",
              "0 0 15px rgba(0,150,255,0.9)",
            ],
          }}
          transition={{ duration: 4, repeat: Infinity }}
          className="text-white font-extrabold tracking-[4px] text-5xl drop-shadow-lg"
        >
          Presence<span className="text-blue-500">AI</span>
        </motion.h1>

        <p className="text-white/60 mt-2 text-sm tracking-wide">
          AI-powered Smart Attendance System
        </p>
      </motion.div>

      {/* ===== MAIN CONTENT WRAPPER ===== */}
      <div
        className="flex items-center justify-center gap-40 w-[88%] max-w-7xl relative z-10 px-12 py-8 
    bg-white/5 backdrop-blur-xl border border-blue-300/10 rounded-3xl 
    shadow-[0_0_60px_rgba(0,110,255,0.15)] h-[75%]"
      >
        {/* ===== LEFT ILLUSTRATION ===== */}
        <motion.img
          src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS671hX9LXk6ykl_P5vZzeGBUhKASSFzuD_1w&s"
          alt="login illustration"
          initial={{ opacity: 0, x: -40 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.7 }}
          className="hidden md:block select-none 
             h-full max-h-[532px] object-cover rounded-xl"
        />

        {/* ===== FORM CARD ===== */}
        <motion.div
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8 }}
          className="w-[460px] bg-white/10 backdrop-blur-2xl border border-blue-300/20 
                     p-12 rounded-2xl shadow-[0_0_40px_rgba(0,90,255,0.22)]"
        >
          <h2 className="text-white text-center text-3xl font-bold mb-2">
            {mode === "login" ? "WELCOME" : "CREATE ACCOUNT"}
          </h2>

          <p className="text-white/50 text-center mb-10 text-sm">
            {mode === "login"
              ? "Access your PresenceAI dashboard."
              : "Create your new PresenceAI account."}
          </p>

          {/* === Toggle Buttons === */}
          <div className="flex mb-10 gap-2 bg-white/10 p-1 rounded-lg">
            <button
              onClick={() => setMode("login")}
              className={`w-1/2 py-3 rounded-lg transition font-semibold ${
                mode === "login"
                  ? "bg-blue-600 text-white"
                  : "text-white/60 hover:text-white"
              }`}
            >
              Login
            </button>

            <button
              onClick={() => setMode("signup")}
              className={`w-1/2 py-3 rounded-lg transition font-semibold ${
                mode === "signup"
                  ? "bg-blue-600 text-white"
                  : "text-white/60 hover:text-white"
              }`}
            >
              Signup
            </button>
          </div>

          {/* ===== FORMS ===== */}
          <AnimatePresence mode="wait">
            {/* ---- LOGIN ---- */}
            {mode === "login" ? (
              <motion.div
                key="loginForm"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.25 }}
                className="flex flex-col gap-8"
              >
                {/* Username */}
                <div className="relative border-b border-white/30 flex items-center gap-4 pb-3">
                  <FaUser className="text-white/50 text-xl" />
                  <input
                    type="text"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full bg-transparent outline-none text-white text-lg"
                    placeholder="Username"
                  />
                </div>

                {/* Password */}
                <div className="relative border-b border-white/30 flex items-center gap-4 pb-3">
                  <FaLock className="text-white/50 text-xl" />
                  <input
                    type="password"
                    value={pass}
                    onChange={(e) => setPass(e.target.value)}
                    className="w-full bg-transparent outline-none text-white text-lg"
                    placeholder="Password"
                  />
                </div>

                <a className="text-right text-white/60 hover:text-white text-sm -mt-4 cursor-pointer">
                  Forgot Password?
                </a>

                <button
                  className="w-full p-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg 
                                   transition font-semibold shadow-[0_0_20px_rgba(0,110,255,0.6)]"
                >
                  Login
                </button>
              </motion.div>
            ) : (
              /* ---- SIGNUP ---- */
              <motion.div
                key="signupForm"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.25 }}
                className="flex flex-col gap-8"
              >
                {/* Full Name */}
                <div className="relative border-b border-white/30 flex items-center gap-4 pb-3">
                  <FaUser className="text-white/50 text-xl" />
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full bg-transparent outline-none text-white text-lg"
                    placeholder="Full Name"
                  />
                </div>

                {/* Email */}
                <div className="relative border-b border-white/30 flex items-center gap-4 pb-3">
                  <FaUser className="text-white/50 text-xl" />
                  <input
                    type="text"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full bg-transparent outline-none text-white text-lg"
                    placeholder="Email"
                  />
                </div>

                {/* Password */}
                <div className="relative border-b border-white/30 flex items-center gap-4 pb-3">
                  <FaLock className="text-white/50 text-xl" />
                  <input
                    type="password"
                    value={pass}
                    onChange={(e) => setPass(e.target.value)}
                    className="w-full bg-transparent outline-none text-white text-lg"
                    placeholder="Password"
                  />
                </div>

                <button
                  className="w-full p-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg 
                                   transition font-semibold shadow-[0_0_20px_rgba(0,110,255,0.6)]"
                >
                  Create Account
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>
    </div>
  );
}
