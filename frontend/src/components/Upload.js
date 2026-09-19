import React, { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import axios from "axios";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";
// import Footer from "./Footer";
import "./Upload.css";

function Upload() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [location, setLocation] = useState(""); // Store user-entered location
  const [result, setResult] = useState("");
  const [backendStatus, setBackendStatus] = useState("Checking Server Status...");
  const [serverState, setServerState] = useState("checking"); // checking | waking | online | offline
  const [questions, setQuestions] = useState([]); // Stores symptom questions
  const [diseases, setDiseases] = useState([]); // Candidate diseases returned by /upload
  const [answers, setAnswers] = useState({}); // Stores user responses
  const [confirmed, setConfirmed] = useState(null); // { disease, severity } from /confirm_symptoms, kept for retry
  const [awaitingSymptoms, setAwaitingSymptoms] = useState(false); // Waiting for symptom input
  const [finalReport, setFinalReport] = useState(null); // Stores full AI-generated report
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isOutputReady, setIsOutputReady] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false); // Tracks button loading state
  const outputRef = useRef(null);
  const [isUploading, setIsUploading] = useState(false); // Tracks Submit button loading state
  const BASE_URL = process.env.REACT_APP_BACKEND_API_URL;

  useEffect(() => {
    // Simulate output completion
    setTimeout(() => setIsOutputReady(true), 2000); // Adjust based on real output loading time
  }, []);

  useEffect(() => {
    let cancelled = false;
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

    // Render's free tier sleeps when idle, so the first requests can fail for up to a
    // minute while it wakes. Keep retrying and say so, instead of showing "Offline".
    const checkBackendStatus = async () => {
      for (let attempt = 0; attempt < 12 && !cancelled; attempt++) {
        try {
          await axios.get(`${BASE_URL}/api/status`, { timeout: 10000 });
          if (!cancelled) {
            setBackendStatus("Server Status: Online ✅");
            setServerState("online");
          }
          return;
        } catch (error) {
          if (cancelled) return;
          console.error("Error connecting to backend:", error);
          setBackendStatus("Server Status: Waking up the server, this can take up to a minute... ⏳");
          setServerState("waking");
          await sleep(3000);
        }
      }
      if (!cancelled) {
        setBackendStatus("Server Status: Offline ❌ . ❗Disclaimer: This is site is for Demo purposes only. Do not use for actual diagnosis❗");
        setServerState("offline");
      }
    };

    checkBackendStatus();
    return () => {
      cancelled = true;
    };
  }, [BASE_URL]);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setPreview(URL.createObjectURL(selectedFile));

    }
  };

  const handleUpload = async () => {
    if (!file) {
      alert("Please upload an image.");
      return;
    }

    if (!location.trim()) {
      alert("Please enter your location.");
      return;
    }

    setIsUploading(true); // Start loading animation

    const formData = new FormData();
    formData.append("file", file);
    formData.append('location', location); // add location too

    try {
      const response = await axios.post(`${BASE_URL}/api/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      if (response.data.questions) {
        setQuestions(response.data.questions);
        setDiseases(response.data.diseases || []);
        setAwaitingSymptoms(true);
        setAnswers({}); // Reset answers
      } else {
        setResult(`Disease: ${response.data.disease}, Severity: ${response.data.severity}`);
      }
    } catch (error) {
      console.error("Error uploading file:", error);
      alert("Error processing image.");
    } finally {
      setIsUploading(false); // Stop loading animation
    }
  };


  // ✅ Show alert AFTER `result` updates
  useEffect(() => {
    if (result) {
      alert(result);
    }
  }, [result]);


  const handleAnswerChange = (symptom, value) => {
    setAnswers(prevAnswers => ({
      ...prevAnswers,
      [symptom]: value // Store answer using symptom as key
    }));
  };

  const handleSubmitSymptoms = async () => {
    if (!location.trim()) {
      setResult("Please enter your location before submitting symptoms.");
      return;
    }

    setIsSubmitting(true); // Show loading icon

    try {
      const response = await axios.post(`${BASE_URL}/api/confirm_symptoms`, { answers, diseases });
      setConfirmed({ disease: response.data.disease, severity: response.data.severity });
      await fetchFullDiseaseInfo(response.data.disease, response.data.severity);
    } catch (error) {
      console.error("Error confirming symptoms:", error);
      setResult("Error processing symptoms.");
    } finally {
      setIsSubmitting(false); // Always stop the spinner, success or failure
    }
  };


  const fetchFullDiseaseInfo = async (disease, severity) => {
    setIsSubmitted(true); // Symptoms were submitted either way; hide "Submit Responses"
    try {
      console.log(`Sending request for Disease: ${disease}, Severity: ${severity}, Location: ${location}`);

      const response = await axios.post(`${BASE_URL}/api/get_disease_info`, {
        disease,
        severity,
        location,
      });

      // If severity is "Out of Class", set special message & stop further display
      if (response.data.out_of_class) {
        setFinalReport({ outOfClass: true });
        return;
      }

      console.log("Received AI Response:", response.data);
      setFinalReport(response.data);
    } catch (error) {
      console.error("Error fetching disease info:", error.response?.data || error.message);
      setFinalReport({ error: "Failed to retrieve additional details." });
    }
  };


  const handleDownloadPDF = () => {
    const element = outputRef.current;

    html2canvas(element, { scale: 2, useCORS: true }).then((canvas) => {
      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF("p", "mm", "a4");

      const imgWidth = 210; // A4 width in mm
      const pageHeight = 297; // A4 height in mm  
      const imgHeight = (canvas.height * imgWidth) / canvas.width;

      let y = 0; // Position to start adding images

      while (y < imgHeight) {
        pdf.addImage(imgData, "PNG", 0, -y, imgWidth, imgHeight);
        y += pageHeight; // Move to the next page
        if (y < imgHeight) pdf.addPage(); // Add new page if content is not fully captured
      }

      pdf.save("SkinNet_Analyzer_Report.pdf");
    });
  };

  return (
    <div ref={outputRef} className="upload-container">
      <p className="backend-status">{backendStatus}</p>
      {serverState === "checking" || serverState === "waking" ? null :
        serverState === "online" ? (
          <>
            <div className="title-divv">
              <h3>❗Disclaimer: This website is for Demonstration Purposes only. Don't use for Real Diagnosis❗</h3>
              <h1 className="upload-title">Skin Disease Diagnosis</h1>
            </div>

            {!preview && (
              <>
                <label htmlFor="file-upload" className="upload-label">Upload Image</label>
                <input
                  id="file-upload"
                  type="file"
                  className="upload-input"
                  accept="image/*"
                  onChange={handleFileChange}
                />
              </>
            )}

            {preview && (
              <div className="image-preview">
                <h3>Image Preview:</h3>
                <img src={preview} alt="Selected Preview" className="preview-img" />
              </div>
            )}

            <div className="location-input">
              <h4 id="location-title">Enter your Location:</h4>
              <input
                id="location-box"
                type="text"
                placeholder="E.g., Chennai, India"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                autoComplete="address-level2"
              />
            </div>

            {!awaitingSymptoms ? (
              <button className="upload-button" onClick={handleUpload} disabled={isUploading}>
                {isUploading ? (
                  <span className="loading-spinner"></span> // Show loading animation
                ) : (
                  "Submit"
                )}
              </button>
            ) : (
              <div className="symptom-questions">
                <h2>Answer the following questions:</h2>
                {questions && Object.entries(questions).map(([symptom, question], index) => (
                  <div key={index} className="question">
                    <p>{question}</p>
                    <button
                      className={answers[symptom] === "1" ? "selected" : ""}
                      onClick={() => handleAnswerChange(symptom, "1")}
                    >
                      Yes
                    </button>
                    <button
                      className={answers[symptom] === "0" ? "selected" : ""}
                      onClick={() => handleAnswerChange(symptom, "0")}
                    >
                      No
                    </button>
                  </div>
                ))}
                {!isSubmitted && (
                  <button className="upload-button" onClick={handleSubmitSymptoms} disabled={isSubmitting}>
                    {isSubmitting ? (
                      <span className="loading-spinner"></span> // Show loading icon
                    ) : (
                      "Submit Responses"
                    )}
                  </button>
                )}
              </div>
            )}

            {/* If "Out of Class", display only the message */}
            {finalReport?.outOfClass ? (
              <h2 className="error-message">Disease Out of Class</h2>
            ) : finalReport?.error ? (
              <div className="disease-report">
                <h2 className="error-message">{finalReport.error}</h2>
                <p>The AI service may be temporarily unavailable. Please try again.</p>
                <button
                  className="upload-button"
                  onClick={() => confirmed && fetchFullDiseaseInfo(confirmed.disease, confirmed.severity)}
                >
                  Retry
                </button>
              </div>
            ) : finalReport && (
              <div className="disease-report">
                <h2>Diagnosed Disease</h2>
                <p><strong>Disease:</strong> {finalReport.disease}</p>
                <p><strong>Severity:</strong> {finalReport.severity}</p>

                <h2>Symptoms & Care Instructions</h2>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {finalReport.symptoms_care}
                </ReactMarkdown>

                <h2 id="page-break">Nearby Hospitals</h2>
                <div className="hospital-list">
                  {finalReport.hospitals && finalReport.hospitals.map((hospital, index) => (
                    <div key={index} className="hospital-card" onClick={() => window.open(hospital.maps_url, "_blank")}>
                      <h3>{index + 1}. {hospital.name}</h3>
                      <p>{hospital.location}</p>
                      <img
                        src="https://cdn.mos.cms.futurecdn.net/6MTaNZBnesPxmrTfRCEbQN-1152-80.png"
                        alt={`Location of ${hospital.name}`}
                        className="hospital-map"
                      />
                    </div>
                  ))}
                </div>
                {isOutputReady && (
                  <button onClick={handleDownloadPDF} className="download-btn">
                    Download as PDF
                  </button>
                )}
              </div>
            )}
          </>
        ) : (
          <h2 className="offline-message">Server Offline. Please try after some time.</h2>
        )}
    </div>
  );
  // <Footer/>

}

export default Upload;