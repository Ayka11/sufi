import os
import eventlet
eventlet.monkey_patch()  # Add this at the very beginning

import requests
import eventlet.green.requests as grequests
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import tempfile
import shutil
from pydub import AudioSegment
import azure.cognitiveservices.speech as speechsdk

app = Flask(__name__)

# Enable CORS for all origins, including WebSocket support
CORS(app, resources={r"/*": {"origins": "*"}})

# Flask-SocketIO initialization with eventlet
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*", ping_timeout=60, ping_interval=30)

# Azure Speech API setup
AZURE_SUBSCRIPTION_KEY = "0457e552ce7a4ca290ca45c2d4910990"
AZURE_REGION = "southeastasia"

# Google Speech API setup (if needed)
GOOGLE_API_KEY = "AIzaSyCtqPXuY9-mRR3eTR-hC-3uf4KZKxknMEA"
GOOGLE_SPEECH_URL = f"https://speech.googleapis.com/v1p1beta1/speech:recognize?key={GOOGLE_API_KEY}"

# File storage
UPLOAD_FOLDER = 'downloads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

log_file_path = os.path.join(UPLOAD_FOLDER, "transcription_log.txt")

@app.before_request
def create_log_file():
    if not os.path.exists(log_file_path):
        with open(log_file_path, "w", encoding="utf-8") as log_file:
            log_file.write("Transcription Log:\n")

@app.route('/')
def home():
    return 'Backend is running!'

# 🔹 Upload & Transcribe Audio Route
@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file uploaded"}), 400

    audio_file = request.files['audio']
    service = request.form.get("service", "azure")  # Default to Azure
    language = request.form.get("language", "en-US")

    # Check if the audio file is not empty
    if audio_file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    file_path = os.path.join(UPLOAD_FOLDER, "uploaded_audio")
    audio_file.save(file_path)

    # Check if the audio file is valid by ensuring it's not zero bytes
    if os.path.getsize(file_path) == 0:
        return jsonify({"error": "Empty audio file"}), 400

    # Ensure audio is in the correct format (WAV, 16-bit PCM, 16kHz)
    try:
        # Convert to WAV using pydub
        wav_file_path = os.path.join(UPLOAD_FOLDER, "converted_audio.wav")
        audio = AudioSegment.from_file(file_path)
        audio = audio.set_channels(1)  # Mono channel
        audio = audio.set_sample_width(2)  # 16-bit sample width
        audio = audio.set_frame_rate(16000)  # 16kHz sampling rate
        audio.export(wav_file_path, format="wav")
    except Exception as e:
        return jsonify({"error": f"Error during audio conversion: {str(e)}"}), 500

    try:
        # Process the audio
        if service == "azure":
            transcription_text = transcribe_with_azure(wav_file_path, language)
        elif service == "google":
            transcription_text = transcribe_with_google(wav_file_path, language)
        else:
            return jsonify({"error": "Invalid service selected"}), 400

        # Log transcription
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {transcription_text}\n"

        with open(log_file_path, "a", encoding="utf-8") as log_file:
            log_file.write(log_entry)

        # Emit transcription to frontend via SocketIO
        try:
            socketio.emit('transcription', {'transcription': transcription_text})
        except Exception as e:
            app.logger.error(f"Socket emission error: {str(e)}")
        
        # Clean up temporary files
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(wav_file_path):
            os.remove(wav_file_path)

        return jsonify({"transcription": transcription_text})

    except Exception as e:
        # Log any exception that occurs during the transcription process
        app.logger.error(f"Error during transcription: {str(e)}")
        return jsonify({"error": str(e)}), 500


# 🔹 Azure Speech-to-Text
def transcribe_with_azure(file_path, language):
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SUBSCRIPTION_KEY, region=AZURE_REGION)
    speech_config.speech_recognition_language = language
    audio_input = speechsdk.audio.AudioConfig(filename=file_path)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)

    try:
        result = speech_recognizer.recognize_once()
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return result.text
        elif result.reason == speechsdk.ResultReason.NoMatch:
            raise Exception(f"No speech could be recognized in the audio.")
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            raise Exception(f"Azure transcription failed: {cancellation_details.reason}, {cancellation_details.error_details}")
        else:
            raise Exception(f"Azure transcription failed: {result.reason}")
    except Exception as e:
        raise Exception(f"Error during Azure transcription: {str(e)}")


# 🔹 Google Speech-to-Text
def transcribe_with_google(file_path, language):
    with open(file_path, "rb") as audio_file:
        audio_content = audio_file.read()

    request_data = {
        "config": {
            "encoding": "LINEAR16",
            "languageCode": language
        },
        "audio": {
            "content": audio_content.decode("ISO-8859-1")  # Encode file to base64
        }
    }

    response = grequests.post(GOOGLE_SPEECH_URL, json=request_data)
    result = response.json()

    if "results" in result:
        return result["results"][0]["alternatives"][0]["transcript"]
    return "No transcription result"

# 🔹 Audio File Validation (Ensures the file is valid)
def is_valid_audio(file_path):
    try:
        with open(file_path, "rb") as file:
            header = file.read(4)
            if header != b'RIFF':
                return False
            return True
    except Exception as e:
        return False


# 🔹 Download Transcription Log
@app.route('/downloads', methods=['GET'])
def downloads():
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], "transcription_log.txt")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# WebSocket Events
@socketio.on('connect')
def handle_connect():
    app.logger.info("Client connected")
    emit('transcription', {'transcription': "Connected!"})

@socketio.on('disconnect')
def handle_disconnect():
    app.logger.info("Client disconnected")

if __name__ == "__main__":
    # Run with eventlet workers to handle async WebSocket connections properly
    socketio.run(app, debug=True, use_reloader=False, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
