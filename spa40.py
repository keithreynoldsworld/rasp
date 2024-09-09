import sounddevice as sd
import numpy as np
from pynput import keyboard
from scipy.io.wavfile import write
import os

# Parameters
sample_rate = 44100  # Sample rate in Hz
output_file = "one2/outputkeith2.wav"

# Variables
recording = False
audio_data = []  # Initialize audio_data as an empty list

# Callback function for recording audio
def audio_callback(indata, frames, time, status):
    global audio_data  # Ensure we refer to the global audio_data
    if recording:
        audio_data.append(indata.copy())

# Functions to handle keyboard events
def on_press(key):
    global recording, audio_data
    try:
        if key == keyboard.Key.space and not recording:
            recording = True
            audio_data = []  # Reset audio data when starting a new recording
            print("Recording started...")
        elif key.char == 'o' and recording:
            recording = False
            print("Recording stopped.")
    except AttributeError:
        pass

# Function to save audio to file
def save_audio():
    if audio_data:  # Ensure audio_data is not empty before saving
        # Convert list of arrays to numpy array
        audio_data_np = np.concatenate(audio_data, axis=0)
        # Save the recorded audio to a file
        write(output_file, sample_rate, audio_data_np)
        print(f"Audio saved to {output_file}")

# Main loop
def main():
    # Start the keyboard listener in a non-blocking way
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    print("Press the space bar to start recording. Press 'O' to stop and save.")

    # Start recording in a non-blocking way
    with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16', callback=audio_callback):
        while True:
            if not recording and audio_data:  # Ensure audio_data is not empty
                # When recording stops, save the audio
                print("Saving audio...")
                save_audio()
                audio_data = []  # Clear audio data after saving

if __name__ == "__main__":
    main()
