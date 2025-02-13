
# audio_processing.py

import wave
import numpy as np
from scipy.signal import spectrogram
import subprocess
from pipeline import settings


def file_to_spectrogram(filename):
    """
    Creates a spectrogram for a given audio file.
    Converts the audio to mono and ensures it matches the required sample rate before processing.

    :param filename: Path to the audio file
    :return: Frequencies, times, and spectrogram data
    """
    with wave.open(filename, 'rb') as wf:
        # Ensure the file is mono
        if wf.getnchannels() > 1:
            raise ValueError("Audio must be mono.")

        # Check and match sample rate
        sample_rate = wf.getframerate()
        if sample_rate != settings.SAMPLE_RATE:
            raise ValueError(f"Sample rate must be {settings.SAMPLE_RATE} Hz.")

        # Read audio data
        audio = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)

        # Compute spectrogram
        nperseg = int(settings.SAMPLE_RATE * settings.FFT_WINDOW_SIZE)
        f, t, Sxx = spectrogram(audio, fs=sample_rate, nperseg=nperseg)
        return f, t, Sxx


def convert_to_wav(input_path, output_path):
    """
    Converts an audio file to WAV using ffmpeg.
    :param input_path: Path to the input file (e.g., MP3)
    :param output_path: Path to save the resulting WAV file
    """
    command = ["ffmpeg", "-y", "-i", input_path, output_path]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr.decode()}")


def ensure_mono(wav_path):
    """
    Ensures that the WAV file has a single (mono) audio channel.
    If the audio is stereo, it is converted to mono.
    :param wav_path: Path to the WAV file
    """
    with wave.open(wav_path, "rb") as wav_file:
        channels = wav_file.getnchannels()
        if channels == 1:
            return  # Already mono

        # Create mono audio
        frames = np.frombuffer(wav_file.readframes(wav_file.getnframes()), dtype=np.int16)
        samples = frames.reshape(-1, channels)
        mono_samples = samples.mean(axis=1).astype(np.int16)

        # Save the mono file
        with wave.open(wav_path, "wb") as mono_file:
            mono_file.setnchannels(1)
            mono_file.setsampwidth(wav_file.getsampwidth())
            mono_file.setframerate(wav_file.getframerate())
            mono_file.writeframes(mono_samples.tobytes())

