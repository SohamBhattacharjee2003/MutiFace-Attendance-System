import React from "react";
import { motion } from "framer-motion";

// A landmark constellation roughly in the shape of a face — brow, eyes, nose, jaw.
// Hand-placed rather than generated so it actually reads as a face at a glance.
const NODES = [
  [50, 18], [78, 22], [108, 20], [136, 24],          // left brow
  [164, 24], [192, 20], [222, 22], [250, 18],        // right brow
  [72, 46], [96, 40], [120, 46], [96, 54],           // left eye
  [180, 46], [204, 40], [228, 46], [204, 54],        // right eye
  [150, 60], [150, 84], [150, 106],                  // nose bridge
  [128, 120], [150, 126], [172, 120],                // nostrils
  [116, 158], [150, 152], [184, 158], [150, 172],    // mouth
  [40, 70], [34, 108], [40, 146], [58, 182],         // left jaw
  [86, 212], [122, 232], [150, 240],                 // chin left
  [178, 232], [214, 212],                            // chin right
  [242, 182], [260, 146], [266, 108], [260, 70],     // right jaw
];

// Which landmarks to wire together — the mesh that makes it look like a model, not dots.
const EDGES = [
  [0, 1], [1, 2], [2, 3], [4, 5], [5, 6], [6, 7],
  [8, 9], [9, 10], [10, 11], [11, 8],
  [12, 13], [13, 14], [14, 15], [15, 12],
  [16, 17], [17, 18], [18, 19], [18, 21], [19, 20], [20, 21],
  [22, 23], [23, 24], [24, 25], [25, 22],
  [26, 27], [27, 28], [28, 29], [29, 30], [30, 31], [31, 32],
  [32, 33], [33, 34], [34, 35], [35, 36], [36, 37], [37, 38],
  [0, 26], [7, 38], [9, 16], [13, 16], [17, 23],
  [10, 16], [12, 16], [22, 29], [24, 34],
];

export default function FaceScan({ className = "" }) {
  return (
    <div className={`relative ${className}`}>
      <svg viewBox="0 0 300 260" className="w-full h-auto overflow-visible">
        <defs>
          <linearGradient id="mesh" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#38bdf8" />
            <stop offset="50%" stopColor="#818cf8" />
            <stop offset="100%" stopColor="#a78bfa" />
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <clipPath id="scanClip">
            <rect x="0" y="0" width="300" height="260" />
          </clipPath>
        </defs>

        {/* detection box, drawing itself in */}
        <motion.rect
          x="14" y="4" width="272" height="252" rx="10"
          fill="none" stroke="url(#mesh)" strokeWidth="1.5" strokeDasharray="10 8"
          initial={{ pathLength: 0, opacity: 0 }}
          animate={{ pathLength: 1, opacity: 0.55 }}
          transition={{ duration: 2, ease: "easeInOut" }}
        />

        {/* the mesh wiring itself up, edge by edge */}
        <g stroke="url(#mesh)" strokeWidth="1" fill="none" opacity="0.6">
          {EDGES.map(([a, b], i) => (
            <motion.line
              key={i}
              x1={NODES[a][0]} y1={NODES[a][1]}
              x2={NODES[b][0]} y2={NODES[b][1]}
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{ pathLength: 1, opacity: [0, 0.75, 0.45] }}
              transition={{ duration: 1.4, delay: 0.4 + i * 0.035, ease: "easeOut" }}
            />
          ))}
        </g>

        {/* the landmarks themselves, breathing */}
        <g filter="url(#glow)">
          {NODES.map(([x, y], i) => (
            <motion.circle
              key={i}
              cx={x} cy={y} r="2.4" fill="#7dd3fc"
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: [0, 1.5, 1], opacity: [0, 1, 0.85] }}
              transition={{
                duration: 0.6, delay: 0.3 + i * 0.03,
                repeat: Infinity, repeatDelay: 3.4, repeatType: "reverse",
              }}
            />
          ))}
        </g>

        {/* the scan line — the whole point of the graphic */}
        <g clipPath="url(#scanClip)">
          <motion.g
            animate={{ y: [0, 250, 0] }}
            transition={{ duration: 4.5, repeat: Infinity, ease: "easeInOut" }}
          >
            <rect x="14" y="0" width="272" height="2" fill="#38bdf8" opacity="0.95" />
            <rect x="14" y="2" width="272" height="26" fill="url(#mesh)" opacity="0.16" />
          </motion.g>
        </g>

        {/* corner brackets */}
        {[[14, 4, 1, 1], [286, 4, -1, 1], [14, 256, 1, -1], [286, 256, -1, -1]].map(
          ([x, y, sx, sy], i) => (
            <motion.path
              key={i}
              d={`M ${x} ${y + 22 * sy} L ${x} ${y} L ${x + 22 * sx} ${y}`}
              stroke="#38bdf8" strokeWidth="2.5" fill="none" strokeLinecap="round"
              initial={{ opacity: 0 }}
              animate={{ opacity: [0.4, 1, 0.4] }}
              transition={{ duration: 2.2, repeat: Infinity, delay: i * 0.18 }}
            />
          )
        )}
      </svg>

      {/* the verdict badge — this is what the system actually outputs */}
      <motion.div
        className="absolute -bottom-3 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-full
                   border border-emerald-400/40 bg-emerald-500/15 px-4 py-1.5
                   text-xs font-semibold text-emerald-300 backdrop-blur"
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 2.2, duration: 0.6 }}
      >
        ● LIVE — identity verified
      </motion.div>
    </div>
  );
}
