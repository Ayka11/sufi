from flask import Flask, render_template, request, jsonify
import os
import tempfile
import azure.cognitiveservices.speech as speechsdk
from pydub import AudioSegment

app = Flask(__name__)

# Azure Speech Service Credentials
SPEECH_KEY = "0457e552ce7a4ca290ca45c2d4910990"
SPEECH_REGION = "southeastasia"

def convert_webm_to_wav(webm_path):
    """Convert WebM audio file to WAV format."""
    try:
        wav_path = webm_path.replace(".webm", ".wav")
        audio = AudioSegment.from_file(webm_path, format="webm")
        audio.export(wav_path, format="wav")
        return wav_path
    except Exception as e:
        print(f"❌ Error converting WebM to WAV: {e}")
        return None  # Return None if conversion fails

def transcribe_audio(file_path, language="en-US"):
    """Transcribe audio using Azure Speech-to-Text with a specified language."""
    try:
        speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
        speech_config.speech_recognition_language = language  # Set selected language

        audio_config = speechsdk.audio.AudioConfig(filename=file_path)
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

        result = speech_recognizer.recognize_once()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return result.text
        elif result.reason == speechsdk.ResultReason.NoMatch:
            return "No speech detected. Try speaking clearly."
        elif result.reason == speechsdk.ResultReason.Canceled:
            return f"Recognition canceled: {result.cancellation_details.reason}"
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        return None  # Return None if API call fails

@app.route("/")
def index():
    """Render the homepage."""
    return render_template("index.html")

@app.route("/transcribe", methods=["POST"])
def transcribe():
    """Handle audio file upload and transcription."""
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files["audio"]
    language = request.form.get("language", "en-US")  # Get language, default to English

    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
        audio_file.save(temp_audio.name)
        webm_path = temp_audio.name

    wav_path = convert_webm_to_wav(webm_path)
    if not wav_path:
        return jsonify({"error": "Failed to convert audio"}), 500

    transcription = transcribe_audio(wav_path, language)
    if transcription is None:
        return jsonify({"error": "Transcription failed"}), 500

    # Cleanup temporary files
    os.remove(webm_path)
    os.remove(wav_path)

    return jsonify({"transcription": transcription})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
