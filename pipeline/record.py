import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np

# Global audio settings
FORMAT = 'int16'
CHANNELS = 1
RATE = 44100  # Sampling rate
RECORD_SECONDS = 10  # Recording duration in seconds


def record_audio(filename=None):
    """Records audio using the microphone for a preset duration and optionally saves it to a WAV file."""
    print("* Recording started...")

    # Capture audio as NumPy array
    frames = sd.rec(int(RATE * RECORD_SECONDS), samplerate=RATE, channels=CHANNELS, dtype=FORMAT)
    sd.wait()

    print("* Recording finished!")

    if filename:
        # Save audio data to a WAV file
        write(filename, RATE, frames)
        print(f"Audio saved as: {filename}")

    return frames.flatten()  # Return as 1D array for processing
