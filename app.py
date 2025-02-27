from flask import Flask, render_template, request, jsonify
import os
import tempfile
import azure.cognitiveservices.speech as speechsdk
from pydub import AudioSegment
import requests
import json

app = Flask(__name__)

# Azure Speech Service Credentials
SPEECH_KEY = "0457e552ce7a4ca290ca45c2d4910990"
SPEECH_REGION = "southeastasia"

# Google Speech API setup
GOOGLE_API_KEY = "AIzaSyCtqPXuY9-mRR3eTR-hC-3uf4KZKxknMEA"
GOOGLE_SPEECH_URL = f"https://speech.googleapis.com/v1p1beta1/speech:recognize?key={GOOGLE_API_KEY}"

def convert_webm_to_wav(webm_path):
    """Convert WebM audio file to WAV format."""
    try:
        wav_path = webm_path.replace(".webm", ".wav")
        audio = AudioSegment.from_file(webm_path, format="webm")
        audio.export(wav_path, format="wav")
        return wav_path
    except Exception as e:
        print(f"❌ Error converting WebM to WAV: {e}")
        return None  # Return None if conversion fails

def transcribe_audio_azure(file_path, language):
    """Transcribe audio using Azure Speech-to-Text with a specified language."""
    try:
        speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
        speech_config.speech_recognition_language = language  # Set selected language

        audio_config = speechsdk.audio.AudioConfig(filename=file_path)
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

        result = speech_recognizer.recognize_once()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return result.text
        elif result.reason == speechsdk.ResultReason.NoMatch:
            return "No speech detected. Try speaking clearly."
        elif result.reason == speechsdk.ResultReason.Canceled:
            return f"Recognition canceled: {result.cancellation_details.reason}"
    except Exception as e:
        print(f"❌ Azure Transcription error: {e}")
        return None  # Return None if API call fails

import requests
import base64
import wave

GOOGLE_SPEECH_URL = "https://speech.googleapis.com/v1/speech:recognize?key=YOUR_API_KEY"

def transcribe_audio_google(file_path, language):
    """Transcribe a WAV file using Google Speech-to-Text."""
    try:
        # Open WAV file to verify format and sample rate
        with wave.open(file_path, "rb") as wav_file:
            sample_width = wav_file.getsampwidth()
            sample_rate = wav_file.getframerate()
            channels = wav_file.getnchannels()

        # Validate format
        if sample_width != 2 or channels != 1:
            print(f"⚠️ Invalid WAV format: Expected 16-bit PCM (sample width=2, channels=1), got width={sample_width}, channels={channels}")
            return "Invalid WAV format (must be 16-bit PCM, mono)."

        if sample_rate != 16000:
            print(f"⚠️ Sample rate mismatch: Expected 16000 Hz, got {sample_rate} Hz")
            return "Invalid sample rate (must be 16kHz)."

        # Read and encode the WAV file
        with open(file_path, "rb") as audio_file:
            audio_content = audio_file.read()

        encoded_audio = base64.b64encode(audio_content).decode("utf-8")

        # Prepare the API request payload
        body = {
            "config": {
                "encoding": "LINEAR16",  # Ensure it's LINEAR16 for WAV files
                "sampleRateHertz": sample_rate,
                "languageCode": language
            },
            "audio": {
                "content": encoded_audio
            }
        }

        # Send request to Google Speech API
        response = requests.post(GOOGLE_SPEECH_URL, json=body)

        # Handle response
        if response.status_code == 200:
            result = response.json()
            if "results" in result and len(result["results"]) > 0:
                return result["results"][0]["alternatives"][0]["transcript"]
            else:
                print("❌ No speech detected in audio.")
                return "No speech detected."
        else:
            print(f"❌ Google Speech API error: {response.status_code} {response.text}")
            return None

    except wave.Error as wav_err:
        print(f"❌ WAV file error: {wav_err}")
        return "Invalid WAV file."

    except Exception as e:
        print(f"❌ Google Transcription error: {e}")
        return None

@app.route("/")
def index():
    """Render the homepage."""
    return render_template("index.html")

@app.route("/transcribe", methods=["POST"])
def transcribe():
    """Handle audio file upload and transcription."""
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files["audio"]
    language = request.form.get("language")  # Get language, default to English
    recognizer_model = request.form.get("recognizerModel", "azure")  # Get selected recognizer model

    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
        audio_file.save(temp_audio.name)
        webm_path = temp_audio.name

    wav_path = convert_webm_to_wav(webm_path)
    if not wav_path:
        return jsonify({"error": "Failed to convert audio"}), 500

    # Choose transcription model based on user selection
    if recognizer_model == "google":
        transcription = transcribe_audio_google(wav_path,language)
    else:
        transcription = transcribe_audio_azure(wav_path,language)

    if transcription is None:
        return jsonify({"error": "Transcription failed"}), 500

    # Cleanup temporary files
    os.remove(webm_path)
    os.remove(wav_path)

    return jsonify({"transcription": transcription})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
