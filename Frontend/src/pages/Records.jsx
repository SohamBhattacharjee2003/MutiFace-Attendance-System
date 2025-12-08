import React, { useEffect, useState } from "react";
import axios from "axios";

export default function Records() {
  const [records, setRecords] = useState([]);

  useEffect(() => {
    axios.get("http://127.0.0.1:5000/attendance").then((res) => {
      setRecords(res.data);
    });
  }, []);

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-center">Attendance Records</h2>

      <div className="bg-white shadow rounded-lg p-5">
        {records.map((r, i) => (
          <div key={i} className="border-b py-3 flex justify-between">
            <span className="font-medium">{r.name}</span>
            <span className="text-gray-600">
              {new Date(r.time).toLocaleString()}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
