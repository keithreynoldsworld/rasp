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
audio_data = []

# Callback function for recording audio
def audio_callback(indata, frames, time, status):
    if recording:
        audio_data.append(indata.copy())

# Functions to handle keyboard events
def on_press(key):
    global recording, audio_data
    if key == keyboard.Key.space and not recording:
        recording = True
        audio_data = []  # Reset audio data
        print("Recording started...")

def on_release(key):
    global recording
    if key == keyboard.Key.space and recording:
        recording = False
        print("Recording stopped.")

# Function to save audio to file
def save_audio():
    # Convert list of arrays to numpy array
    audio_data_np = np.concatenate(audio_data, axis=0)
    # Save the recorded audio to a file
    write(output_file, sample_rate, audio_data_np)
    print(f"Audio saved to {output_file}")

# Main loop
def main():
    # Start the keyboard listener in a non-blocking way
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    print("Press and hold the space bar to start recording. Release to stop.")

    # Start recording in a non-blocking way
    with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16', callback=audio_callback):
        while True:
            if not recording and audio_data:
                # When recording stops, save the audio
                print("Saving audio...")
                save_audio()
                audio_data = []  # Clear audio data after saving

            # Check for spacebar to start recording again
            print("Press spacebar to record again or press 'Esc' to exit.")
            with keyboard.Events() as events:
                for event in events:
                    if isinstance(event, keyboard.Events.Press) and event.key == keyboard.Key.space:
                        break
                    elif isinstance(event, keyboard.Events.Press) and event.key == keyboard.Key.esc:
                        print("Exiting...")
                        listener.stop()
                        exit()

if __name__ == "__main__":
    main()
