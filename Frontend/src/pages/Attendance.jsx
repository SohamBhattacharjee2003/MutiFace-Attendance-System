import React, { useState } from "react";
import CameraCapture from "../components/CameraCapture";
import axios from "axios";
import { motion } from "framer-motion";

export default function Attendance() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleCapture = async (img) => {
    try {
      setLoading(true);
      console.log("📸 Capturing image...");
      
      const res = await axios.post("http://127.0.0.1:5000/predict", { image: img });
      console.log("📊 Raw response:", res.data);
      
      const results = res.data.results || [];
      console.log("📊 Parsed results:", results);
      
      setResults(results);
      
      // Log attendance capture
      const recognized = results.filter(r => r.isKnown);
      console.log("✅ Total faces detected:", results.length);
      console.log("✅ Known faces:", recognized.length);
      
      if (recognized.length > 0) {
        console.log("✅ Attendance captured for:", recognized.map(r => r.name).join(", "));
        console.log("📊 Dashboard & Settings will auto-update in 5 seconds");
      } else if (results.length > 0) {
        console.log("⚠️ Faces detected but none recognized");
      } else {
        console.log("⚠️ No faces detected in image");
      }
    } catch (error) {
      console.error("❌ Error capturing attendance:", error);
      console.error("❌ Error details:", error.response?.data || error.message);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full mx-auto max-w-[1400px] px-5 sm:px-8 pt-24 pb-16 relative">

      {/* Background Glows */}
      <div className="absolute w-[600px] h-[600px] bg-blue-900/20 blur-[200px] -top-32 left-10 rounded-full" />
      <div className="absolute w-[500px] h-[500px] bg-indigo-800/20 blur-[200px] bottom-10 right-10 rounded-full" />

      {/* Title */}
      <motion.h2
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-2xl sm:text-3xl font-bold text-center tracking-wide"
      >
        AI Attendance Scanner
      </motion.h2>

      <p className="text-gray-400 text-center mt-2">
        Capture your image and let PresenceAI detect & mark attendance.
      </p>

      {/* CAMERA BOX */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="
          max-w-4xl mx-auto bg-white/5 backdrop-blur-xl 
          border border-white/10 rounded-2xl p-8 mt-10 relative
          shadow-[0_0_30px_rgba(0,110,255,0.2)]
        "
      >
        {/* Camera Component */}
        <CameraCapture onCapture={handleCapture} loading={loading} />

        {/* Animated Border */}
        <motion.div
          className="absolute inset-0 border-2 border-blue-500/20 rounded-2xl pointer-events-none"
          animate={{ opacity: [0.3, 1, 0.3] }}
          transition={{ duration: 2, repeat: Infinity }}
        />
        
        {/* Loading Overlay */}
        {loading && (
          <div className="absolute inset-0 bg-black/50 backdrop-blur-sm rounded-2xl flex items-center justify-center">
            <div className="text-center">
              <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-white font-semibold">Processing...</p>
            </div>
          </div>
        )}
      </motion.div>

      {/* RESULTS SECTION */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="
          max-w-4xl mx-auto bg-white/5 backdrop-blur-xl 
          border border-white/10 rounded-2xl p-6 mt-10
          shadow-[0_0_25px_rgba(255,255,255,0.05)]
        "
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold">Detection Results</h3>
          {results.length > 0 && (
            <span className="text-sm bg-blue-600/30 px-3 py-1 rounded-full text-blue-300">
              {results.length} face{results.length > 1 ? 's' : ''} detected
            </span>
          )}
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-12">
            <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-4"></div>
            <p className="text-gray-400">Processing image...</p>
          </div>
        ) : results.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📸</div>
            <p className="text-gray-400 mb-2">No faces detected yet</p>
            <p className="text-gray-500 text-sm">Capture an image to start attendance marking</p>
          </div>
        ) : (
          <div className="space-y-3">
            {results.map((r, i) => {
              const isKnown = r.isKnown || r.name !== "Unknown";
              const confidencePercent = Math.round(r.confidence * 100);
              
              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className={`
                    flex justify-between items-center p-5 rounded-xl
                    ${isKnown 
                      ? 'bg-green-600/10 border border-green-500/30' 
                      : 'bg-red-600/10 border border-red-500/30'
                    }
                  `}
                >
                  <div className="flex items-center gap-4">
                    <div className={`
                      w-14 h-14 rounded-full flex items-center justify-center font-bold text-2xl
                      ${isKnown 
                        ? 'bg-gradient-to-br from-green-600 to-emerald-400' 
                        : 'bg-gradient-to-br from-red-600 to-rose-400'
                      }
                    `}>
                      {r.name.charAt(0).toUpperCase()}
                    </div>
                    
                    <div>
                      <div className="text-lg font-semibold flex items-center gap-2">
                        {r.name}
                        {isKnown ? (
                          <span className="text-xs bg-green-600/30 px-2 py-1 rounded-full text-green-300">
                            ✓ Recognized
                          </span>
                        ) : (
                          <span className="text-xs bg-red-600/30 px-2 py-1 rounded-full text-red-300">
                            ✗ Unknown
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-gray-400">
                        Distance: {r.distance?.toFixed(3) || 'N/A'}
                      </div>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className={`
                      text-2xl font-bold
                      ${confidencePercent >= 70 ? 'text-green-400' :
                        confidencePercent >= 50 ? 'text-yellow-400' :
                        'text-red-400'
                      }
                    `}>
                      {confidencePercent}%
                    </div>
                    <div className="text-xs text-gray-500">Confidence</div>
                  </div>
                </motion.div>
              );
            })}
            
            {/* Summary */}
            <div className="mt-6 pt-4 border-t border-white/10">
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">
                  Known: <span className="text-green-400 font-semibold">
                    {results.filter(r => r.isKnown || r.name !== "Unknown").length}
                  </span>
                </span>
                <span className="text-gray-400">
                  Unknown: <span className="text-red-400 font-semibold">
                    {results.filter(r => !r.isKnown && r.name === "Unknown").length}
                  </span>
                </span>
                <span className="text-gray-400">
                  Total: <span className="text-blue-400 font-semibold">
                    {results.length}
                  </span>
                </span>
              </div>
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
}
