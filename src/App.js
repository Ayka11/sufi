// Updated App.js
import React, { useState, useEffect } from "react";
import { FaMicrophone, FaStop, FaDownload } from "react-icons/fa";

const App = () => {
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);
  const [transcriptions, setTranscriptions] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [service, setService] = useState("azure");
  const [language, setLanguage] = useState("en-US");

  useEffect(() => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      console.warn("getUserMedia is not supported in this environment.");
      return;
    }

    navigator.mediaDevices.getUserMedia({ audio: true })
      .then((stream) => {
        const recorder = new MediaRecorder(stream);
        recorder.ondataavailable = (event) => {
          setAudioChunks((prev) => [...prev, event.data]);
        };
        setMediaRecorder(recorder);
      })
      .catch((err) => {
        console.error("Error accessing microphone:", err);
      });

    const savedTranscriptions = JSON.parse(localStorage.getItem("transcriptions")) || [];
    setTranscriptions(savedTranscriptions);
  }, []);

  const startRecording = () => {
    setAudioChunks([]);
    mediaRecorder?.start();
    setIsRecording(true);
  };

  const stopRecording = () => {
    mediaRecorder?.stop();
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

        const updatedTranscriptions = [...transcriptions, newEntry];
        setTranscriptions(updatedTranscriptions);
        localStorage.setItem("transcriptions", JSON.stringify(updatedTranscriptions));
      })
      .catch((err) => console.error("Error:", err));
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
        <button className="download-button" onClick={() => {}}>
          <FaDownload /> Download Log
        </button>
      </div>
    </div>
  );
};

export default App;
