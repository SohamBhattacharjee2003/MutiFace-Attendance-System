import React, { useState } from "react";
import CameraCapture from "../components/CameraCapture";
import axios from "axios";

export default function Register() {
  const [name, setName] = useState("");
  const [images, setImages] = useState([]);
  const [message, setMessage] = useState("");

  const handleCapture = (img) => setImages([...images, img]);

  const sendRegister = async () => {
    if (!name || images.length < 5) {
      alert("Enter name & capture at least 5 images");
      return;
    }

    const res = await axios.post("http://127.0.0.1:5000/register-student", {
      name,
      images,
    });

    setMessage("Student registered successfully! Retrain model now.");
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
          className="px-5 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 shadow"
        >
          Register
        </button>
      </div>

      <p className="text-center text-gray-700">{message}</p>

      <h4 className="text-center text-lg font-medium">
        Captured Images: <span className="text-blue-600">{images.length}</span>
      </h4>
    </div>
  );
}
