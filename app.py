import azure.cognitiveservices.speech as speechsdk
import time
import os
from datetime import datetime
import base64
import requests
from flask import Flask, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS  # For handling CORS
import threading

app = Flask(__name__)

# Enable CORS for all origins (for React app to communicate with Flask)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins

# Flask-SocketIO initialization
socketio = SocketIO(app, async_mode='eventlet')

# Azure Speech API setup
subscription_key = "0457e552ce7a4ca290ca45c2d4910990"
region = "southeastasia"

# Google Speech API setup
API_KEY = "AIzaSyCtqPXuY9-mRR3eTR-hC-3uf4KZKxknMEA"
SPEECH_API_URL = "https://speech.googleapis.com/v1p1beta1/speech:recognize?key=" + API_KEY

transcription_text = ""
language = "en-US"  # Default language
transcription_active = False
speech_recognizer = None
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

# This function will be called to transcribe audio using Azure Speech SDK
def transcribe_azure(language):
    global transcription_text, transcription_active, speech_recognizer

    speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)
    speech_config.speech_recognition_language = language
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    def recognized_handler(evt):
        global transcription_text
        transcription_text = evt.result.text
        print(f"Recognized: {transcription_text}")  # Debug log

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {transcription_text}\n"

        with open(log_file_path, "a", encoding="utf-8") as log_file:
            log_file.write(log_entry)

        socketio.emit('transcription', {'transcription': transcription_text})

    speech_recognizer.recognized.connect(recognized_handler)
    speech_recognizer.start_continuous_recognition()

    while transcription_active:
        time.sleep(1)

    speech_recognizer.stop_continuous_recognition()
    print("Transcription stopped.")

@app.route('/')
def home():
    return 'working fine'
    
@app.route('/start', methods=['POST'])
def start_transcription():
    global language, transcription_active
    data = request.get_json()
    language = data.get('language', 'en-US')
    service = data.get('service', 'azure')  # Default to Azure if no service is specified

    if transcription_active:
        return jsonify({"message": "Transcription is already running."}), 400

    transcription_active = True
    if service == 'azure':
        thread = threading.Thread(target=transcribe_azure, args=(language,))
    else:
        return jsonify({"message": "Google Speech API not implemented."}), 400
    
    thread.daemon = True
    thread.start()

    socketio.emit('transcription_status', {'status': 'Transcription started'})
    return jsonify({"message": "Speech recognition started."}), 200

@app.route('/stop', methods=['POST'])
def stop_transcription():
    global transcription_active, speech_recognizer

    if not transcription_active:
        return jsonify({"message": "No active transcription to stop."}), 400

    transcription_active = False

    if speech_recognizer:
        speech_recognizer.stop_continuous_recognition()

    socketio.emit('transcription_status', {'status': 'Transcription stopped'})
    return jsonify({"message": "Speech recognition stopped."}), 200

@app.route('/transcription', methods=['GET'])
def get_transcription():
    return jsonify({'transcription': transcription_text})

@app.route('/downloads', methods=['GET'])
def downloads():
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], "transcription_log.txt")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@socketio.on('connect')
def handle_connect():
    print("Client connected")
    emit('transcription', {'transcription': transcription_text})

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

if __name__ == "__main__":
    socketio.run(app, debug=True, use_reloader=False, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
