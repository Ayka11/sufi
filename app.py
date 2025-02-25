from flask import Flask, render_template, request, jsonify
import os
import tempfile
import azure.cognitiveservices.speech as speechsdk
from pydub import AudioSegment

app = Flask(__name__)

# Azure Speech API Credentials
SPEECH_KEY = "0457e552ce7a4ca290ca45c2d4910990"
SPEECH_REGION = "southeastasia"

def convert_webm_to_wav(webm_path):
    """Convert a .webm audio file to .wav format."""
    wav_path = webm_path.replace(".webm", ".wav")
    audio = AudioSegment.from_file(webm_path, format="webm")
    audio.export(wav_path, format="wav")
    return wav_path

def transcribe_audio(file_path, language):
    """Transcribe an audio file using Azure Speech-to-Text."""
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    speech_config.speech_recognition_language = language  # Set the recognition language
    audio_config = speechsdk.audio.AudioConfig(filename=file_path)

    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    result = speech_recognizer.recognize_once()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text
    elif result.reason == speechsdk.ResultReason.NoMatch:
        return "No speech recognized"
    elif result.reason == speechsdk.ResultReason.Canceled:
        return f"Recognition canceled: {result.cancellation_details.reason}"

@app.route("/")
def index():
    """Render the main HTML page."""
    return render_template("index.html")

@app.route("/transcribe", methods=["POST"])
def transcribe():
    """Handle audio file upload and transcription."""
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    
    language = request.form.get("language", "en-US")  # Default to English if no language is selected
    audio_file = request.files["audio"]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
        audio_file.save(temp_audio.name)
        webm_path = temp_audio.name

    try:
        wav_path = convert_webm_to_wav(webm_path)
        transcription = transcribe_audio(wav_path, language)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        os.remove(webm_path)  # Cleanup temp files
        if os.path.exists(wav_path):
            os.remove(wav_path)

    return jsonify({"transcription": transcription})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
