import azure.cognitiveservices.speech as speechsdk
import time
import os
from datetime import datetime
import base64
import requests
from flask import Flask, jsonify, request, send_from_directory, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import threading

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Azure Speech API setup
AZURE_SUBSCRIPTION_KEY = "0457e552ce7a4ca290ca45c2d4910990"
AZURE_REGION = "southeastasia"

# Google Speech API setup
GOOGLE_API_KEY = "AIzaSyCtqPXuY9-mRR3eTR-hC-3uf4KZKxknMEA"
GOOGLE_SPEECH_URL = f"https://speech.googleapis.com/v1p1beta1/speech:recognize?key={GOOGLE_API_KEY}"

UPLOAD_FOLDER = 'downloads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

transcription_text = ""
transcription_active = False
speech_recognizer = None

def transcribe_azure(language):
    global transcription_text, transcription_active, speech_recognizer

    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SUBSCRIPTION_KEY, region=AZURE_REGION)
    speech_config.speech_recognition_language = language
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    def recognized_handler(evt):
        global transcription_text
        transcription_text = evt.result.text
        print(f"Azure Recognized: {transcription_text}")
        socketio.emit('transcription', {'transcription': transcription_text})

    speech_recognizer.recognized.connect(recognized_handler)
    speech_recognizer.start_continuous_recognition()

    while transcription_active:
        time.sleep(1)

    speech_recognizer.stop_continuous_recognition()
    print("Azure Transcription Stopped.")

def transcribe_google(audio_data, language):
    global transcription_text

    audio_content = base64.b64encode(audio_data).decode('utf-8')
    payload = {
        "config": {"encoding": "LINEAR16", "sampleRateHertz": 16000, "languageCode": language},
        "audio": {"content": audio_content}
    }

    try:
        response = requests.post(GOOGLE_SPEECH_URL, json=payload)
        if response.status_code == 200:
            result = response.json()
            if 'results' in result:
                transcription_text = result['results'][0]['alternatives'][0]['transcript']
                print(f"Google Recognized: {transcription_text}")
                socketio.emit('transcription', {'transcription': transcription_text})
        else:
            print(f"Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Error during Google Speech API request: {e}")

@socketio.on('audio_data')
def handle_audio_data(data):
    global transcription_active
    if transcription_active:
        audio_chunk = base64.b64decode(data['audio_data'])
        transcribe_google(audio_chunk, data['language'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_transcription():
    global transcription_active

    if transcription_active:
        return jsonify({"message": "Transcription already running."}), 400

    data = request.get_json()
    service = data.get('service', 'azure')
    language = data.get('language', 'en-US')

    transcription_active = True
    if service == 'azure':
        thread = threading.Thread(target=transcribe_azure, args=(language,))
        thread.start()
    return jsonify({"message": "Speech recognition started."}), 200

@app.route('/stop', methods=['POST'])
def stop_transcription():
    global transcription_active
    transcription_active = False
    return jsonify({"message": "Speech recognition stopped."}), 200

if __name__ == "__main__":
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
