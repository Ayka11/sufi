@app.route("/transcribe", methods=["POST"])
def transcribe():
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
        os.remove(webm_path)  # Cleanup temp file
        if os.path.exists(wav_path):
            os.remove(wav_path)

    return jsonify({"transcription": transcription})
