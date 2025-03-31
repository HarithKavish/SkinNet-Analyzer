// src/components/Camera.js
import { useState, useRef } from "react";

const SkinCheckButton = () => {
  const [capturedImage, setCapturedImage] = useState(null);
  const [stream, setStream] = useState(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  const requestCameraPermission = async () => {
    try {
      await navigator.permissions.query({ name: "camera" });
      startCamera();
    } catch (error) {
      alert("Camera permission is required to capture images.");
      console.error("Error requesting camera permission:", error);
    }
  };

  const startCamera = async () => {
    try {
      const userStream = await navigator.mediaDevices.getUserMedia({ video: true });
      setStream(userStream);
      if (videoRef.current) {
        videoRef.current.srcObject = userStream;
      }
    } catch (error) {
      alert("Camera access is required to capture images.");
      console.error("Error accessing camera:", error);
    }
  };

  const captureImage = () => {
    if (videoRef.current && canvasRef.current) {
      const context = canvasRef.current.getContext("2d");
      canvasRef.current.width = videoRef.current.videoWidth;
      canvasRef.current.height = videoRef.current.videoHeight;
      context.drawImage(videoRef.current, 0, 0);
      setCapturedImage(canvasRef.current.toDataURL("image/png"));
      stopCamera();
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
  };

  const handleMobileCapture = (event) => {
    const file = event.target.files[0];
    if (file) {
      const imageUrl = URL.createObjectURL(file);
      setCapturedImage(imageUrl);
    }
  };

  return (
    <div className="camera-container" style={{ textAlign: "center" }}>
      {!capturedImage && (
        <div>
          {navigator.mediaDevices && navigator.mediaDevices.getUserMedia ? (
            <button className="gradient-button" onClick={requestCameraPermission}>
              CHECK YOUR SKIN NOW
            </button>
          ) : (
            <label className="gradient-button">
              CHECK YOUR SKIN NOW
              <input
                type="file"
                accept="image/*"
                capture="environment"
                onChange={handleMobileCapture}
                style={{ display: "none" }}
              />
            </label>
          )}
        </div>
      )}
      {stream && (
        <div>
          <video ref={videoRef} autoPlay playsInline style={{ width: "100%", maxWidth: "400px", borderRadius: "10px" }} />
          <button onClick={captureImage} style={{ margin: "10px", padding: "10px", borderRadius: "5px", backgroundColor: "#ff4d4d", color: "white", border: "none", cursor: "pointer" }}>Capture</button>
          <button onClick={stopCamera} style={{ margin: "10px", padding: "10px", borderRadius: "5px", backgroundColor: "#333", color: "white", border: "none", cursor: "pointer" }}>Stop Camera</button>
        </div>
      )}
      {capturedImage && (
        <div>
          <h3>Preview:</h3>
          
          <img src={capturedImage} alt="Captured" style={{ width: "100%", maxWidth: "200px", borderRadius: "10px" }} />
          <button onClick={() => setCapturedImage(null)} style={{ margin: "10px", padding: "10px", borderRadius: "5px", backgroundColor: "#ff4d4d", color: "white", border: "none", cursor: "pointer" }}>Retake</button>
        </div>
      )}
      <canvas ref={canvasRef} style={{ display: "none" }}></canvas>
    </div>
  );
};

export default SkinCheckButton;
