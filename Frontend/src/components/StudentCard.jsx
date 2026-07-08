import React from "react";

export default function StudentCard({ student }) {
  const initials = student.name
    .split(" ")
    .map((w) => w[0])
    .join("");

  return (
    <div className="bg-white/10 border border-white/20 backdrop-blur-xl rounded-2xl p-6 
                    shadow-[0_0_15px_rgba(0,150,255,0.3)] hover:shadow-[0_0_25px_rgba(0,150,255,0.6)]
                    transition cursor-pointer">

      {/* Avatar Circle */}
      <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-600 to-cyan-500 flex items-center justify-center text-white text-xl font-bold mx-auto mb-4">
        {initials}
      </div>

      {/* Student Name */}
      <p className="text-white text-center text-lg font-semibold">{student.name}</p>

      {/* ID or Label */}
      <p className="text-blue-300 text-center text-sm opacity-80 mt-1">
        Registered Student
      </p>
    </div>
  );
}
