import azure.cognitiveservices.speech as speechsdk
import os
import requests
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS

app = Flask(__name__)

# Enable CORS for all origins, including WebSocket support
CORS(app, resources={r"/*": {"origins": "*"}})

# Flask-SocketIO initialization with CORS settings
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")  # Allow all origins for WebSocket

# Azure Speech API setup
AZURE_SUBSCRIPTION_KEY = "0457e552ce7a4ca290ca45c2d4910990"
AZURE_REGION = "southeastasia"

# Google Speech API setup
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

    file_path = os.path.join(UPLOAD_FOLDER, "uploaded_audio.wav")
    audio_file.save(file_path)

    # Check if the audio file is valid by ensuring it's not zero bytes
    if os.path.getsize(file_path) == 0:
        return jsonify({"error": "Empty audio file"}), 400

    try:
        # Check the format of the audio file before processing
        if not is_valid_audio(file_path):
            return jsonify({"error": "Invalid audio file format"}), 400

        if service == "azure":
            transcription_text = transcribe_with_azure(file_path, language)
        elif service == "google":
            transcription_text = transcribe_with_google(file_path, language)
        else:
            return jsonify({"error": "Invalid service selected"}), 400

        # Log transcription
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {transcription_text}\n"

        with open(log_file_path, "a", encoding="utf-8") as log_file:
            log_file.write(log_entry)

        # Emit transcription to frontend via SocketIO
        socketio.emit('transcription', {'transcription': transcription_text})

        return jsonify({"transcription": transcription_text})

    except Exception as e:
        # Log any exception that occurs during the transcription process
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

    response = requests.post(GOOGLE_SPEECH_URL, json=request_data)
    result = response.json()

    if "results" in result:
        return result["results"][0]["alternatives"][0]["transcript"]
    return "No transcription result"

# 🔹 Audio File Validation (Ensures the file is valid)
def is_valid_audio(file_path):
    # Add your custom logic to validate the audio file format
    try:
        with open(file_path, "rb") as file:
            # Check the first few bytes for standard WAV header
            header = file.read(4)
            if header != b'RIFF':
                return False  # Invalid audio file, not a valid WAV file
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
    print("Client connected")
    emit('transcription', {'transcription': "Connected!"})

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

if __name__ == "__main__":
    # Run with eventlet to support WebSocket connections
    socketio.run(app, debug=True, use_reloader=False, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
