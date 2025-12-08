import React, { useState } from "react";
import CameraCapture from "../components/CameraCapture";
import axios from "axios";

export default function Attendance() {
  const [results, setResults] = useState([]);

  const handleCapture = async (img) => {
    const res = await axios.post("http://127.0.0.1:5000/predict", {
      image: img,
    });

    setResults(res.data.results || []);
  };

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-center">Take Attendance</h2>

      <div className="flex justify-center">
        <CameraCapture onCapture={handleCapture} />
      </div>

      <div className="bg-white p-5 mt-5 shadow rounded-lg">
        <h3 className="text-xl font-semibold mb-3">Detected Faces:</h3>

        {results.length === 0 && (
          <p className="text-gray-600">No faces detected yet.</p>
        )}

        {results.map((r, i) => (
          <div
            key={i}
            className="p-3 border-b flex justify-between items-center"
          >
            <span className="font-medium">{r.name}</span>
            <span className="text-blue-600 font-semibold">
              {Math.round(r.confidence * 100)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
