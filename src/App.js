import React, { useState, useEffect } from 'react';
import './App.css';
import { FaMicrophone, FaStop, FaDownload } from 'react-icons/fa';

const App = () => {
  const [transcription, setTranscription] = useState('');
  const [language, setLanguage] = useState('en-US');
  const [service, setService] = useState('azure'); // Default to Azure
  const [isRecording, setIsRecording] = useState(false);

  useEffect(() => {
    const intervalId = setInterval(() => {
      fetch('https://transkripsiya-backend.azurewebsites.net/transcription')
        .then(response => response.json())
        .then(data => {
          setTranscription(data.transcription);
        })
        .catch((err) => console.error('Error fetching transcription:', err));
    }, 2000);

    return () => clearInterval(intervalId);
  }, []);

  const startTranscription = () => {
    fetch('https://transkripsiya-backend.azurewebsites.net/start', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ language, service }), // Send service type (Azure or Google)
    })
      .then(response => response.json())
      .then(data => {
        if (data.message === 'Speech recognition started.') {
          setIsRecording(true);
        }
      })
      .catch((err) => console.error('Error starting transcription:', err));
  };

  const stopTranscription = () => {
    fetch('https://transkripsiya-backend.azurewebsites.net/stop', {
      method: 'POST',
    })
      .then(response => response.json())
      .then(data => {
        if (data.message === 'Speech recognition stopped.') {
          setIsRecording(false);
        }
      })
      .catch((err) => console.error('Error stopping transcription:', err));
  };

  const downloadFile = () => {
    window.location.href = 'https://transkripsiya-backend.azurewebsites.net/downloads';
  };

  return (
    <div className="App">
      <h1>Real-Time Transcription</h1>

      <div className="controls">
        <select onChange={(e) => setLanguage(e.target.value)} value={language}>
          <option value="en-US">English</option>
          <option value="az-AZ">Azerbaijani</option>
          <option value="fr-FR">French</option>
          <option value="es-ES">Spanish</option>
        </select>

        <select onChange={(e) => setService(e.target.value)} value={service}>
          <option value="azure">Azure</option>
          <option value="google">Google</option>
        </select>

        <div className="action-buttons">
          <button className="start-button" onClick={startTranscription} disabled={isRecording}>
            <FaMicrophone /> Start Transcription
          </button>
          <button className="stop-button" onClick={stopTranscription} disabled={!isRecording}>
            <FaStop /> Stop Transcription
          </button>
        </div>

        <button className="download-button" onClick={downloadFile}>
          <FaDownload /> Download Transcription Log
        </button>
      </div>

      <div className="transcription-box">
        <div className="transcription-text">{transcription}</div>
      </div>
    </div>
  );
};

export default App;
