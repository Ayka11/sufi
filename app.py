from flask import Flask, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
import threading
import azure.cognitiveservices.speech as speechsdk
import time
import os
from datetime import datetime

app = Flask(__name__)

# Flask-SocketIO initialization
socketio = SocketIO(app, async_mode='eventlet')

# Replace with your Azure Speech API subscription key and region
subscription_key = "0457e552ce7a4ca290ca45c2d4910990"
region = "southeastasia"

# Store the current transcription text globally
transcription_text = ""
language = "en-US"  # Default language

# Global variable to control the transcription thread
transcription_active = False
speech_recognizer = None

# Log file path ff
log_file_path = "transcription_log_" + str(time.time())[:10] + ".txt"

def transcribe_audio(language):
    global transcription_text, transcription_active, speech_recognizer

    # Create a speech configuration object with your subscription key and region
    speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)

    # Set the language dynamically from the input
    speech_config.speech_recognition_language = language

    # Create an audio configuration object for real-time transcription using the microphone
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

    # Create a speech recognizer using the audio and speech configuration
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    # Event handler to capture and display transcription results in real-time
    def recognized_handler(evt):
        global transcription_text
        transcription_text = evt.result.text
        print(f"Recognized: {transcription_text}")  # Debug log

        # Add timestamp to the transcription
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {transcription_text}\n"

        # Save the transcription to the log file
        with open(log_file_path, "a", encoding="utf-8") as log_file:
            log_file.write(log_entry)

        # Emit the transcription to the front-end via WebSocket in real-time
        socketio.emit('transcription', {'transcription': transcription_text})
        print("Transcription sent to WebSocket")  # Debug log

    # Event handler for speech recognition started
    def start_handler(evt):
        print("Speech recognition started...")

    # Event handler for speech recognition completed
    def stop_handler(evt):
        print("Speech recognition stopped.")

    # Connect event handlers to recognized event
    speech_recognizer.recognized.connect(recognized_handler)
    speech_recognizer.session_started.connect(start_handler)
    speech_recognizer.session_stopped.connect(stop_handler)

    # Start continuous recognition
    print("Starting speech recognition...")
    speech_recognizer.start_continuous_recognition()

    # Keep the transcription active
    while transcription_active:
        time.sleep(1)

    # Stop continuous recognition when transcription_active is False
    speech_recognizer.stop_continuous_recognition()
    print("Transcription stopped.")

@app.route('/')
def home():
    #os.remove(log_file_path)
    return send_from_directory(os.getcwd(), 'index.html')

@app.route('/start', methods=['POST'])
def start_transcription():
    global language, transcription_active

    if transcription_active:
        return jsonify({"message": "Transcription is already running."}), 400

    data = request.get_json()
    language = data.get('language', 'en-US')  # Default to English if no language is provided

    # Start the transcription in a background thread with the selected language
    transcription_active = True
    thread = threading.Thread(target=transcribe_audio, args=(language,))
    thread.daemon = True
    thread.start()

    # Emit a notification event to the frontend
    socketio.emit('transcription_status', {'status': 'Transcription started'})

    return jsonify({"message": "Speech recognition started."}), 200

@app.route('/stop', methods=['POST'])
def stop_transcription():
    global transcription_active, speech_recognizer

    if not transcription_active:
        return jsonify({"message": "No active transcription to stop."}), 400

    # Stop the transcription
    transcription_active = False

    # Stop the Azure Speech Recognizer if it exists
    if speech_recognizer:
        speech_recognizer.stop_continuous_recognition()

    # Emit a notification event to the frontend
    socketio.emit('transcription_status', {'status': 'Transcription stopped'})

    return jsonify({"message": "Speech recognition stopped."}), 200

@app.route('/download_log', methods=['GET'])
def download_log():
    try:
        # Ensure the log file path is correct
        return send_from_directory(directory='/home/site/wwwroot/', path=log_file_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@socketio.on('connect')
def handle_connect():
    print("Client connected")
    # Send initial transcription state if available
    emit('transcription', {'transcription': transcription_text})

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

if __name__ == "__main__":
    # Ensure the log file exists
    if not os.path.exists('/home/site/wwwroot/'+log_file_path):
        with open(log_file_path, "w", encoding="utf-8") as log_file:
            log_file.write("Transcription Log:\n")

    socketio.run(app, debug=True, use_reloader=False, host='0.0.0.0', port=5000)
