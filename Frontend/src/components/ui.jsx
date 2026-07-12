import React from "react";
import { motion } from "framer-motion";

/**
 * PresenceAI UI kit — the single source of layout truth.
 *
 * Before this existed, every page invented its own wrapper: three different background
 * colours (#060b23, #070c24, #05081c), four different top paddings, and cards whose
 * padding and radius changed from page to page. Each page also painted an OPAQUE
 * background over the body gradient, so the app looked like seven different apps.
 *
 * Rules enforced here:
 *   - pages never set a background; the body owns it (see index.css)
 *   - one container width, one gutter, one navbar offset
 *   - cards are h-full so a row of them is always the same height
 *   - one type scale — no page-local font sizes
 */

/* ── layout ─────────────────────────────────────────────────────────────── */

export function PageShell({ children, className = "", wide = false }) {
  return (
    <div className={`min-h-screen pt-24 pb-16 ${className}`}>
      <div className={`mx-auto px-5 sm:px-8 ${wide ? "max-w-[1400px]" : "max-w-6xl"}`}>
        {children}
      </div>
    </div>
  );
}

export function PageHeader({ title, accent, sub, actions }) {
  return (
    <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
          {title} {accent && <span className="text-[--brand]">{accent}</span>}
        </h1>
        {sub && <p className="mt-1.5 text-sm text-[--muted]">{sub}</p>}
      </div>
      {actions && <div className="flex items-center gap-2.5">{actions}</div>}
    </div>
  );
}

/* ── surfaces ───────────────────────────────────────────────────────────── */

export function Card({ children, className = "", hover = false, pad = "p-5" }) {
  return (
    <div
      className={`card-glass flex h-full flex-col ${pad} ${
        hover ? "transition duration-200 hover:border-white/25 hover:-translate-y-0.5" : ""
      } ${className}`}
    >
      {children}
    </div>
  );
}

export function CardTitle({ children, right }) {
  return (
    <div className="mb-4 flex items-center justify-between gap-3">
      <h2 className="text-sm font-semibold tracking-wide text-white/90 uppercase">
        {children}
      </h2>
      {right}
    </div>
  );
}

/**
 * A metric tile. Fixed internal structure so a row of them always aligns:
 * label on top, number on the baseline, hint pinned to the bottom.
 */
export function Stat({ icon: Icon, label, value, hint, tone = "brand", delay = 0 }) {
  const tones = {
    brand: "from-sky-500/20 to-indigo-500/10 text-sky-300 border-sky-400/25",
    good: "from-emerald-500/20 to-teal-500/10 text-emerald-300 border-emerald-400/25",
    warn: "from-amber-500/20 to-orange-500/10 text-amber-300 border-amber-400/25",
    bad: "from-rose-500/20 to-pink-500/10 text-rose-300 border-rose-400/25",
    violet: "from-violet-500/20 to-fuchsia-500/10 text-violet-300 border-violet-400/25",
  };
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4 }}
      className="card-glass flex h-full flex-col p-4"
    >
      <div className="flex items-start justify-between gap-3">
        <span className="text-xs font-medium text-[--muted]">{label}</span>
        {Icon && (
          <span
            className={`grid h-8 w-8 shrink-0 place-items-center rounded-lg border bg-gradient-to-br ${tones[tone]}`}
          >
            <Icon className="h-4 w-4" />
          </span>
        )}
      </div>
      <div className="mt-3 text-2xl font-bold tracking-tight text-white tabular-nums">
        {value}
      </div>
      {hint && <div className="mt-auto pt-2 text-[11px] leading-snug text-slate-500">{hint}</div>}
    </motion.div>
  );
}

/* ── controls ───────────────────────────────────────────────────────────── */

export function Button({
  children, variant = "primary", size = "md", className = "", as: As = "button", ...rest
}) {
  const sizes = {
    sm: "px-3 py-1.5 text-xs",
    md: "px-4 py-2.5 text-sm",
    lg: "px-6 py-3 text-sm",
  };
  const variants = {
    primary:
      "bg-gradient-to-r from-[--brand] to-indigo-500 text-white shadow-lg shadow-indigo-900/30 hover:brightness-110",
    ghost:
      "border border-white/12 bg-white/[0.04] text-slate-200 hover:border-white/25 hover:bg-white/[0.08]",
    danger:
      "border border-rose-400/30 bg-rose-500/10 text-rose-300 hover:bg-rose-500/20",
  };
  return (
    <As
      className={`inline-flex items-center justify-center gap-2 rounded-lg font-semibold
                  transition disabled:cursor-not-allowed disabled:opacity-50
                  ${sizes[size]} ${variants[variant]} ${className}`}
      {...rest}
    >
      {children}
    </As>
  );
}

export function Badge({ children, tone = "brand", className = "" }) {
  const tones = {
    brand: "border-sky-400/30 bg-sky-500/10 text-sky-300",
    good: "border-emerald-400/30 bg-emerald-500/10 text-emerald-300",
    warn: "border-amber-400/30 bg-amber-500/10 text-amber-300",
    bad: "border-rose-400/30 bg-rose-500/10 text-rose-300",
    muted: "border-white/12 bg-white/5 text-slate-400",
  };
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1
                  text-[11px] font-medium ${tones[tone]} ${className}`}
    >
      {children}
    </span>
  );
}

export function Field({ label, ...rest }) {
  return (
    <label className="block">
      {label && (
        <span className="mb-1.5 block text-xs font-medium text-[--muted]">{label}</span>
      )}
      <input
        className="w-full rounded-lg border border-white/12 bg-black/25 px-3.5 py-2.5 text-sm
                   text-white placeholder:text-slate-500 transition
                   focus:border-[--brand] focus:outline-none"
        {...rest}
      />
    </label>
  );
}

/* ── feedback ───────────────────────────────────────────────────────────── */

export function Empty({ icon: Icon, title, sub }) {
  return (
    <div className="flex flex-col items-center justify-center py-14 text-center">
      {Icon && (
        <span className="mb-3 grid h-12 w-12 place-items-center rounded-xl border border-white/10 bg-white/[0.04]">
          <Icon className="h-5 w-5 text-slate-500" />
        </span>
      )}
      <p className="text-sm font-medium text-slate-300">{title}</p>
      {sub && <p className="mt-1 max-w-xs text-xs text-slate-500">{sub}</p>}
    </div>
  );
}

export const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06 } },
};
export const riseIn = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] } },
};
