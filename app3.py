import os
import pyaudio
from google.cloud import speech

# Set the path to your Google Cloud service account key
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "sc-1-433715-558af7a8b81b.json" ###

# Configure the microphone audio input stream
RATE = 16000  # Sample rate in Hz
CHUNK = 1024  # Size of each audio chunk
CHANNELS = 1  # Mono audio
FORMAT = pyaudio.paInt16  # Audio format for PyAudio

def transcribe_streaming():
    # Initialize the speech client
    client = speech.SpeechClient()

    # Set up audio stream configuration
    streaming_config = speech.StreamingRecognitionConfig(
        config=speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,  # Using the enum directly
            sample_rate_hertz=RATE,
            language_code="en-US",
        ),
        interim_results=True,  # To get live transcription as it's being spoken
    )

    # Open microphone input stream using PyAudio
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True,
                    frames_per_buffer=CHUNK)

    print("Recording... (Speak into the microphone)")

    # Generate audio chunks and send them to Google Cloud in real time
    requests = (speech.StreamingRecognizeRequest(audio_content=stream.read(CHUNK)) for _ in range(100000))  # Generate multiple requests

    # Send the audio data to Google Cloud Speech API
    responses = client.streaming_recognize(streaming_config, requests)

    # Print the responses
    for response in responses:
        for result in response.results:
            print("Transcript: {}".format(result.alternatives[0].transcript))

if __name__ == "__main__":
    transcribe_streaming()
