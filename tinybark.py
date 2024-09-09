# Load model directly
from transformers import AutoProcessor, AutoModelForTextToWaveform

processor = AutoProcessor.from_pretrained("suno/bark")
model = AutoModelForTextToWaveform.from_pretrained("suno/bark")

from transformers import pipeline
import scipy

synthesiser = pipeline("text-to-speech", "suno/bark")

speech = synthesiser("Hello, my dog is cooler than you!", forward_params={"do_sample": True})
https://drive.google.com/file/d/1awinZUSQRCvixiRTgd9PqCw2nSi8eqL7/view?usp=sharing
scipy.io.wavfile.write("bark_out.wav", rate=speech["sampling_rate"], data=speech["audio"])
