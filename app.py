from flask import Flask, render_template, request, jsonify
import os
import tempfile
import azure.cognitiveservices.speech as speechsdk
import requests
import json
from pydub import AudioSegment

app = Flask(__name__)

# Azure Speech API Credentials
AZURE_SPEECH_KEY = "0457e552ce7a4ca290ca45c2d4910990"
AZURE_SPEECH_REGION = "southeastasia"

# Google Cloud Speech-to-Text API Key
GOOGLE_API_KEY = "AIzaSyCtqPXuY9-mRR3eTR-hC-3uf4KZKxknMEA"
GOOGLE_SPEECH_API_URL = f"https://speech.googleapis.com/v1p1beta1/speech:recognize?key={GOOGLE_API_KEY}"

def convert_webm_to_wav(webm_path):
    """Convert .webm to .wav"""
    wav_path = webm_path.replace(".webm", ".wav")
    audio = AudioSegment.from_file(webm_path, format="webm")
    audio.export(wav_path, format="wav")
    return wav_path

def transcribe_with_azure(file_path, language):
    """Transcribe audio using Azure Speech-to-Text"""
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
    speech_config.speech_recognition_language = language
    audio_config = speechsdk.audio.AudioConfig(filename=file_path)

    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    result = speech_recognizer.recognize_once()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text
    elif result.reason == speechsdk.ResultReason.NoMatch:
        return "No speech recognized"
    elif result.reason == speechsdk.ResultReason.Canceled:
        return f"Recognition canceled: {result.cancellation_details.reason}"

def transcribe_with_google(file_path, language):
    """Transcribe audio using Google Speech-to-Text"""
    with open(file_path, "rb") as audio_file:
        audio_content = audio_file.read()

    request_data = {
        "config": {
            "encoding": "LINEAR16",
            "sampleRateHertz": 16000,
            "languageCode": language
        },
        "audio": {
            "content": audio_content.decode("ISO-8859-1")  # Convert binary to text
        }
    }

    response = requests.post(GOOGLE_SPEECH_API_URL, json=request_data)
    result = response.json()

    if "results" in result:
        return " ".join([alt["transcript"] for res in result["results"] for alt in res["alternatives"]])
    return "No speech recognized"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/transcribe", methods=["POST"])
def transcribe():
    """Handle audio transcription with selected service"""
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    language = request.form.get("language", "en-US")
    recognizer = request.form.get("recognizer", "azure")  # Default to Azure
    audio_file = request.files["audio"]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
        audio_file.save(temp_audio.name)
        webm_path = temp_audio.name

    try:
        wav_path = convert_webm_to_wav(webm_path)

        if recognizer == "azure":
            transcription = transcribe_with_azure(wav_path, language)
        elif recognizer == "google":
            transcription = transcribe_with_google(wav_path, language)
        else:
            return jsonify({"error": "Invalid recognizer selected"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        os.remove(webm_path)  # Cleanup
        if os.path.exists(wav_path):
            os.remove(wav_path)

    return jsonify({"transcription": transcription})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
