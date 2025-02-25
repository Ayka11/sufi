from flask import Flask, render_template, request, jsonify
import os
import tempfile
import azure.cognitiveservices.speech as speechsdk
from pydub import AudioSegment
import requests
import json

app = Flask(__name__)

# Azure Speech Config
SPEECH_KEY = "0457e552ce7a4ca290ca45c2d4910990"
SPEECH_REGION = "southeastasia"

# Google Speech API Key
GOOGLE_API_KEY = "AIzaSyCtqPXuY9-mRR3eTR-hC-3uf4KZKxknMEA"
GOOGLE_SPEECH_URL = f"https://speech.googleapis.com/v1/speech:recognize?key={GOOGLE_API_KEY}"

def convert_audio(input_path, output_format="wav"):
    """ Converts audio to the desired format """
    output_path = input_path.rsplit(".", 1)[0] + f".{output_format}"
    audio = AudioSegment.from_file(input_path)
    audio.export(output_path, format=output_format)
    return output_path

def transcribe_with_azure(file_path, language):
    """ Transcribe using Azure Speech-to-Text """
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
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
    """ Transcribe using Google Speech-to-Text """
    flac_path = convert_audio(file_path, "flac")  # Google requires FLAC or LINEAR16
    with open(flac_path, "rb") as audio_file:
        audio_content = audio_file.read()

    payload = {
        "config": {
            "encoding": "FLAC",
            "sampleRateHertz": 16000,
            "languageCode": language
        },
        "audio": {
            "content": audio_content.decode("ISO-8859-1")  # Convert binary to text
        }
    }

    response = requests.post(GOOGLE_SPEECH_URL, json=payload)
    
    os.remove(flac_path)  # Clean up converted file

    if response.status_code == 200:
        result = response.json()
        if "results" in result:
            return " ".join([alt["transcript"] for res in result["results"] for alt in res["alternatives"]])
        else:
            return "No speech recognized"
    else:
        return f"Google API error: {response.text}"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files["audio"]
    language = request.form.get("language", "en-US")
    recognizer = request.form.get("recognizer", "azure")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
        audio_file.save(temp_audio.name)
        webm_path = temp_audio.name

    try:
        wav_path = convert_audio(webm_path, "wav")
        if recognizer == "azure":
            transcription = transcribe_with_azure(wav_path, language)
        elif recognizer == "google":
            transcription = transcribe_with_google(wav_path, language)
        else:
            return jsonify({"error": "Invalid recognizer"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        os.remove(webm_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)

    return jsonify({"transcription": transcription})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
