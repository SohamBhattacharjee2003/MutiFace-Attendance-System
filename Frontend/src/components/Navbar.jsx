import React, { useState } from "react";
import { motion } from "framer-motion";
import { HiMenu, HiX } from "react-icons/hi";
import { Link, useLocation } from "react-router-dom";
import logo from "../assets/logo.png";  // your real logo

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const location = useLocation();

  const menuItems = [
    { name: "Dashboard", path: "/dashboard" },
    { name: "Register Student", path: "/register" },
    { name: "Live Attendance", path: "/live" },
    { name: "Attendance Logs", path: "/attendance" },
    { name: "Students List", path: "/students" },
    { name: "Attendance Report", path: "/attendance-records" },
  ];

  return (
    <motion.nav
      initial={{ y: -40, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6 }}
      className="
        fixed top-0 left-0 w-full z-50
        bg-[#050a1a]/70 backdrop-blur-xl
        border-b border-blue-900/30
        shadow-[0_0_25px_rgba(0,50,150,0.35)]
      "
    >
      <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">

        {/* ========== LOGO ========== */}
        <Link to="/dashboard" className="flex items-center gap-3 select-none">
          <motion.img
            src={logo}
            alt="PresenceAI"
            className="w-18 h-12 rounded-xl shadow-[0_0_12px_rgba(0,140,255,0.7)]"
            whileHover={{ scale: 1.08 }}
          />

          <h1 className="text-white text-2xl font-extrabold tracking-wide">
            Presence<span className="text-blue-400">AI</span>
          </h1>
        </Link>

        {/* ========== DESKTOP MENU ========== */}
        <div className="hidden md:flex items-center gap-10 text-white/70 font-medium">
          {menuItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`relative group ${
                location.pathname === item.path ? "text-blue-400" : ""
              }`}
            >
              {item.name}

              <span
                className={`absolute left-0 -bottom-1 h-[2px] bg-blue-500 transition-all rounded-full
                  ${location.pathname === item.path ? "w-full" : "w-0 group-hover:w-full"}
                `}
              />
            </Link>
          ))}
        </div>

        {/* ========== MOBILE MENU BUTTON ========== */}
        <button
          className="md:hidden text-white text-3xl"
          onClick={() => setOpen(!open)}
        >
          {open ? <HiX /> : <HiMenu />}
        </button>
      </div>

      {/* ========== MOBILE MENU ========== */}
      <motion.div
        initial={{ height: 0 }}
        animate={{ height: open ? "auto" : "0px" }}
        transition={{ duration: 0.25 }}
        className="overflow-hidden md:hidden bg-[#050a1a]/80 border-t border-blue-900/30"
      >
        <div className="flex flex-col text-white/80 px-6 py-4 gap-4 text-lg">
          {menuItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              onClick={() => setOpen(false)}
              className={`pb-1 border-b border-blue-900/20 ${
                location.pathname === item.path ? "text-blue-400" : ""
              }`}
            >
              {item.name}
            </Link>
          ))}
        </div>
      </motion.div>
    </motion.nav>
  );
}
