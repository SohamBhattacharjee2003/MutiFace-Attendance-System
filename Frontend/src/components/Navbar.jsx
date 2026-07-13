import React, { useState } from "react";
import { motion } from "framer-motion";
import { HiMenu, HiX } from "react-icons/hi";
import { FiLogOut } from "react-icons/fi";
import { Link, useLocation, useNavigate } from "react-router-dom";
import logo from "../assets/logo.png";
import { logout } from "../utils/api";

function currentUser() {
  try {
    const s = localStorage.getItem("user");
    return s ? JSON.parse(s) : null;
  } catch {
    return null;
  }
}

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const user = currentUser();

  const menuItems = [
    { name: "Dashboard", path: "/dashboard" },
    { name: "Classes", path: "/api/classes" },
    { name: "Register", path: "/api/register" },
    { name: "Live", path: "/live" },
    { name: "Scan", path: "/api/attendance" },
    { name: "Students", path: "/api/students" },
    { name: "Records", path: "/attendance-records" },
  ];

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const isActive = (path) => location.pathname === path;

  return (
    <motion.nav
      initial={{ y: -40, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="fixed top-0 left-0 w-full z-50 border-b border-white/10
                 bg-[#05070f]/70 backdrop-blur-xl"
    >
      <div className="max-w-7xl mx-auto px-6 h-16 flex justify-between items-center">
        {/* LOGO */}
        <Link to="/dashboard" className="flex items-center gap-3 select-none">
          <motion.img
            src={logo}
            alt="PresenceAI"
            className="w-10 h-10 rounded-lg object-cover ring-1 ring-white/15"
            whileHover={{ scale: 1.06 }}
          />
          <h1 className="text-white text-xl font-extrabold tracking-tight">
            Presence<span className="text-blue-400">AI</span>
          </h1>
        </Link>

        {/* DESKTOP MENU */}
        <div className="hidden md:flex items-center gap-1">
          {menuItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`px-3.5 py-2 rounded-lg text-sm font-medium transition-colors
                ${isActive(item.path)
                  ? "text-white bg-white/10"
                  : "text-white/60 hover:text-white hover:bg-white/5"}`}
            >
              {item.name}
            </Link>
          ))}
        </div>

        {/* RIGHT: user + logout (desktop) */}
        <div className="hidden md:flex items-center gap-3">
          {user?.name && (
            <span className="text-white/70 text-sm">
              Hi, <span className="text-white font-semibold">{user.name.split(" ")[0]}</span>
            </span>
          )}
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium
                       text-white/80 border border-white/10 hover:border-red-400/40
                       hover:text-red-300 hover:bg-red-500/10 transition-colors"
          >
            <FiLogOut className="w-4 h-4" /> Logout
          </button>
        </div>

        {/* MOBILE TOGGLE */}
        <button
          className="md:hidden text-white text-2xl"
          onClick={() => setOpen(!open)}
          aria-label="Toggle menu"
        >
          {open ? <HiX /> : <HiMenu />}
        </button>
      </div>

      {/* MOBILE MENU */}
      <motion.div
        initial={{ height: 0 }}
        animate={{ height: open ? "auto" : "0px" }}
        transition={{ duration: 0.25 }}
        className="overflow-hidden md:hidden bg-[#05070f]/95 border-t border-white/10"
      >
        <div className="flex flex-col px-6 py-4 gap-1">
          {menuItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              onClick={() => setOpen(false)}
              className={`px-3 py-2.5 rounded-lg font-medium
                ${isActive(item.path) ? "text-white bg-white/10" : "text-white/70"}`}
            >
              {item.name}
            </Link>
          ))}
          <button
            onClick={handleLogout}
            className="mt-2 flex items-center gap-2 px-3 py-2.5 rounded-lg font-medium
                       text-red-300 border border-red-400/20 bg-red-500/10"
          >
            <FiLogOut className="w-4 h-4" /> Logout
          </button>
        </div>
      </motion.div>
    </motion.nav>
  );
}
