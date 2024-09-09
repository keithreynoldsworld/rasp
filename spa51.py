import sys
import termios
import tty
import sounddevice as sd
import numpy as np
import subprocess
import serial
from scipy.io.wavfile import write
import os
import whisper_timestamped as whisper
import json
import ollama

# Parameters
sample_rate = 44100  # Sample rate in Hz
output_file = "one2/outputkeith2.wav"

# Initialize Arduino connection
arduino_port = '/dev/ttyUSB0'  # Replace with your Arduino port (Raspberry Pi uses /dev/ttyUSB0)
arduino = serial.Serial(arduino_port, 9600)

# Variables
recording = False
audio_data = []

# Callback function for recording audio
def audio_callback(indata, frames, time, status):
    if recording:
        audio_data.append(indata.copy())

# Function to detect keypress (for spacebar)
def get_key_press():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

# Function to handle spacebar press/release
def handle_keypress():
    global recording, audio_data
    while True:
        key = get_key_press()
        if key == ' ':  # Spacebar pressed
            if not recording:
                recording = True
                audio_data = []  # Reset audio data
                print("Recording started...")
            else:  # Spacebar released
                recording = False
                print("Recording stopped.")
                break
        elif key == '\x1b':  # Escape to exit
            print("Exiting...")
            exit()

# Function to speak text and control servo based on volume
def speak(text, voice='en-us+f3', speed=200, pitch=99):
    process = subprocess.Popen(['espeak', '-v', voice, '-s', str(speed), '-p', str(pitch), text], stdout=subprocess.PIPE)

    def speak_callback(indata, frames, time, status):
        volume_norm = np.linalg.norm(indata) * 10  # Adjust scaling factor as needed
        servo_position = int(np.clip(volume_norm, 0, 180)) * 5  # Map to 0-180 for servo range
        arduino.write(f"{servo_position}\n".encode())  # Send position to Arduino with newline

    with sd.InputStream(callback=speak_callback):
        while process.poll() is None:
            sd.sleep(100)

    arduino.write(b'0\n')  # Reset servo to 0 after speaking
    print("Speaking finished.")

# Function to transcribe audio and generate a response
def transcribe_and_respond():
    audio_data_np = np.concatenate(audio_data, axis=0)
    write(output_file, sample_rate, audio_data_np)
    print(f"Audio saved to {output_file}")

    audio = whisper.load_audio(output_file)
    model = whisper.load_model("tiny", device="cpu")
    result = whisper.transcribe(model, audio, language="en")
    print(result)

    conversation = [
        {'role': 'system', 'content': 'You are a bad friend.'},
        {'role': 'user', 'content': result['text']}
    ]

    json_file_path = os.path.join("one2", "outputkeith2.json")
    with open(json_file_path, 'w') as json_file:
        json.dump(result, json_file, indent=2, ensure_ascii=False)
    print(f"JSON file created: {json_file_path}")

    response = ollama.chat(
        model='blah',
        messages=conversation,
    )
    print(response['message']['content'])
    speak(response['message']['content'], voice='en-us', speed=80, pitch=40)

# Main loop
def main():
    while True:
        print("Press and hold the space bar to start recording. Release to stop.")
        with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16', callback=audio_callback):
            handle_keypress()

        transcribe_and_respond()

        print("Press spacebar to record again or press 'Esc' to exit.")
        handle_keypress()

if __name__ == "__main__":
    main()
