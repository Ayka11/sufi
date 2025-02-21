import React, { useState, useEffect } from "react";
import { FaMicrophone, FaStop, FaDownload } from "react-icons/fa";

const App = () => {
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);
  const [transcriptions, setTranscriptions] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [service, setService] = useState("azure"); // Default to Azure
  const [language, setLanguage] = useState("en-US"); // Default to English

  useEffect(() => {
    // Initialize media recorder
    navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
      const recorder = new MediaRecorder(stream);
      recorder.ondataavailable = (event) => {
        setAudioChunks((prev) => [...prev, event.data]);
      };
      setMediaRecorder(recorder);
    });

    // Load previous transcriptions from local storage
    const savedTranscriptions = JSON.parse(localStorage.getItem("transcriptions")) || [];
    setTranscriptions(savedTranscriptions);
  }, []);

  const startRecording = () => {
    setAudioChunks([]);
    mediaRecorder.start();
    setIsRecording(true);
  };

  const stopRecording = () => {
    mediaRecorder.stop();
    setIsRecording(false);

    mediaRecorder.onstop = () => {
      const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
      sendAudioToBackend(audioBlob);
    };
  };

  const sendAudioToBackend = (audioBlob) => {
    const formData = new FormData();
    formData.append("audio", audioBlob, "audio.wav");
    formData.append("service", service);
    formData.append("language", language);

    fetch("https://transkripsiya-backend.azurewebsites.net/upload_audio", {
      method: "POST",
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        const newEntry = {
          timestamp: new Date().toLocaleString(),
          text: data.transcription || "No transcription available",
        };

        // Update state and store in local storage
        const updatedTranscriptions = [...transcriptions, newEntry];
        setTranscriptions(updatedTranscriptions);
        localStorage.setItem("transcriptions", JSON.stringify(updatedTranscriptions));
      })
      .catch((err) => console.error("Error:", err));
  };

  const downloadTranscription = () => {
    if (transcriptions.length === 0) {
      alert("No transcription available to download.");
      return;
    }

    let textContent = "Transcription Log:\n\n";
    transcriptions.forEach((entry) => {
      textContent += `[${entry.timestamp}] ${entry.text}\n`;
    });

    const blob = new Blob([textContent], { type: "text/plain" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "transcription_log.txt";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="App">
      <h1>Real-Time Transcription</h1>

      <div className="controls">
        <label>Language:</label>
        <select onChange={(e) => setLanguage(e.target.value)} value={language}>
          <option value="en-US">English</option>
          <option value="az-AZ">Azerbaijani</option>
          <option value="fr-FR">French</option>
          <option value="es-ES">Spanish</option>
        </select>

        <label>Service:</label>
        <select onChange={(e) => setService(e.target.value)} value={service}>
          <option value="azure">Azure</option>
          <option value="google">Google</option>
        </select>

        <button className="start-button" onClick={startRecording} disabled={isRecording}>
          <FaMicrophone /> Start Recording
        </button>
        <button className="stop-button" onClick={stopRecording} disabled={!isRecording}>
          <FaStop /> Stop Recording
        </button>
        <button className="download-button" onClick={downloadTranscription}>
          <FaDownload /> Download Log
        </button>
      </div>

      <div className="transcription-box">
        <h3>Transcription:</h3>
        {transcriptions.length === 0 ? (
          <p>No transcriptions yet.</p>
        ) : (
          transcriptions.map((entry, index) => (
            <p key={index}>
              <strong>[{entry.timestamp}]</strong> {entry.text}
            </p>
          ))
        )}
      </div>
    </div>
  );
};

export default App;
