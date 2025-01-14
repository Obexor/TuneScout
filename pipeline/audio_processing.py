import pyaudio
import wave

def record_audio(output_file, duration=5):
    """
    Record audio from the microphone and save it to a WAV file.

    :param output_file: The name of the output WAV file
    :param duration: Duration of the recording in seconds (default is 5 seconds)
    """
    # Audio configuration parameters
    FORMAT = pyaudio.paInt16  # Audio format (16-bit PCM)
    CHANNELS = 1  # Number of audio channels (1 for mono)
    RATE = 44100  # Sampling rate in Hz (CD quality)
    CHUNK = 1024  # Buffer size for audio data

    # Initialize PyAudio instance
    audio = pyaudio.PyAudio()
    
    # Open a stream for audio input
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    frames = []  # List to store audio data frames

    # Read audio data from the input stream
    for _ in range(0, int(RATE / CHUNK * duration)):
        data = stream.read(CHUNK)  # Read a chunk of audio data
        frames.append(data)  # Append the chunk to the frames list

    # Stop and close the audio stream
    stream.stop_stream()
    stream.close()
    
    # Terminate the PyAudio instance
    audio.terminate()

    # Save recorded audio to a WAV file
    with wave.open(output_file, 'wb') as wf:
        wf.setnchannels(CHANNELS)  # Set the number of audio channels
        wf.setsampwidth(audio.get_sample_size(FORMAT))  # Set the sample width
        wf.setframerate(RATE)  # Set the frame rate (sampling rate)
        wf.writeframes(b''.join(frames))  # Write audio frames to the file


