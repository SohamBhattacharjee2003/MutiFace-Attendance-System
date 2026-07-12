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
    <div className="min-h-screen w-full mx-auto max-w-[1400px] px-5 sm:px-8 pt-24 pb-16 relative">

      {/* Background Glow */}
      <div className="absolute w-[650px] h-[650px] bg-blue-900/20 blur-[200px] -top-20 left-20 rounded-full"></div>
      <div className="absolute w-[450px] h-[450px] bg-cyan-600/20 blur-[200px] bottom-10 right-10 rounded-full"></div>

      {/* Title */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-10 gap-4">
        <div>
          <motion.h1
            initial={{ opacity: 0, y: -12 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-white text-2xl sm:text-3xl font-bold flex items-center gap-4"
          >
            Attendance <span className="text-blue-400">Records</span>
            <span className="text-base bg-blue-600/30 px-4 py-2 rounded-full text-blue-300 font-semibold">
              {records.length} Total
            </span>
          </motion.h1>
          {lastUpdate && (
            <p className="text-gray-400 text-sm mt-2">
              Last updated: {lastUpdate.toLocaleTimeString()} • Auto-refreshing every 5s
            </p>
          )}
        </div>
        
        <button
          onClick={() => fetchRecords(validStudentNames)}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium transition shadow-lg flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      {/* Top Controls */}
      <div className="flex items-center justify-between mb-8">

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
            {filteredRecords.length === 0 ? (
              <tr>
                <td colSpan="5" className="py-12 text-center">
                  <div className="text-gray-400">
                    <div className="text-5xl mb-4">📋</div>
                    <p className="text-xl font-semibold mb-2">No Attendance Records Found</p>
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
                    className="border-b border-white/10 hover:bg-white/5"
                  >
                    {/* Avatar */}
                    <td className="py-3">
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-cyan-400 rounded-full flex items-center justify-center font-bold text-white">
                        {initials}
                      </div>
                    </td>

                    {/* Name */}
                    <td className="font-semibold">{rec.name || "Unknown"}</td>

                    {/* Confidence */}
                    <td className="text-blue-300">
                      {rec.confidence ? `${(rec.confidence * 100).toFixed(0)}%` : "N/A"}
                    </td>

                    {/* Time */}
                    <td className="text-gray-300">
                      {rec.time ? new Date(rec.time).toLocaleString() : "N/A"}
                    </td>

                    {/* Status */}
                    <td>
                      <span className="px-3 py-1 bg-green-600/50 border border-green-300/20 rounded-xl text-green-200 text-sm font-medium">
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
