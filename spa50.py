#when I use the following code on the Raspberry Pi the spacebar doesn't stop recording when I release it it just stays there

import sounddevice as sd
import numpy as np
import subprocess
import serial
from pynput import keyboard
from scipy.io.wavfile import write
import os
import whisper_timestamped as whisper
import json
import ollama
# Parameters
sample_rate = 44100  # Sample rate in Hz
output_file = "one2/outputkeith2.wav"

# Initialize Arduino connection
arduino_port = '/dev/tty.usbmodem11301'  # Replace with your Arduino port
arduino = serial.Serial(arduino_port, 9600)

# Variables
recording = False
audio_data = []

# Callback function for recording audio
def audio_callback(indata, frames, time, status):
    if recording:
        audio_data.append(indata.copy())

# Functions to handle keyboard events
def on_press(key):
    global recording, audio_data
    if key == keyboard.Key.space:
        if not recording:
            recording = True
            audio_data = []  # Reset audio data
            print("Recording started...")

def on_release(key):
    global recording
    if key == keyboard.Key.space:
        if recording:
            recording = False
            print("Recording stopped.")
            return False  # Stop listener

# Function to speak text and control servo based on volume
def speak(text, voice='en-us+f3', speed=200, pitch=99):
    process = subprocess.Popen(['espeak', '-v', voice, '-s', str(speed), '-p', str(pitch), text], stdout=subprocess.PIPE)

    def speak_callback(indata, frames, time, status):
        volume_norm = np.linalg.norm(indata) * 10  # Adjust scaling factor as needed
        servo_position = int(np.clip(volume_norm, 0, 180)) * 5  # Map to 0-180 for servo range
        # print(f"Volume Norm: {volume_norm}, Servo Position: {servo_position}")

        arduino.write(f"{servo_position}\n".encode())  # Send position to Arduino with newline

    with sd.InputStream(callback=speak_callback):
        while process.poll() is None:
            sd.sleep(100)

    arduino.write(b'0\n')  # Reset servo to 0 after speaking
    print("Speaking finished.")

# Function to transcribe audio and generate a response
def transcribe_and_respond():
    # Convert list of arrays to a single numpy array
    audio_data_np = np.concatenate(audio_data, axis=0)

    # Save the recorded audio to a file
    write(output_file, sample_rate, audio_data_np)
    print(f"Audio saved to {output_file}")

    # Load the audio file and model
    audio = whisper.load_audio(output_file)
    model = whisper.load_model("tiny", device="cpu")

    # Transcribe the audio
    result = whisper.transcribe(model, audio, language="en")
    print(result)

    # Start a new conversation for each interaction
    conversation = [
        {'role': 'system', 'content': 'You are a bad friend.'},
        {'role': 'user', 'content': result['text']}
    ]

    # Save transcription to JSON
    json_file_path = os.path.join("one2", "outputkeith2.json")
    with open(json_file_path, 'w') as json_file:
        json.dump(result, json_file, indent=2, ensure_ascii=False)
    print(f"JSON file created: {json_file_path}")

    # Generate a response using TinyLLaMA model
    print(conversation)
    response = ollama.chat(
        model='blah',
        messages=conversation,
    )
    print(response['message']['content'])

    # Speak the response
    speak(response['message']['content'], voice='en-us', speed=80, pitch=40)

# Main loop
def main():
    while True:
        print("Press and hold the space bar to start recording. Release to stop.")

        # Start recording in a non-blocking way
        with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16', callback=audio_callback):
            with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
                listener.join()

        # Transcribe and respond
        transcribe_and_respond()

        # Wait for user to press spacebar again to start over
        print("Press spacebar to record again or press 'Esc' to exit.")
        with keyboard.Events() as events:
            for event in events:
                if isinstance(event, keyboard.Events.Press) and event.key == keyboard.Key.space:
                    break
                elif isinstance(event, keyboard.Events.Press) and event.key == keyboard.Key.esc:
                    print("Exiting...")
                    exit()

if __name__ == "__main__":
    main()
