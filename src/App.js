import React, { useState, useEffect, useCallback } from "react";
import { FaMicrophone, FaStop, FaDownload } from "react-icons/fa";
import { io } from "socket.io-client"; // Import socket.io-client
import './App.css';  // Import the App.css file for styling

const App = () => {
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);
  const [transcriptions, setTranscriptions] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [service, setService] = useState("azure");
  const [language, setLanguage] = useState("en-US");
  const [, setSocket] = useState(null);  // New state to hold socket connection
  const [timeoutId, setTimeoutId] = useState(null);  // For silence detection

  // Initialize socket connection on component mount
  useEffect(() => {
    const newSocket = io("https://transkripsiya-backend.azurewebsites.net/", {
      transports: ["websocket"],  // Force WebSocket transport gg
    });

    setSocket(newSocket);

    // Listen for transcriptions from the backend
    newSocket.on("transcription", (data) => {
      console.log("Received transcription:", data.transcription);
      setTranscriptions((prev) => [
        ...prev,
        { timestamp: new Date().toLocaleString(), text: data.transcription },
      ]);
    });

    return () => {
      newSocket.disconnect();
    };
  }, []);

  // Handle microphone access and MediaRecorder setup
  useEffect(() => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      console.warn("getUserMedia is not supported in this environment.");
      alert("Your browser does not support microphone access. Please try a different browser.");
      return;
    }

    // Request microphone access
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then((stream) => {
        const recorder = new MediaRecorder(stream);
        recorder.ondataavailable = (event) => {
          console.log("Audio chunk available:", event.data);
          setAudioChunks((prev) => [...prev, event.data]);
        };
        setMediaRecorder(recorder);
      })
      .catch((err) => {
        console.error("Error accessing microphone:", err);
        // Handle the error, perhaps show an error message to the user
        if (err.name === "NotAllowedError") {
          alert("Microphone access was denied. Please allow microphone access and try again.");
        } else {
          alert("An error occurred while accessing the microphone.");
        }
      });

    // Load previous transcriptions from localStorage
    const savedTranscriptions = JSON.parse(localStorage.getItem("transcriptions")) || [];
    setTranscriptions(savedTranscriptions);
  }, []);

  // Wrap sendAudioToBackend in useCallback to prevent unnecessary re-creations
  const sendAudioToBackend = useCallback((audioBlob) => {
    console.log("Sending audio to backend:", audioBlob);
    const formData = new FormData();
    formData.append("audio", audioBlob, "audio.ogg"); // Send as OGG format
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

        // Save only the latest transcription
        const updatedTranscriptions = [newEntry]; // Overwrite with the latest transcription
        setTranscriptions(updatedTranscriptions);
        localStorage.setItem("transcriptions", JSON.stringify(updatedTranscriptions));
      })
      .catch((err) => console.error("Error:", err));
  }, [service, language]);  // Added service and language as dependencies to ensure the callback stays up-to-date

  // Handle silence detection to automatically send audio to backend after a pause
  const detectSilence = useCallback(() => {
    // Clear previous timeout if any
    if (timeoutId) {
      clearTimeout(timeoutId);
    }

    // Set a new timeout for 2 seconds of silence (you can adjust this)
    const id = setTimeout(() => {
      if (audioChunks.length > 0) {
        const audioBlob = new Blob(audioChunks, { type: "audio/ogg" });
        sendAudioToBackend(audioBlob); // Send audio after silence
        setAudioChunks([]); // Clear audio chunks after sending
      }
    }, 2000); // Adjust silence timeout as needed
    setTimeoutId(id);
  }, [audioChunks, timeoutId, sendAudioToBackend]);  // Added sendAudioToBackend to dependencies

  // Monitor audio data availability and silence detection
  useEffect(() => {
    if (audioChunks.length > 0) {
      detectSilence();
    }
  }, [audioChunks, detectSilence]);

  // Start recording audio
  const startRecording = () => {
    setAudioChunks([]); // Reset audio chunks before starting
    mediaRecorder?.start();
    setIsRecording(true);
    console.log("Recording started...");
  };

  // Stop recording audio
  const stopRecording = () => {
    mediaRecorder?.stop();
    setIsRecording(false);
    console.log("Recording stopped...");

    // When stop is triggered, send audio to backend
    mediaRecorder.onstop = () => {
      const audioBlob = new Blob(audioChunks, { type: "audio/ogg" }); // Using OGG format as output
      sendAudioToBackend(audioBlob);
    };
  };

  // Download the latest transcription log
  const downloadLog = () => {
    const latestTranscription = transcriptions[0]; // Only the latest transcription
    const blob = new Blob([JSON.stringify(latestTranscription, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "transcription.json";
    a.click();
    URL.revokeObjectURL(url);
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
        <button className="download-button" onClick={downloadLog}>
          <FaDownload /> Download Log
        </button>
      </div>

      <div className="transcriptions">
        <h2>Latest Transcription:</h2>
        {transcriptions.length > 0 && (
          <div>
            <strong>{transcriptions[0].timestamp}</strong>: {transcriptions[0].text}
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
