import React, { useRef, useState } from "react";
import { X, Camera, Upload, Trash2 } from "lucide-react";
import axios from "axios";
import Webcam from "react-webcam";
import { motion } from "framer-motion";

export default function AddImagesModal({ student, onClose }) {
  const webcamRef = useRef(null);
  const [capturedImages, setCapturedImages] = useState([]);
  const [uploading, setUploading] = useState(false);

  const captureImage = () => {
    if (!webcamRef.current) {
      alert("Camera not ready");
      return;
    }
    
    const imageSrc = webcamRef.current.getScreenshot();
    if (imageSrc) {
      setCapturedImages([...capturedImages, imageSrc]);
      console.log("Image captured, total:", capturedImages.length + 1);
    }
  };

  const removeImage = (index) => {
    setCapturedImages(capturedImages.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (capturedImages.length === 0) {
      alert("Please capture at least one image");
      return;
    }

    setUploading(true);
    try {
      const response = await axios.post("http://localhost:5000/update-student", {
        name: student.name,
        images: capturedImages,
      });

      console.log("Upload response:", response.data);
      alert(
        `Successfully added ${capturedImages.length} new image(s) for ${student.name}!\nTotal samples: ${response.data.total_samples}`
      );
      onClose();
    } catch (error) {
      console.error("Upload error:", error);
      const errorMsg =
        error.response?.data?.error || error.message || "Unknown error";
      alert(`Failed to update images: ${errorMsg}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-[#0a1128] border border-white/20 rounded-2xl max-w-4xl w-full my-8">
        {/* Header */}
        <div className="sticky top-0 bg-[#0a1128] border-b border-white/10 px-6 py-4 flex items-center justify-between z-10 rounded-t-2xl">
          <div>
            <h2 className="text-2xl font-bold text-white flex items-center gap-2">
              <Camera className="w-6 h-6 text-blue-400" />
              Add More Images
            </h2>
            <p className="text-gray-400 mt-1">
              For:{" "}
              <span className="font-semibold text-blue-400">{student.name}</span> (
              {student.samples || 0} existing images)
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/10 rounded-lg transition-colors"
          >
            <X className="w-6 h-6 text-gray-400" />
          </button>
        </div>

        <div className="p-6 max-h-[calc(90vh-100px)] overflow-y-auto">
          {/* Camera Section */}
          <div className="mb-6">
            <div className="w-full overflow-hidden rounded-2xl border border-blue-500/20 shadow-[0_0_25px_rgba(0,110,255,0.25)]">
              <Webcam
                ref={webcamRef}
                mirrored
                screenshotFormat="image/jpeg"
                videoConstraints={{
                  width: 1280,
                  height: 720,
                  facingMode: "user",
                }}
                className="w-full rounded-2xl"
              />
            </div>
            
            {/* Capture Button */}
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={captureImage}
              className="w-full mt-4 py-4 bg-blue-600 hover:bg-blue-700 text-white text-lg font-semibold rounded-xl transition shadow-[0_0_25px_rgba(0,110,255,0.45)] flex items-center justify-center gap-2"
            >
              <Camera className="w-5 h-5" />
              Capture Image
            </motion.button>
          </div>

          {/* Tips */}
          <div className="bg-blue-600/10 border border-blue-500/20 rounded-xl p-4 mb-6">
            <h3 className="font-semibold text-blue-400 mb-2 flex items-center gap-2">
              <span>💡</span> Tips for Better Recognition:
            </h3>
            <ul className="text-sm text-gray-300 space-y-1.5">
              <li>✓ Capture from different angles (front, left, right)</li>
              <li>✓ Use good lighting conditions</li>
              <li>✓ Try different facial expressions</li>
              <li>✓ Add 5-10 more images for best results</li>
              <li>✓ Ensure your face is clearly visible and centered</li>
            </ul>
          </div>

          {/* Captured Images */}
          {capturedImages.length > 0 && (
            <div>
              <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
                <span className="text-green-400">✓</span>
                Captured Images ({capturedImages.length})
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 mb-6">
                {capturedImages.map((img, index) => (
                  <div key={index} className="relative group">
                    <img
                      src={img}
                      alt={`Capture ${index + 1}`}
                      className="w-full h-32 object-cover rounded-lg border-2 border-white/20 group-hover:border-blue-400 transition-colors"
                    />
                    <button
                      onClick={() => removeImage(index)}
                      className="absolute top-2 right-2 bg-red-600 text-white p-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-700"
                      title="Remove image"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                    <div className="absolute bottom-2 left-2 bg-black/70 text-white text-xs px-2 py-1 rounded font-medium">
                      #{index + 1}
                    </div>
                  </div>
                ))}
              </div>

              {/* Upload Button */}
              <button
                onClick={handleUpload}
                disabled={uploading}
                className="w-full bg-gradient-to-r from-green-600 to-emerald-600 text-white px-6 py-4 rounded-lg hover:from-green-700 hover:to-emerald-700 transition-all flex items-center justify-center space-x-2 font-semibold disabled:opacity-50 disabled:cursor-not-allowed shadow-lg text-lg"
              >
                {uploading ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Uploading...</span>
                  </>
                ) : (
                  <>
                    <Upload className="w-6 h-6" />
                    <span>
                      Update Training Data ({capturedImages.length}{" "}
                      {capturedImages.length === 1 ? "image" : "images"})
                    </span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}