import azure.cognitiveservices.speech as speechsdk
import os
import time
import base64
import requests
import threading
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

socketio = SocketIO(app, async_mode='eventlet')

# Azure Speech API setup
subscription_key = "0457e552ce7a4ca290ca45c2d4910990"
region = "southeastasia"

# Google Speech API setup
API_KEY = "AIzaSyCtqPXuY9-mRR3eTR-hC-3uf4KZKxknMEA"
SPEECH_API_URL = f"https://speech.googleapis.com/v1p1beta1/speech:recognize?key={API_KEY}"

transcription_text = ""
language = "en-US"
transcription_active = False
speech_recognizer = None
UPLOAD_FOLDER = 'downloads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

log_file_path = f"transcription_log_{int(time.time())}.txt"

def transcribe_azure(language):
    global transcription_text, transcription_active, speech_recognizer

    print("Initializing Azure Speech SDK...")
    speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)
    speech_config.speech_recognition_language = language
    
    # Use None instead of default microphone (Azure App Service does not support microphones)
    audio_config = None  
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    
    def recognized_handler(evt):
        global transcription_text
        transcription_text = evt.result.text
        print(f"Recognized: {transcription_text}")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {transcription_text}\n"
        with open(os.path.join('downloads', log_file_path), "a", encoding="utf-8") as log_file:
            log_file.write(log_entry)
        
        socketio.emit('transcription', {'transcription': transcription_text})
    
    speech_recognizer.recognized.connect(recognized_handler)
    speech_recognizer.start_continuous_recognition()
    print("Azure speech recognition started...")

    while transcription_active:
        time.sleep(1)
    
    speech_recognizer.stop_continuous_recognition()
    print("Azure transcription stopped.")

def transcribe_google(language):
    global transcription_text, transcription_active

    def process_audio_chunk(audio_data):
        audio_content = base64.b64encode(audio_data).decode('utf-8')
        payload = {"audio": {"content": audio_content}, "config": {"encoding": "LINEAR16", "sampleRateHertz": 16000, "languageCode": language}}
        
        try:
            response = requests.post(SPEECH_API_URL, json=payload)
            if response.status_code == 200 and 'results' in response.json():
                for res in response.json()['results']:
                    transcription_text = res['alternatives'][0]['transcript']
                    print("Transcript:", transcription_text)
                    socketio.emit('transcription', {'transcription': transcription_text})
            else:
                print("No speech detected.")
        except Exception as e:
            print(f"Error during Google Speech API request: {e}")

    while transcription_active:
        # Placeholder for real audio input capture
        audio_data = b''  # Replace with real audio data
        process_audio_chunk(audio_data)
        time.sleep(1)

@app.route('/')
def home():
    return 'Server is running.'

@app.route('/start', methods=['POST'])
def start_transcription():
    global language, transcription_active
    
    if transcription_active:
        return jsonify({"message": "Transcription is already running."}), 400

    data = request.get_json()
    language = data.get('language', 'en-US')
    service = data.get('service', 'azure')
    
    transcription_active = True
    thread = threading.Thread(target=transcribe_azure if service == 'azure' else transcribe_google, args=(language,))
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
        return send_from_directory(app.config['UPLOAD_FOLDER'], log_file_path)
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
