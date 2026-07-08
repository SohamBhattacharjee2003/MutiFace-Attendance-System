import React, { useRef, useEffect, useState } from "react";
import { Camera, Square, StopCircle, Video, VideoOff } from "lucide-react";
import { predictFace } from "../utils/api";

export default function LiveAttendance() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);          // reliable handle for cleanup
  const intervalRef = useRef(null);
  const busyRef = useRef(false);           // prevents overlapping predict calls
  const [isAttendanceActive, setIsAttendanceActive] = useState(false);
  const [detectedFaces, setDetectedFaces] = useState([]);
  const [cameraOn, setCameraOn] = useState(true);

  useEffect(() => {
    startCamera();
    return () => {
      stopCamera();
      stopAttendance();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { width: 1280, height: 720 },
      });
      streamRef.current = mediaStream;
      if (videoRef.current) videoRef.current.srcObject = mediaStream;
      setCameraOn(true);
    } catch (err) {
      console.error("Camera error:", err);
      alert("Could not access camera");
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (videoRef.current) videoRef.current.srcObject = null;
    setCameraOn(false);
  };

  const toggleCamera = () => {
    if (cameraOn) {
      stopAttendance();     // can't scan without a camera
      stopCamera();
    } else {
      startCamera();
    }
  };

  const startAttendance = () => {
    if (!cameraOn) { alert("Turn the camera on first."); return; }
    setIsAttendanceActive(true);
    setDetectedFaces([]);

    intervalRef.current = setInterval(() => {
      captureAndPredict();
    }, 1500); // give CPU ArcFace time; the busy-guard prevents pile-ups
  };

  const stopAttendance = () => {
    setIsAttendanceActive(false);
    setDetectedFaces([]);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  const captureAndPredict = async () => {
    if (!videoRef.current || !canvasRef.current) return;
    if (busyRef.current || !streamRef.current) return;   // skip if a request is in flight
    busyRef.current = true;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);

    const base64Image = canvas.toDataURL("image/jpeg", 0.8);

    try {
      const response = await predictFace(base64Image);
      if (response?.results) {
        setDetectedFaces(response.results);
      }
    } catch (err) {
      console.error("Prediction error:", err);
    } finally {
      busyRef.current = false;
    }
  };

  const drawFaceBoxes = () => {
    if (!videoRef.current || detectedFaces.length === 0) return null;

    const video = videoRef.current;
    const videoWidth = video.offsetWidth;
    const videoHeight = video.offsetHeight;
    const scaleX = videoWidth / video.videoWidth;
    const scaleY = videoHeight / video.videoHeight;

    return detectedFaces.map((face, index) => {
      const [x1, y1, x2, y2] = face.box;
      const left = x1 * scaleX;
      const top = y1 * scaleY;
      const width = (x2 - x1) * scaleX;
      const height = (y2 - y1) * scaleY;

      const isKnown = face.isKnown;
      const color = isKnown ? "#10b981" : "#ef4444"; // Green for known, Red for unknown

      return (
        <div
          key={index}
          style={{
            position: "absolute",
            left: `${left}px`,
            top: `${top}px`,
            width: `${width}px`,
            height: `${height}px`,
            border: `3px solid ${color}`,
            boxShadow: `0 0 10px ${color}`,
            pointerEvents: "none",
            zIndex: 10,
          }}
        >
          <div
            style={{
              position: "absolute",
              top: "-30px",
              left: "0",
              backgroundColor: "#070c24",
              color: "white",
              padding: "4px 12px",
              borderRadius: "4px",
              fontSize: "14px",
              fontWeight: "600",
              whiteSpace: "nowrap",
              boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
            }}
          >
            {face.name} ({Math.round(face.confidence * 100)}%)
          </div>
        </div>
      );
    });
  };

  return (
    <div className="min-h-screen bg-[#070c24] pt-20 pb-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-[#070c24] rounded-lg shadow-md p-6 mb-6">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div className="flex items-center space-x-4">
              <div className="bg-blue-600 p-3 rounded-lg">
                <Camera className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-2xl lg:text-3xl font-bold text-gray-300">
                  Live Face Attendance
                </h1>
                <p className="text-white/60 mt-1">
                  {isAttendanceActive ? (
                    <span className="flex items-center gap-2">
                      <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                      Detecting faces...
                    </span>
                  ) : (
                    "Click Start to begin attendance"
                  )}
                </p>
              </div>
            </div>

            {/* Control Buttons */}
            <div className="flex flex-wrap gap-3">
              {!isAttendanceActive ? (
                <button
                  onClick={startAttendance}
                  disabled={!cameraOn}
                  className="flex items-center space-x-2 bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition-colors shadow-md hover:shadow-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Square className="w-5 h-5" />
                  <span>Start Attendance</span>
                </button>
              ) : (
                <button
                  onClick={stopAttendance}
                  className="flex items-center space-x-2 bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700 transition-colors shadow-md hover:shadow-lg font-medium"
                >
                  <StopCircle className="w-5 h-5" />
                  <span>Stop Attendance</span>
                </button>
              )}

              <button
                onClick={toggleCamera}
                className={`flex items-center space-x-2 px-6 py-3 rounded-lg font-medium border transition-colors
                  ${cameraOn
                    ? "border-red-400/30 text-red-300 hover:bg-red-500/10"
                    : "border-emerald-400/30 text-emerald-300 hover:bg-emerald-500/10"}`}
              >
                {cameraOn ? <VideoOff className="w-5 h-5" /> : <Video className="w-5 h-5" />}
                <span>{cameraOn ? "Camera Off" : "Camera On"}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Video Feed with Face Detection */}
        <div className="bg-[#070c24] rounded-lg shadow-md p-6">
          <div className="relative w-full overflow-hidden rounded-lg" style={{ aspectRatio: "16/9" }}>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full bg-gray-900 object-cover"
            />
            {isAttendanceActive && (
              <div className="absolute inset-0 pointer-events-none">
                {drawFaceBoxes()}
              </div>
            )}
            {!cameraOn && (
              <div className="absolute inset-0 flex flex-col items-center justify-center gap-3
                              bg-[#05070f]/90 text-white/50">
                <VideoOff className="w-14 h-14" />
                <p className="text-sm">Camera is off — click “Camera On” to resume</p>
              </div>
            )}
          </div>
          <canvas ref={canvasRef} className="hidden" />

          {/* Legend */}
          {isAttendanceActive && (
            <div className="mt-6 flex items-center justify-center space-x-8 pb-4 border-b">
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 bg-green-500 rounded"></div>
                <span className="text-sm font-medium text-white/70">
                  Known Person
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 bg-red-500 rounded"></div>
                <span className="text-sm font-medium text-white/70">
                  Unknown Person
                </span>
              </div>
            </div>
          )}

          {/* Detection Stats */}
          {isAttendanceActive && detectedFaces.length > 0 && (
            <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white/5 border border-white/10 rounded-lg p-4 text-center">
                <p className="text-3xl font-bold text-blue-400">
                  {detectedFaces.length}
                </p>
                <p className="text-sm text-white/60 mt-1">Total Faces Detected</p>
              </div>
              <div className="bg-green-500/10 border border-green-400/20 rounded-lg p-4 text-center">
                <p className="text-3xl font-bold text-green-600">
                  {detectedFaces.filter((f) => f.isKnown).length}
                </p>
                <p className="text-sm text-white/60 mt-1">Known Persons</p>
              </div>
              <div className="bg-red-500/10 border border-red-400/20 rounded-lg p-4 text-center">
                <p className="text-3xl font-bold text-red-600">
                  {detectedFaces.filter((f) => !f.isKnown).length}
                </p>
                <p className="text-sm text-white/60 mt-1">Unknown Persons</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
