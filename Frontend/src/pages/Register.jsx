import React, { useState } from "react";
import CameraCapture from "../components/CameraCapture";
import { API } from "../utils/api";


export default function Register() {
  const [name, setName] = useState("");
  const [images, setImages] = useState([]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleCapture = (img) => {
    setImages((prev) => [...prev, img]);
  };

  const sendRegister = async () => {
    if (!name || images.length < 5) {
      alert("Enter name & capture at least 5 images");
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      const res = await API.post("/register/register-student", { name, images });

      setMessage(res.data.message || "Student registered successfully!");
      setImages([]);
      setName("");
    } catch (err) {
      console.error("Register error:", err);
      // Network errors won't have response; show message accordingly
      const msg =
        err.response?.data?.error ||
        err.message ||
        "Error registering student";
      setMessage(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-center">Register Student</h2>

      <div className="flex justify-center">
        <CameraCapture onCapture={handleCapture} />
      </div>

      <div className="flex justify-center space-x-3">
        <input
          type="text"
          placeholder="Enter Student Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="border p-2 rounded-lg w-64 shadow"
        />

        <button
          onClick={sendRegister}
          disabled={loading}
          className="px-5 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 shadow disabled:opacity-50"
        >
          {loading ? "Registering..." : "Register"}
        </button>
      </div>

      <p className="text-center text-gray-700">{message}</p>

      <h4 className="text-center text-lg font-medium">
        Captured Images:{" "}
        <span className="text-blue-600">{images.length}</span>
      </h4>
    </div>
  );
}
