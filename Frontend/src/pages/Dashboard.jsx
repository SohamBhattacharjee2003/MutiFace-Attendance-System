import React, { useEffect, useState } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function Dashboard() {
  const API = "http://127.0.0.1:5000";   // BACKEND

  const [studentCount, setStudentCount] = useState(0);
  const [todayCount, setTodayCount] = useState(0);
  const [attendanceData, setAttendanceData] = useState([]);
  const [recentLogs, setRecentLogs] = useState([]);

  useEffect(() => {
    loadStudents();
    loadAttendance();
  }, []);

  /* ------------------ FETCH TOTAL STUDENTS ------------------ */
  const loadStudents = async () => {
    try {
      const res = await axios.get(`${API}/students`);
      setStudentCount(res.data.length || 0);
    } catch {
      console.log("Student fetch failed");
    }
  };

  /* ------------------ FETCH ATTENDANCE LOGS ------------------ */
  const loadAttendance = async () => {
    try {
      const res = await axios.get(`${API}/attendance`);
      const logs = res.data;

      /* LAST 5 RECOGNITIONS */
      setRecentLogs(logs.slice(-5).reverse());

      /* TODAY'S COUNT */
      const today = new Date().toDateString();
      setTodayCount(
        logs.filter((l) => new Date(l.time).toDateString() === today).length
      );

      /* GROUP BY DATE FOR LINECHART */
      const grouped = {};
      logs.forEach((log) => {
        const d = new Date(log.time).toLocaleDateString();
        grouped[d] = (grouped[d] || 0) + 1;
      });
      setAttendanceData(
        Object.entries(grouped).map(([date, count]) => ({ date, count }))
      );
    } catch {
      console.log("Attendance fetch error");
    }
  };

  return (
    <div className="min-h-screen bg-[#070c24] px-10 py-10 pt-32 relative overflow-hidden">

      {/* Dashboard Header */}
      <motion.h1
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-white text-4xl font-bold tracking-wide mb-8"
      >
        PresenceAI <span className="text-blue-400">Dashboard</span>
      </motion.h1>

      {/* STAT CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
        <StatCard title="Total Students" value={studentCount} icon="👥" color="blue" />
        <StatCard title="Today's Attendance" value={todayCount} icon="📅" color="purple" />
        <StatCard title="Model Accuracy" value="95%" icon="🎯" color="green" />
        <StatCard title="Last Training" value="Auto-Updating" icon="⚙️" color="orange" />
      </div>

      {/* CHARTS */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 mb-10">
        
        {/* LINE CHART */}
        <div className="bg-white/10 border border-white/20 rounded-2xl p-6 backdrop-blur-xl shadow-lg">
          <h2 className="text-white text-xl mb-4">📊 Attendance Trend</h2>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={attendanceData}>
              <XAxis dataKey="date" stroke="#aaa" />
              <YAxis stroke="#aaa" />
              <Tooltip />
              <Line type="monotone" dataKey="count" stroke="#4f8bff" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* BAR CHART */}
        <div className="bg-white/10 border border-white/20 rounded-2xl p-6 backdrop-blur-xl shadow-lg">
          <h2 className="text-white text-xl mb-4">📈 Confidence Distribution</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={recentLogs.map(l => ({
              name: l.name,
              confidence: Math.round(l.confidence * 100),
            }))}>
              <XAxis dataKey="name" stroke="#aaa" />
              <YAxis stroke="#aaa" />
              <Tooltip />
              <Bar dataKey="confidence" fill="#00d4ff" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* RECENT LOG TABLE */}
      <div className="bg-white/10 border border-white/20 rounded-2xl p-6">
        <h2 className="text-white text-xl mb-4">📝 Recent Recognitions</h2>

        <table className="w-full text-left text-gray-300">
          <thead>
            <tr className="border-b border-white/20 text-gray-400">
              <th className="py-2">Name</th>
              <th className="py-2">Time</th>
              <th className="py-2">Confidence</th>
            </tr>
          </thead>

          <tbody>
            {recentLogs.map((log, i) => (
              <tr key={i} className="border-b border-white/10">
                <td>{log.name}</td>
                <td>{new Date(log.time).toLocaleString()}</td>
                <td>{(log.confidence * 100).toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

    </div>
  );
}


/* ----------- Reusable Stat Card Component ----------- */
const StatCard = ({ title, value, icon, color }) => {
  const glow = {
    blue: "shadow-[0_0_20px_rgba(0,150,255,0.4)]",
    purple: "shadow-[0_0_20px_rgba(150,0,255,0.4)]",
    green: "shadow-[0_0_20px_rgba(0,255,150,0.4)]",
    orange: "shadow-[0_0_20px_rgba(255,150,0,0.4)]",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bg-white/10 border border-white/20 backdrop-blur-xl p-6 rounded-2xl text-white ${glow[color]}`}
    >
      <div className="text-4xl mb-2">{icon}</div>
      <h3 className="text-gray-300">{title}</h3>
      <p className="text-3xl font-bold mt-1">{value}</p>
    </motion.div>
  );
};
