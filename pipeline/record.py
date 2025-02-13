# record.py

import os
import wave
import threading
import pyaudio
import numpy as np
from pipeline import settings


class AudioRecorder:
    """Class for recording audio and saving it as a WAV file."""

    def __init__(self, channels=1, rate=settings.SAMPLE_RATE, chunk_size=settings.CHUNK):
        self.channels = channels
        self.rate = rate
        self.chunk_size = chunk_size
        self.audio = pyaudio.PyAudio()

    def record(self, duration, filename=None):
        """
        Records audio for the specified duration and optionally saves it as a file.

        :param duration: Recording duration in seconds.
        :param filename: Name of the file to save the WAV data (optional).
        :return: Numpy array with the recorded audio data.
        """
        stream = self.audio.open(format=pyaudio.paInt16,
                                 channels=self.channels,
                                 rate=self.rate,
                                 input=True,
                                 frames_per_buffer=self.chunk_size)

        print("* Recording started")

        frames = []
        raw_frames = []

        for _ in range(0, int(self.rate / self.chunk_size * duration)):
            data = stream.read(self.chunk_size, exception_on_overflow=False)
            frames.append(np.frombuffer(data, dtype=np.int16))
            raw_frames.append(data)

        print("* Recording finished")

        stream.stop_stream()
        stream.close()

        if filename:
            self._save_to_wav(filename, raw_frames)

        return np.hstack(frames)

    def _save_to_wav(self, filename, frames):
        """
        Saves the recorded audio frames as a WAV file.

        :param filename: Name of the WAV file.
        :param frames: List of frames (byte data).
        """
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(frames))
        print(f"File saved: {filename}")

    def terminate(self):
        """Terminates the PyAudio instance."""
        self.audio.terminate()


class RecordThread(threading.Thread):
    """Thread for continuous recording in overlapping segments."""

    def __init__(self, base_filename, piece_len=10, spacing=5):
        """
        Initializes a recording thread.

        :param base_filename: Base name of the files for the segments.
        :param piece_len: Length of each segment in seconds.
        :param spacing: Overlap time between segments in seconds.
        """
        super().__init__()
        self.stop_request = threading.Event()
        self.piece_len = piece_len
        self.spacing = spacing
        self.base_filename = base_filename
        self.audio_recorder = AudioRecorder()
        self.frames = []
        self.file_num = self._get_file_num()

    def _get_file_num(self):
        """Determines the next available file number."""
        file_num = 1
        if not os.path.exists(settings.SAVE_DIRECTORY):
            os.makedirs(settings.SAVE_DIRECTORY)

        for f in os.listdir(settings.SAVE_DIRECTORY):
            if self.base_filename not in f:
                continue
            try:
                num = int(f.split(".")[0][len(self.base_filename):])
                if num >= file_num:
                    file_num = num + 1
            except ValueError:
                continue
        return file_num

    def run(self):
        """Starts the recording in a separate thread."""
        while not self.stop_request.is_set():
            segment_filename = os.path.join(settings.SAVE_DIRECTORY, f"{self.base_filename}{self.file_num}.wav")
            print(f"Recording started: Segment {self.file_num}")

            audio_data = self.audio_recorder.record(self.piece_len)
            self.frames.append(audio_data)
            self.audio_recorder._save_to_wav(segment_filename, [audio_data.tobytes()])

            self.file_num += 1

    def join(self, timeout=None):
        """Stops the recording thread."""
        self.stop_request.set()
        self.audio_recorder.terminate()
        super().join(timeout)


def gen_many_tests(base_filename, spacing=5, piece_len=10):
    """
    Continuously creates overlapping test segments and saves them.

    :param base_filename: Base name of the files (without extension).
    :param spacing: Overlap time in seconds between recording starts.
    :param piece_len: Length of each recorded segment in seconds.
    """
    rec_thread = RecordThread(base_filename, piece_len=piece_len, spacing=spacing)
    rec_thread.start()
    input("Press <Enter> to stop recording.")
    rec_thread.join()


def record_audio_and_save(temp_file_name, duration=5):
    """
    Records audio for a specific duration and saves it as a WAV file.

    :param temp_file_name: Name of the file (without extension).
    :param duration: Recording duration in seconds.
    :return: Path to the saved WAV file.
    """
    try:
        recorder = AudioRecorder()
        temp_file_path = f"{temp_file_name}.wav"
        recorder.record(duration, filename=temp_file_path)
        recorder.terminate()
        print(f"Audio recorded and saved as: {temp_file_path}")
        return temp_file_path
    except Exception as e:
        raise RuntimeError(f"Error during audio recording: {str(e)}")
