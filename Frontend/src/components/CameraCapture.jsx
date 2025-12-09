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
        width={480}
        height={360}
        screenshotFormat="image/jpeg"
        videoConstraints={{
          width: 640,
          height: 480,
          facingMode: "user",
        }}
        className="rounded-lg shadow-lg"
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
