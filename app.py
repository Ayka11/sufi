import azure.cognitiveservices.speech as speechsdk
import os
import requests
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS

app = Flask(__name__)

# Enable CORS for all origins
CORS(app, resources={r"/*": {"origins": "*"}})

# Flask-SocketIO initialization
socketio = SocketIO(app, async_mode='eventlet')

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

    file_path = os.path.join(UPLOAD_FOLDER, "uploaded_audio.wav")
    audio_file.save(file_path)

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

    # Emit transcription to frontend
    socketio.emit('transcription', {'transcription': transcription_text})

    return jsonify({"transcription": transcription_text})

# 🔹 Azure Speech-to-Text
def transcribe_with_azure(file_path, language):
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SUBSCRIPTION_KEY, region=AZURE_REGION)
    speech_config.speech_recognition_language = language
    audio_input = speechsdk.audio.AudioConfig(filename=file_path)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)

    result = speech_recognizer.recognize_once()
    return result.text if result.text else "No transcription result"

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

# 🔹 Download Transcription Log
@app.route('/downloads', methods=['GET'])
def downloads():
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], "transcription_log.txt")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@socketio.on('connect')
def handle_connect():
    print("Client connected")
    emit('transcription', {'transcription': "Connected!"})

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

if __name__ == "__main__":
    socketio.run(app, debug=True, use_reloader=False, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
