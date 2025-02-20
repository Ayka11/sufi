// TranscriptionComponent.js
import React from 'react';

const TranscriptionComponent = ({ transcription }) => {
  return (
    <div className="transcription">
      <h3>Transcription:</h3>
      <p>{transcription}</p>
    </div>
  );
};

export default TranscriptionComponent;
