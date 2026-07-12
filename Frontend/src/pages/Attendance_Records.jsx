import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import axios from "axios";

export default function AttendanceRecords() {
  const [records, setRecords] = useState([]);
  const [search, setSearch] = useState("");
  const [date, setDate] = useState("");
  const [lastUpdate, setLastUpdate] = useState(null);
  const [validStudentNames, setValidStudentNames] = useState([]);

  const loadValidStudents = async () => {
    try {
      const res = await axios.get("http://127.0.0.1:5000/students/valid-names");
      const validNames = res.data.valid_names || [];
      setValidStudentNames(validNames);
      console.log("✅ Valid students with embeddings:", validNames);
      return validNames;
    } catch (err) {
      console.log("❌ Failed to fetch valid student names:", err);
      setValidStudentNames([]);
      return [];
    }
  };

  const fetchRecords = async (validNames = []) => {
    try {
      const res = await axios.get("http://127.0.0.1:5000/attendance");
      console.log("📋 Fetched records:", res.data);
      console.log("📋 Total records:", res.data?.length || 0);
      console.log("📋 Valid names to filter:", validNames);
      
      // If no valid names, show all records; otherwise filter
      const validRecords = validNames.length === 0 
        ? (res.data || [])
        : (res.data || []).filter(record => validNames.includes(record.name));
      console.log("📋 Displaying records:", validRecords.length);
      
      setRecords(validRecords);
      setLastUpdate(new Date());
    } catch (err) {
      console.error("❌ Error loading attendance:", err);
      setRecords([]);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      const validNames = await loadValidStudents();
      await fetchRecords(validNames);
    };
    
    loadData();
    
    // Auto-refresh every 5 seconds for faster updates
    const interval = setInterval(() => {
      console.log("🔄 Auto-refreshing Settings/Records data...");
      loadData();
    }, 5000);
    
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
    <div className="min-h-screen w-full mx-auto max-w-6xl px-5 sm:px-8 pt-24 pb-16 relative">

      {/* Background Glow */}

      {/* Title */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-5 gap-4">
        <div>
          <motion.h1
            initial={{ opacity: 0, y: -12 }}
            animate={{ opacity: 1, y: 0 }}
            className="display-lg text-white flex items-center gap-3"
          >
            Attendance <span className="text-blue-400">Records</span>
            <span className="rounded-full border border-sky-400/30 bg-sky-500/10 px-2.5 py-1 text-[11px] font-medium text-sky-300">
              {records.length} Total
            </span>
          </motion.h1>
          {lastUpdate && (
            <p className="mt-1.5 text-xs text-[--muted]">
              Last updated: {lastUpdate.toLocaleTimeString()} • Auto-refreshing every 5s
            </p>
          )}
        </div>
        
        <button
          onClick={() => fetchRecords(validStudentNames)}
          className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-[--brand] to-indigo-500 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-900/30 transition hover:brightness-110"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      {/* Top Controls */}
      <div className="mb-4 flex flex-wrap items-center gap-2.5">

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
      <div className="card-glass scroll-x max-h-[65vh] overflow-y-auto p-0">

        <table className="w-full min-w-[640px] text-left text-sm text-white">
          <thead>
            <tr className="sticky top-0 z-10 border-b border-white/10 bg-[--bg-1]/95 backdrop-blur text-[11px] uppercase tracking-wide text-slate-400">
              <th className="px-4 py-3 font-medium">Avatar</th>
              <th>Name</th>
              <th>Confidence</th>
              <th>Time</th>
              <th>Status</th>
            </tr>
          </thead>

          <tbody>
            {filteredRecords.length === 0 ? (
              <tr>
                <td colSpan="5" className="px-4 py-14 text-center">
                  <div className="text-slate-500">
                    
                    <p className="text-sm font-medium text-slate-300">No attendance records yet</p>
                    <p className="text-sm">
                      {records.length === 0 
                        ? "Start taking attendance to see records here" 
                        : "No records match your search criteria"}
                    </p>
                  </div>
                </td>
              </tr>
            ) : (
              filteredRecords.map((rec, i) => {
                const initials = rec.name
                  ? rec.name.split(" ").map((w) => w[0]).join("")
                  : "?";

                return (
                  <motion.tr
                    key={i}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.03 }}
                    className="border-b border-white/[0.06] transition hover:bg-white/[0.03]"
                  >
                    {/* Avatar */}
                    <td className="px-4 py-2.5">
                      <div className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-[--brand]/40 to-violet-500/30 text-xs font-bold text-white">
                        {initials}
                      </div>
                    </td>

                    {/* Name */}
                    <td className="px-4 py-2.5 font-medium">{rec.name || "Unknown"}</td>

                    {/* Confidence */}
                    <td className="px-4 py-2.5 font-mono text-xs tabular-nums text-sky-300">
                      {rec.confidence ? `${(rec.confidence * 100).toFixed(0)}%` : "N/A"}
                    </td>

                    {/* Time */}
                    <td className="px-4 py-2.5 text-xs tabular-nums text-slate-400">
                      {rec.time ? new Date(rec.time).toLocaleString() : "N/A"}
                    </td>

                    {/* Status */}
                    <td>
                      <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-400/30 bg-emerald-500/10 px-2.5 py-1 text-[11px] font-medium text-emerald-300">
                        Present
                      </span>
                    </td>
                  </motion.tr>
                );
              })
            )}
          </tbody>
        </table>

      </div>
    </div>
  );
}
