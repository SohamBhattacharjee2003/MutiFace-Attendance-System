import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { RefreshCw, Plus, Camera, Trash2 } from "lucide-react";
import axios from "axios";
import AddImagesModal from "../components/AddImagesModal";


export default function StudentList() {
  const [students, setStudents] = useState([]);
  const [search, setSearch] = useState("");
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [showAddImagesModal, setShowAddImagesModal] = useState(false);

  useEffect(() => {
    fetchStudents();
    const interval = setInterval(fetchStudents, 5000); // live refresh
    return () => clearInterval(interval);
  }, []);

  const fetchStudents = async () => {
    try {
      const res = await axios.get(`/api/students`);
      setStudents(res.data);
    } catch (err) {
      console.error("Error loading students:", err);
    }
  };

  const handleDelete = async (name) => {
    if (!window.confirm(`Delete "${name}" and all their training images?`)) return;
    try {
      await axios.delete(`/api/students/${encodeURIComponent(name)}`);
      fetchStudents();
    } catch (err) {
      alert(err.response?.data?.error || "Failed to delete student");
    }
  };

  const handleAddImages = (student) => {
    setSelectedStudent(student);
    setShowAddImagesModal(true);
  };

  const handleModalClose = () => {
    setShowAddImagesModal(false);
    setSelectedStudent(null);
    fetchStudents(); // Refresh the list
  };

  return (
    <div className="min-h-screen w-full mx-auto max-w-[1400px] px-5 sm:px-8 pt-24 pb-16 relative">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
        <motion.h1
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-3xl md:text-2xl sm:text-3xl font-bold mb-4 md:mb-0"
        >
          Student <span className="text-blue-400">List</span>
        </motion.h1>

        <button
          onClick={fetchStudents}
          className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors w-fit"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Search */}
      <div className="mb-8">
        <input
          type="text"
          placeholder="Search student..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full md:w-80 px-5 py-3 rounded-xl bg-white/10 border border-white/20 focus:outline-none focus:border-blue-400 transition-colors"
        />
      </div>

      {/* Student Count */}
      <p className="text-gray-400 mb-6">
        Showing{" "}
        {students
          .filter((s) => s.name.toLowerCase().includes(search.toLowerCase()))
          .length}{" "}
        of {students.length} students
      </p>

      {/* Student Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {students
          .filter((s) => s.name.toLowerCase().includes(search.toLowerCase()))
          .map((student, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl p-6 hover:border-blue-400/50 transition-all"
            >
              {/* Avatar */}
              <div className="w-16 h-16 mb-4 bg-gradient-to-br from-blue-500 to-cyan-400 rounded-full flex items-center justify-center text-2xl font-bold shadow-lg">
                {student.name[0].toUpperCase()}
              </div>

              <h3 className="text-xl font-semibold mb-2">{student.name}</h3>

              <p className="text-gray-400 mb-1">
                Training Images:{" "}
                <span className="text-blue-400 font-semibold">
                  {student.samples || 0}
                </span>
              </p>

              {/* Quality Indicator */}
              <div className="mb-4">
                <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
                  <span>Quality</span>
                  <span className="font-semibold">
                    {student.samples >= 15
                      ? "Excellent"
                      : student.samples >= 10
                      ? "Good"
                      : student.samples >= 5
                      ? "Fair"
                      : "Poor"}
                  </span>
                </div>
                <div className="w-full bg-white/10 rounded-full h-1.5">
                  <div
                    className={`h-1.5 rounded-full transition-all ${
                      student.samples >= 15
                        ? "bg-green-500"
                        : student.samples >= 10
                        ? "bg-blue-500"
                        : student.samples >= 5
                        ? "bg-yellow-500"
                        : "bg-red-500"
                    }`}
                    style={{
                      width: `${Math.min((student.samples / 15) * 100, 100)}%`,
                    }}
                  ></div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-2">
                <button
                  onClick={() => handleAddImages(student)}
                  className="flex-1 flex items-center justify-center space-x-2 bg-blue-600 text-white px-4 py-2.5 rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  <Plus className="w-4 h-4" />
                  <span>Add Images</span>
                </button>
                <button
                  onClick={() => handleDelete(student.name)}
                  title="Delete student"
                  className="px-3 py-2.5 rounded-lg border border-red-400/30 text-red-300 hover:bg-red-500/10 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              {/* Warning */}
              {student.samples < 10 && (
                <p className="mt-3 text-xs text-center text-amber-400">
                  ⚠️ Add {10 - student.samples} more for better accuracy
                </p>
              )}
            </motion.div>
          ))}
      </div>

      {/* Empty State */}
      {students.filter((s) => s.name.toLowerCase().includes(search.toLowerCase())).length === 0 && (
        <div className="text-center py-16">
          <Camera className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400 text-lg">
            {search ? "No students found matching your search" : "No students registered yet"}
          </p>
        </div>
      )}

      {/* Add Images Modal */}
      {showAddImagesModal && (
        <AddImagesModal student={selectedStudent} onClose={handleModalClose} />
      )}
    </div>
  );
}
