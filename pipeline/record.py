import os
import wave
import threading
import pyaudio
import numpy as np
from pipeline import settings


class AudioRecorder:
    """Class for recording audio and saving it as a WAV file."""

    def __init__(self, channels=settings.CHANNELS, rate=settings.SAMPLE_RATE, chunk_size=settings.CHUNK):
        self.channels = channels
        self.rate = rate
        self.chunk_size = chunk_size
        self.audio = pyaudio.PyAudio()

    def record(self, duration, filename=None):
        """
        Records audio for the specified duration and optionally saves it to a file.

        :param duration: Duration of the recording in seconds.
        :param filename: Name of the file to optionally save the WAV data.
        :return: Numpy array containing the recorded audio data.
        """
        # Open input stream
        stream = self.audio.open(format=pyaudio.paInt16,
                                 channels=self.channels,
                                 rate=self.rate,
                                 input=True,
                                 frames_per_buffer=self.chunk_size)

        print("* Recording started")

        frames = []
        write_frames = []

        for _ in range(0, int(self.rate / self.chunk_size * duration)):
            data = stream.read(self.chunk_size)
            frames.append(np.frombuffer(data, dtype=np.int16))
            if filename is not None:
                write_frames.append(data)

        print("* Recording stopped")

        # Close stream
        stream.stop_stream()
        stream.close()

        # Save data to a WAV file (if filename is provided)
        if filename:
            self._save_to_wav(filename, write_frames)

        # Return the complete audio data as a Numpy array
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
        """Closes the PyAudio instance."""
        self.audio.terminate()


class RecordThread(threading.Thread):
    """Thread for continuous recording in overlapping segments."""

    def __init__(self, base_filename, piece_len=10, spacing=5):
        """
        Initializes a recording thread.

        :param base_filename: Base name of the file storing the segments.
        :param piece_len: Length of each segment in seconds.
        :param spacing: Overlapping time in seconds between segments.
        """
        threading.Thread.__init__(self)
        self.stop_request = threading.Event()
        self.piece_len = piece_len
        self.spacing = spacing
        self.base_filename = base_filename
        self.audio_recorder = AudioRecorder()
        self.frames = []
        self.file_num = self._get_file_num()  # Start number for files

    def _get_file_num(self):
        """Determines the next sequential number based on existing files."""
        file_num = 1
        if not os.path.exists(settings.SAVE_DIRECTORY):
            os.makedirs(settings.SAVE_DIRECTORY)

        for f in os.listdir(settings.SAVE_DIRECTORY):
            if self.base_filename not in f:
                continue
            num = int(f.split(".")[0][len(self.base_filename):])
            if num >= file_num:
                file_num = num + 1
        return file_num

    def run(self):
        """Starts recording in a separate thread."""
        while not self.stop_request.isSet():
            print(f"Starting recording: Segment {self.file_num}")
            segment_filename = os.path.join(settings.SAVE_DIRECTORY, f"{self.base_filename}{self.file_num}.wav")
            data = self.audio_recorder.record(self.piece_len)
            self.frames.append(data)
            self.audio_recorder._save_to_wav(segment_filename, [data.tobytes()])  # Save frames
            self.file_num += 1

    def join(self, timeout=None):
        """Stops the recording thread."""
        self.stop_request.set()
        self.audio_recorder.terminate()
        super(RecordThread, self).join(timeout)


def gen_many_tests(base_filename, spacing=5, piece_len=10):
    """
    Continuously generates overlapping test segments and saves them.

    :param base_filename: Base name of the files (without extension).
    :param spacing: Overlapping time in seconds between recording start times.
    :param piece_len: Length of each recorded segment in seconds.
    """
    rec_thread = RecordThread(base_filename, piece_len=piece_len, spacing=spacing)
    rec_thread.start()
    input("Press <Enter> to stop recording.")
    rec_thread.join()
