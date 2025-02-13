# audio_processing.py

import os
import wave
import numpy as np
import subprocess
from scipy.signal import spectrogram
from pipeline import settings


def file_to_spectrogram(filename):
    """
    Creates a spectrogram for a given WAV file.
    Ensures that the file is mono and has the correct sample rate.

    :param filename: Path to the audio file
    :return: Frequencies, timestamps, and spectrogram data
    """
    with wave.open(filename, 'rb') as wf:
        # Check the number of channels and sample rate
        if wf.getnchannels() != 1:
            raise ValueError("The audio file must be mono.")

        if wf.getframerate() != settings.SAMPLE_RATE:
            raise ValueError(f"The sample rate must be {settings.SAMPLE_RATE} Hz.")

        # Read audio data
        frames = wf.readframes(wf.getnframes())
        audio = np.frombuffer(frames, dtype=np.int16)

        # Compute spectrogram
        nperseg = int(settings.SAMPLE_RATE * settings.FFT_WINDOW_SIZE)
        f, t, Sxx = spectrogram(audio, fs=settings.SAMPLE_RATE, nperseg=nperseg)

        return f, t, Sxx


def convert_to_wav(input_path, output_path):
    """
    Converts an audio file to WAV format with the correct sample rate and mono audio.

    :param input_path: Path to the input file (e.g., MP3)
    :param output_path: Path where the WAV file will be saved
    """
    command = [
        "ffmpeg", "-y", "-i", input_path,
        "-ac", "1",  # Mono
        "-ar", str(settings.SAMPLE_RATE),  # Adjust sample rate
        output_path
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg error: {result.stderr.decode()}")


def ensure_mono(wav_path):
    """
    Ensures that a WAV file is mono. If it is stereo, it will be converted.

    :param wav_path: Path to the WAV file
    """
    with wave.open(wav_path, "rb") as wf:
        channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        framerate = wf.getframerate()
        frames = wf.readframes(wf.getnframes())

    if channels == 1:
        return  # File is already mono

    # Stereo -> Mono conversion by averaging channels
    audio = np.frombuffer(frames, dtype=np.int16).reshape(-1, channels)
    mono_audio = audio.mean(axis=1).astype(np.int16)

    # Save the new file
    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(sample_width)
        wf.setframerate(framerate)
        wf.writeframes(mono_audio.tobytes())
