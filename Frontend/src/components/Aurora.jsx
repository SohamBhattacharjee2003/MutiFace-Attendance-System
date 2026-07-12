import React from "react";
import { motion } from "framer-motion";

/**
 * Ambient background: drifting colour fields, a perspective grid, and a slow scan sweep.
 *
 * Purely decorative and pointer-events:none, so it can sit behind any page without
 * intercepting clicks. Everything is CSS/SVG — no images, no external assets.
 */
export default function Aurora({ variant = "full" }) {
  return (
    <div className="pointer-events-none fixed inset-0 overflow-hidden -z-10">
      {/* base */}
      <div className="absolute inset-0 bg-[#05081c]" />

      {/* drifting colour fields */}
      <motion.div
        className="absolute -top-1/4 -left-1/4 h-[70vw] w-[70vw] rounded-full blur-[140px]"
        style={{ background: "radial-gradient(circle, rgba(56,189,248,0.22), transparent 65%)" }}
        animate={{ x: [0, 80, -40, 0], y: [0, -50, 40, 0] }}
        transition={{ duration: 26, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute top-1/3 -right-1/4 h-[60vw] w-[60vw] rounded-full blur-[150px]"
        style={{ background: "radial-gradient(circle, rgba(139,92,246,0.20), transparent 65%)" }}
        animate={{ x: [0, -70, 30, 0], y: [0, 60, -30, 0] }}
        transition={{ duration: 32, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute -bottom-1/4 left-1/4 h-[55vw] w-[55vw] rounded-full blur-[130px]"
        style={{ background: "radial-gradient(circle, rgba(16,185,129,0.14), transparent 65%)" }}
        animate={{ x: [0, 50, -50, 0], y: [0, -30, 20, 0] }}
        transition={{ duration: 29, repeat: Infinity, ease: "easeInOut" }}
      />

      {/* perspective grid */}
      {variant === "full" && (
        <svg className="absolute inset-0 h-full w-full opacity-[0.14]" aria-hidden="true">
          <defs>
            <pattern id="aurora-grid" width="56" height="56" patternUnits="userSpaceOnUse">
              <path d="M56 0H0V56" fill="none" stroke="rgba(125,211,252,0.35)" strokeWidth="0.6" />
            </pattern>
            <radialGradient id="aurora-fade" cx="50%" cy="40%" r="70%">
              <stop offset="0%" stopColor="white" stopOpacity="0.9" />
              <stop offset="100%" stopColor="white" stopOpacity="0" />
            </radialGradient>
            <mask id="aurora-mask">
              <rect width="100%" height="100%" fill="url(#aurora-fade)" />
            </mask>
          </defs>
          <rect width="100%" height="100%" fill="url(#aurora-grid)" mask="url(#aurora-mask)" />
        </svg>
      )}

      {/* slow scan sweep — echoes the camera doing its pass */}
      <motion.div
        className="absolute inset-x-0 h-40"
        style={{
          background:
            "linear-gradient(180deg, transparent, rgba(56,189,248,0.10), transparent)",
        }}
        animate={{ y: ["-10vh", "110vh"] }}
        transition={{ duration: 9, repeat: Infinity, ease: "linear" }}
      />

      {/* vignette keeps text legible over the colour */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_35%,rgba(5,8,28,0.85))]" />
    </div>
  );
}
