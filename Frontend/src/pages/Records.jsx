import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import axios from "axios";

export default function Records() {
  const [records, setRecords] = useState([]);
  const [search, setSearch] = useState("");
  const [date, setDate] = useState("");

  useEffect(() => {
    fetchRecords();
  }, []);

  const fetchRecords = async () => {
    try {
      const res = await axios.get("/api/attendance");
      setRecords(res.data);
    } catch (err) {
      console.error("Error loading attendance:", err);
    }
  };

  // CSV Export
  const exportCSV = () => {
    const header = "Name,Confidence,Time\n";
    const rows = records
      .map((r) => `${r.name},${r.confidence},${new Date(r.time).toLocaleString()}`)
      .join("\n");

    const blob = new Blob([header + rows], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "attendance_records.csv";
    a.click();
  };

  const filteredRecords = records.filter((r) => {
    const matchName = r.name.toLowerCase().includes(search.toLowerCase());
    const matchDate = date
      ? new Date(r.time).toISOString().startsWith(date)
      : true;
    return matchName && matchDate;
  });

  return (
    <div className="min-h-screen w-full mx-auto max-w-[1400px] px-5 sm:px-8 pt-24 pb-16 relative">

      {/* Background Glow */}
      <div className="absolute w-[650px] h-[650px] bg-blue-900/20 blur-[200px] -top-20 left-20 rounded-full"></div>
      <div className="absolute w-[450px] h-[450px] bg-cyan-600/20 blur-[200px] bottom-10 right-10 rounded-full"></div>

      {/* Title */}
      <motion.h1
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-white text-2xl sm:text-3xl font-bold mb-10"
      >
        Attendance <span className="text-blue-400">Records</span>
      </motion.h1>

      {/* Top Controls */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between mb-8 gap-4">

        {/* Search */}
        <input
          type="text"
          placeholder="Search student..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="bg-white/10 text-white px-6 py-3 w-80 rounded-xl border border-white/20 
                     backdrop-blur-xl focus:border-blue-400 focus:outline-none transition"
        />

        {/* Date Filter */}
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="bg-white/10 text-white px-4 py-3 rounded-xl border border-white/20 
                     backdrop-blur-xl focus:border-blue-400 focus:outline-none transition"
        />

        {/* Export Button */}
        <button
          onClick={exportCSV}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl 
                     shadow-[0_0_15px_rgba(0,150,255,0.5)] transition"
        >
          Export CSV
        </button>
      </div>

      {/* Table Container */}
      <div className="bg-white/10 border border-white/20 rounded-2xl backdrop-blur-xl p-6 shadow-xl overflow-auto max-h-[70vh]">

        <table className="w-full text-left text-white">
          <thead>
            <tr className="border-b border-white/20 text-blue-300">
              <th className="py-3">Avatar</th>
              <th>Name</th>
              <th>Confidence</th>
              <th>Time</th>
              <th>Status</th>
            </tr>
          </thead>

          <tbody>
            {filteredRecords.map((rec, i) => {
              const initials = rec.name
                .split(" ")
                .map((w) => w[0])
                .join("");

              return (
                <motion.tr
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.03 }}
                  className="border-b border-white/10 hover:bg-white/5"
                >
                  {/* Avatar */}
                  <td className="py-3">
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-cyan-400 rounded-full flex items-center justify-center font-bold">
                      {initials}
                    </div>
                  </td>

                  {/* Name */}
                  <td>{rec.name}</td>

                  {/* Confidence */}
                  <td className="text-blue-300">{rec.confidence.toFixed(2)}</td>

                  {/* Time */}
                  <td>{new Date(rec.time).toLocaleString()}</td>

                  {/* Status */}
                  <td>
                    <span className="px-3 py-1 bg-green-600/50 border border-green-300/20 rounded-xl text-green-200">
                      Present
                    </span>
                  </td>
                </motion.tr>
              );
            })}
          </tbody>
        </table>

      </div>
    </div>
  );
}
