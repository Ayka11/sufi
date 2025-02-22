import React, { useState, useEffect } from "react";
import { FaMicrophone, FaStop, FaDownload } from "react-icons/fa";
import { io } from "socket.io-client"; // Import socket.io-client

const App = () => {
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);
  const [transcriptions, setTranscriptions] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [service, setService] = useState("azure");
  const [language, setLanguage] = useState("en-US");
  const [,, setSocket] = useState(null);  // New state to hold socket connection
  const [timeoutId, setTimeoutId] = useState(null);  // For silence detection

  // Initialize socket connection on component mount
  useEffect(() => {
    const newSocket = io("https://transkripsiya-backend.azurewebsites.net/", {
      transports: ["websocket"],  // Force WebSocket transport
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
  }, [setSocket]); // Add setSocket as a dependency to fix ESLint warning

  // Handle microphone access and MediaRecorder setup
  useEffect(() => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      console.warn("getUserMedia is not supported in this environment.");
      return;
    }

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
      });

    const savedTranscriptions = JSON.parse(localStorage.getItem("transcriptions")) || [];
    setTranscriptions(savedTranscriptions);
  }, []); // No need to update the dependency array here

  // Start recording audio
  const startRecording = () => {
    setAudioChunks([]);
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

  // Send audio to backend for transcription
  const sendAudioToBackend = (audioBlob) => {
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

        const updatedTranscriptions = [...transcriptions, newEntry];
        setTranscriptions(updatedTranscriptions);
        localStorage.setItem("transcriptions", JSON.stringify(updatedTranscriptions));
      })
      .catch((err) => console.error("Error:", err));
  };

  // Handle silence detection to automatically send audio to backend after a pause
  const detectSilence = () => {
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
  };

  // Monitor audio data availability and silence detection
  useEffect(() => {
    if (audioChunks.length > 0) {
      detectSilence();
    }
  }, [audioChunks, detectSilence]); // Add detectSilence to the dependency array

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

      <div className="transcriptions">
        <h2>Transcriptions:</h2>
        {transcriptions.map((entry, index) => (
          <div key={index}>
            <strong>{entry.timestamp}</strong>: {entry.text}
          </div>
        ))}
      </div>
    </div>
  );
};

export default App;
