import os
import pyaudio
import base64
import requests
import json
import wave

# Your Google Cloud API Key
API_KEY = "AIzaSyCtqPXuY9-mRR3eTR-hC-3uf4KZKxknMEA"

# Audio stream configuration
RATE = 16000  # Sample rate in Hz
CHUNK = 1024  # Size of each audio chunk
CHANNELS = 1  # Mono audio
FORMAT = pyaudio.paInt16  # Audio format for PyAudio

# URL for Google Cloud Speech API
SPEECH_API_URL = "https://speech.googleapis.com/v1p1beta1/speech:recognize?key=" + API_KEY

def transcribe_audio_live():
    # Initialize PyAudio to capture audio
    p = pyaudio.PyAudio()

    # Open the audio stream
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("Recording... Speak into the microphone")

    audio_buffer = []  # Buffer to accumulate audio data

    while True:
        # Record a chunk of audio from the microphone
        audio_data = stream.read(CHUNK)
        if not audio_data:
            continue

        # Add the chunk to the buffer
        audio_buffer.append(audio_data)

        # If the buffer has enough audio data, process it
        if len(audio_buffer) * CHUNK >= RATE * 2:  # 2 seconds of audio
            # Combine the audio chunks into a single audio blob
            audio_blob = b''.join(audio_buffer)
            audio_content = base64.b64encode(audio_blob).decode('utf-8')

            # Set up the request payload
            audio = {
                "content": audio_content
            }
            config = {
                "encoding": "LINEAR16",
                "sampleRateHertz": RATE,
                "languageCode": "en-US"
            }

            payload = {
                "audio": audio,
                "config": config
            }

            # Send the request to the Google Cloud Speech API
            try:
                response = requests.post(SPEECH_API_URL, json=payload)

                # Check the response from the API
                if response.status_code == 200:
                    result = response.json()
                    if 'results' in result:
                        for res in result['results']:
                            print("Transcript:", res['alternatives'][0]['transcript'])
                    else:
                        print("No speech detected.")
                else:
                    print(f"Error {response.status_code}: {response.text}")
            except Exception as e:
                print(f"Error during request: {e}")

            # Reset the audio buffer after processing
            audio_buffer = []

if __name__ == "__main__":
    transcribe_audio_live()
