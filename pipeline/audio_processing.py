import sounddevice as sd
import wave
import numpy as np
from scipy.signal import spectrogram



def record_audio(output_file, duration=10):
    """
    Record audio from the microphone and save it to a WAV file.

    :param output_file: The name of the output WAV file
    :param duration: Duration of the recording in seconds (default is 10 seconds)
    """
    # Audio configuration parameters
    SAMPLE_RATE = 44100  # Sampling rate in Hz (CD quality)
    CHANNELS = 1  # Number of audio channels (1 for mono)

    # Record audio data using sounddevice
    audio_data = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='int16')
    sd.wait()  # Wait until the recording is finished

    # Save recorded audio data to a WAV file
    with wave.open(output_file, 'wb') as wf:
        wf.setnchannels(CHANNELS)  # Set the number of audio channels
        wf.setsampwidth(2)  # Set the sample width (2 bytes for int16)
        wf.setframerate(SAMPLE_RATE)  # Set the frame rate (sampling rate)
        wf.writeframes(audio_data.tobytes())  # Write audio frames to the file

def file_to_spectrogram(audio_file):
    """
       Calculate the spectrogram of a given WAV file.

       :param audio_file: Path to the audio file or a file-like object
       :return: Frequencies (f), time points (t), and the spectrogram (Sxx)
       """
    try:
        if hasattr(audio_file, "seek"):  # If the file is a file-like object, reset file pointer
            audio_file.seek(0)

        with wave.open(audio_file, 'rb') as wav_file:
            sample_rate = wav_file.getframerate()
            frames = wav_file.readframes(wav_file.getnframes())
            audio_data = np.frombuffer(frames, dtype=np.int16)

        # Compute the spectrogram
        f, t, Sxx = spectrogram(audio_data, sample_rate, nperseg=2048, noverlap=1024)
        return f, t, Sxx
    except Exception as e:
        raise ValueError(f"Error processing audio file for spectrogram: {e}")


