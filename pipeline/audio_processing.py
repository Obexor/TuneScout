import sounddevice as sd
import wave


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
