# audioconverter.py

import subprocess
from pipeline import settings


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



