import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import StudentCard from "../components/StudentCard";
import axios from "axios";

export default function StudentList() {
  const [students, setStudents] = useState([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    fetchStudents();
  }, []);

  const fetchStudents = async () => {
    try {
      const res = await axios.get("http://127.0.0.1:5001/students");
      setStudents(res.data);
    } catch (err) {
      console.error("Error loading students:", err);
    }
  };

  return (
    <div className="min-h-screen bg-[#060b23] px-12 py-10 relative overflow-hidden">

      {/* Background Lights */}
      <div className="absolute w-[600px] h-[600px] bg-blue-900/20 blur-[200px] -top-20 left-10 rounded-full"></div>
      <div className="absolute w-[500px] h-[500px] bg-cyan-600/10 blur-[200px] bottom-0 right-10 rounded-full"></div>

      {/* Page Title */}
      <motion.h1
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-white text-4xl font-bold mb-10"
      >
        Student <span className="text-blue-400">Directory</span>
      </motion.h1>

      {/* TOP BAR */}
      <div className="flex justify-between items-center mb-8">

        {/* SEARCH BAR */}
        <div className="relative">
          <input
            type="text"
            placeholder="Search students..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-white/10 text-white px-6 py-3 w-80 rounded-xl border border-white/20 backdrop-blur-xl 
                       focus:outline-none focus:border-blue-400 transition"
          />
          <span className="absolute right-4 top-3 text-blue-300">🔍</span>
        </div>

        {/* TOTAL COUNT */}
        <div className="text-white opacity-80 text-lg">
          Total Students: <span className="text-blue-400">{students.length}</span>
        </div>

        {/* ADD STUDENT BUTTON */}
        <button className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-xl text-white shadow-[0_0_15px_rgba(0,150,255,0.5)]">
          + Add Student
        </button>
      </div>

      {/* GRID OF STUDENT CARDS */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-7"
      >
        {students
          .filter((s) => s.name.toLowerCase().includes(search.toLowerCase()))
          .map((student, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
            >
              <StudentCard student={student} />
            </motion.div>
          ))}
      </motion.div>
    </div>
  );
}
