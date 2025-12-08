import React, { useRef } from "react";
import Webcam from "react-webcam";

export default function CameraCapture({ onCapture }) {
  const ref = useRef(null);

  const capture = () => {
    const imgSrc = ref.current.getScreenshot();
    onCapture(imgSrc);
  };

  return (
    <div className="flex flex-col items-center space-y-4">
      <Webcam
        ref={ref}
        screenshotFormat="image/jpeg"
        videoConstraints={{ facingMode: "user" }}
        className="rounded-lg shadow-lg w-[320px]"
      />

      <button
        onClick={capture}
        className="px-6 py-2 bg-blue-600 text-white rounded-lg shadow-md hover:bg-blue-700 transition"
      >
        Capture Image
      </button>
    </div>
  );
}
