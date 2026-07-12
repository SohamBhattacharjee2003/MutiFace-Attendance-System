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
  const [presentToday, setPresentToday] = useState([]);
  const [detectedFaces, setDetectedFaces] = useState([]);
  const [loading, setLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [validStudentNames, setValidStudentNames] = useState([]);
  const [stats, setStats] = useState(null);

  const loadStats = async () => {
    try {
      const res = await axios.get(`${API}/stats`);
      setStats(res.data);
    } catch (err) {
      console.log("❌ Failed to fetch stats:", err);
    }
  };

  useEffect(() => {
    // Load data sequentially to avoid race conditions
    const loadData = async () => {
      const validNames = await loadValidStudents();
      await loadStudents(validNames);
      await loadAttendance(validNames);
      await loadStats();
    };
    
    loadData();
    
    // Auto-refresh every 5 seconds for faster updates
    const interval = setInterval(() => {
      console.log("🔄 Auto-refreshing Dashboard data...");
      loadData();
    }, 5000);
    
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* ------------------ FETCH VALID STUDENTS (with embeddings) ------------------ */
  const loadValidStudents = async () => {
    try {
      const res = await axios.get(`${API}/students/valid-names`);
      const validNames = res.data.valid_names || [];
      setValidStudentNames(validNames);
      console.log("✅ Valid students with embeddings:", validNames);
      return validNames; // Return for sequential use
    } catch (err) {
      console.log("❌ Failed to fetch valid student names:", err);
      setValidStudentNames([]);
      return [];
    }
  };

  /* ------------------ FETCH TOTAL STUDENTS ------------------ */
  const loadStudents = async (validNames = []) => {
    try {
      const res = await axios.get(`${API}/students`);
      console.log("📊 All students from API:", res.data);
      
      // If no validNames provided, just use all students
      if (validNames.length === 0) {
        setStudentCount(res.data.length || 0);
        console.log("✅ Student count (all):", res.data.length);
      } else {
        // Filter students to only count those with embeddings
        const validStudents = res.data.filter(student => validNames.includes(student.name));
        setStudentCount(validStudents.length || 0);
        console.log("✅ Valid student count:", validStudents.length);
      }
    } catch (err) {
      console.log("❌ Student fetch failed:", err);
      setStudentCount(0);
    }
  };

  /* ------------------ FETCH ATTENDANCE LOGS ------------------ */
  const loadAttendance = async (validNames = []) => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/attendance`);
      const logs = res.data || [];
      
      console.log("📊 Dashboard loaded attendance data:", logs);
      console.log("📊 Total records:", logs.length);
      console.log("📊 Valid names to filter:", validNames);
      
      // If no valid names, use all logs; otherwise filter
      const validLogs = validNames.length === 0 ? logs : logs.filter(log => validNames.includes(log.name));
      console.log("📊 Displaying records:", validLogs.length);

      /* LAST 5 RECOGNITIONS (validLogs is newest-first from the API) */
      const recentRecognitions = validLogs.slice(0, 5);
      setRecentLogs(recentRecognitions);
      console.log("📝 Recent logs:", recentRecognitions);
      
      /* DETECTED FACES - Group by name with latest confidence */
      const faceMap = {};
      validLogs.forEach(log => {
        if (!faceMap[log.name] || new Date(log.time) > new Date(faceMap[log.name].time)) {
          faceMap[log.name] = log;
        }
      });
      const faces = Object.values(faceMap).map(log => ({
        name: log.name,
        confidence: Math.round(log.confidence * 100)
      }));
      setDetectedFaces(faces);

      /* TODAY'S COUNT - UNIQUE STUDENTS */
      const today = new Date().toDateString();
      const todayLogs = validLogs.filter((l) => new Date(l.time).toDateString() === today);
      const uniqueStudentsToday = new Set(todayLogs.map(log => log.name)).size;
      setTodayCount(uniqueStudentsToday);
      
      /* LIST OF STUDENTS PRESENT TODAY */
      const uniqueNames = [...new Set(todayLogs.map(log => log.name))];
      const presentStudents = uniqueNames.map(name => {
        const studentLogs = todayLogs.filter(l => l.name === name);
        return {
          name,
          time: studentLogs[0].time,
          confidence: studentLogs[0].confidence
        };
      });
      setPresentToday(presentStudents);

      /* GROUP BY DATE FOR LINECHART */
      const grouped = {};
      validLogs.forEach((log) => {
        // Use YYYY-MM-DD format for proper sorting
        const date = new Date(log.time);
        const dateKey = date.toISOString().split('T')[0]; // YYYY-MM-DD
        grouped[dateKey] = (grouped[dateKey] || 0) + 1;
      });
      
      // Sort by date and format for display
      const sortedData = Object.entries(grouped)
        .sort(([dateA], [dateB]) => new Date(dateA) - new Date(dateB))
        .map(([date, count]) => ({
          date: new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
          fullDate: date,
          count
        }));
      
      console.log("📈 Line chart data:", sortedData);
      setAttendanceData(sortedData);
      
      setLastUpdate(new Date());
    } catch (err) {
      console.error("❌ Attendance fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full mx-auto max-w-[1400px] px-5 sm:px-8 pt-24 pb-16 relative">

      {/* Dashboard Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <motion.h1
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="display-lg text-white"
          >
            PresenceAI <span className="text-blue-400">Dashboard</span>
          </motion.h1>
          {lastUpdate && (
            <p className="text-gray-400 text-sm mt-2">
              Last updated: {lastUpdate.toLocaleTimeString()} • Auto-refreshing every 5s
            </p>
          )}
        </div>
        
        <button
          onClick={() => {
            loadStudents();
            loadAttendance();
          }}
          disabled={loading}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium transition shadow-lg flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              Loading...
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh Data
            </>
          )}
        </button>
      </div>

      {/* STAT CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
        <StatCard title="Total Students" value={stats?.identities_trained ?? studentCount} icon="👥" color="blue" />
        <StatCard title="Today's Attendance" value={stats?.present_today ?? todayCount} icon="📅" color="purple" />
        <StatCard title="Detected Faces" value={detectedFaces.length} icon="🔍" color="cyan" />
        <StatCard
          title="Model Accuracy"
          value={stats?.model_accuracy != null ? `${(stats.model_accuracy * 100).toFixed(1)}%` : "—"}
          icon="🎯" color="green"
        />
      </div>

      {/* CHARTS */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 mb-10">
        
        {/* LINE CHART */}
        <div className="card-glass p-5">
          <h2 className="text-white text-xl mb-4 flex items-center justify-between">
            <span>📊 Attendance Trend</span>
            <span className="text-sm bg-blue-600/30 px-3 py-1 rounded-full text-blue-300">
              {attendanceData.length} days
            </span>
          </h2>
          
          {attendanceData.length === 0 ? (
            <div className="h-[260px] flex items-center justify-center text-gray-400">
              No attendance data available
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={attendanceData}>
                <XAxis 
                  dataKey="date" 
                  stroke="#aaa" 
                  angle={-45}
                  textAnchor="end"
                  height={80}
                  tick={{ fill: '#aaa', fontSize: 12 }}
                />
                <YAxis 
                  stroke="#aaa" 
                  tick={{ fill: '#aaa', fontSize: 12 }}
                  allowDecimals={false}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(0,0,0,0.8)', 
                    border: '1px solid rgba(255,255,255,0.2)',
                    borderRadius: '8px',
                    color: 'white'
                  }}
                />
                <Line 
                  type="monotone" 
                  dataKey="count" 
                  stroke="#4f8bff" 
                  strokeWidth={3}
                  dot={{ fill: '#4f8bff', r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* BAR CHART */}
        <div className="card-glass p-5">
          <h2 className="text-white text-xl mb-4 flex items-center justify-between">
            <span>📈 Recent Recognition Confidence</span>
            <span className="text-sm bg-cyan-600/30 px-3 py-1 rounded-full text-cyan-300">
              Last {recentLogs.length}
            </span>
          </h2>
          
          {recentLogs.length === 0 ? (
            <div className="h-[260px] flex items-center justify-center text-gray-400">
              No recent recognitions
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={recentLogs.map(l => ({
                name: l.name,
                confidence: Math.round(l.confidence * 100),
              }))}>
                <XAxis 
                  dataKey="name" 
                  stroke="#aaa" 
                  tick={{ fill: '#aaa', fontSize: 12 }}
                />
                <YAxis 
                  stroke="#aaa" 
                  tick={{ fill: '#aaa', fontSize: 12 }}
                  domain={[0, 100]}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(0,0,0,0.8)', 
                    border: '1px solid rgba(255,255,255,0.2)',
                    borderRadius: '8px',
                    color: 'white'
                  }}
                  formatter={(value) => [`${value}%`, 'Confidence']}
                />
                <Bar 
                  dataKey="confidence" 
                  fill="#00d4ff" 
                  radius={[6, 6, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* DETECTED FACES LIST */}
      {detectedFaces.length > 0 && (
        <div className="card-glass p-5 mb-10">
          <h2 className="text-white text-2xl font-bold mb-6 flex items-center gap-3">
            <span className="text-3xl">🔍</span>
            Detected Faces
            <span className="text-sm bg-blue-600/30 px-3 py-1 rounded-full text-blue-300">
              {detectedFaces.length} Total
            </span>
          </h2>
          
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {detectedFaces.map((face, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.05 }}
                className="bg-white/5 border border-white/10 rounded-xl p-4 hover:bg-white/10 hover:border-blue-400/50 transition-all text-center"
              >
                <div className="w-16 h-16 mx-auto bg-gradient-to-br from-blue-600 to-cyan-400 rounded-full flex items-center justify-center font-bold text-white text-2xl mb-3 shadow-lg">
                  {face.name.charAt(0).toUpperCase()}
                </div>
                <div className="text-white font-semibold mb-1 truncate">{face.name}</div>
                <div className="text-blue-300 text-sm font-medium">{face.confidence}%</div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* TWO COLUMN LAYOUT FOR TABLES */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* STUDENTS PRESENT TODAY */}
        <div className="card-glass p-5">
          <h2 className="text-white text-xl mb-4 flex items-center gap-2">
            ✅ Students Present Today
            <span className="text-sm bg-green-600/30 px-3 py-1 rounded-full text-green-300">
              {presentToday.length}
            </span>
          </h2>

          {presentToday.length === 0 ? (
            <div className="text-gray-400 text-center py-8">
              No students present yet today
            </div>
          ) : (
            <div className="space-y-3 max-h-[400px] overflow-y-auto">
              {presentToday.map((student, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="bg-white/5 border border-white/10 rounded-xl p-4 hover:bg-white/10 transition"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-cyan-400 rounded-full flex items-center justify-center font-bold text-white">
                        {student.name.charAt(0)}
                      </div>
                      <div>
                        <div className="text-white font-semibold">{student.name}</div>
                        <div className="text-gray-400 text-sm">
                          {new Date(student.time).toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                    <div className="text-green-400 text-sm font-medium">
                      {(student.confidence * 100).toFixed(0)}%
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>

        {/* RECENT RECOGNITIONS */}
        <div className="card-glass p-5">
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
                  <td className="py-2">{log.name}</td>
                  <td className="py-2">{new Date(log.time).toLocaleString()}</td>
                  <td className="py-2">{(log.confidence * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      
      </div>

    </div>
  );
}


/* ----------- Reusable Stat Card Component ----------- */
const StatCard = ({ title, value, icon, color }) => {
  const glow = {
    blue: "shadow-[0_0_20px_rgba(0,150,255,0.4)]",
    purple: "shadow-[0_0_20px_rgba(150,0,255,0.4)]",
    cyan: "shadow-[0_0_20px_rgba(0,255,255,0.4)]",
    green: "shadow-[0_0_20px_rgba(0,255,150,0.4)]",
    orange: "shadow-[0_0_20px_rgba(255,150,0,0.4)]",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bg-white/10 border border-white/20 backdrop-blur-xl p-6 rounded-2xl text-white ${glow[color]}`}
    >
      <div className="text-2xl sm:text-3xl mb-2">{icon}</div>
      <h3 className="text-gray-300">{title}</h3>
      <p className="text-3xl font-bold mt-1">{value}</p>
    </motion.div>
  );
};
