from flask import Flask, request, jsonify
import os
import tempfile
import azure.cognitiveservices.speech as speechsdk

app = Flask(__name__)

SPEECH_KEY = "0457e552ce7a4ca290ca45c2d4910990"
SPEECH_REGION = "southeastasia"

def transcribe_audio(file_path):
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    audio_config = speechsdk.audio.AudioConfig(filename=file_path)

    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    result = speech_recognizer.recognize_once()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text
    elif result.reason == speechsdk.ResultReason.NoMatch:
        return "No speech recognized"
    elif result.reason == speechsdk.ResultReason.Canceled:
        return f"Recognition canceled: {result.cancellation_details.reason}"

@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files["audio"]
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
        audio_file.save(temp_audio.name)
        temp_audio_path = temp_audio.name

    transcription = transcribe_audio(temp_audio_path)
    
    os.remove(temp_audio_path)  # Cleanup temp file

    return jsonify({"transcription": transcription})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
