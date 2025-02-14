import os
import wave
import threading
import pyaudio
import numpy as np

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 10
SAVE_DIRECTORY = "test/"


def record_audio(filename=None):
    """
    Records 10 seconds of audio and optionally saves it to a file.

    :param filename: The path where the audio will be saved (optional).
    :returns: The audio stream as a NumPy array with parameters defined in this module.
    """
    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("* Recording started...")

    frames = []
    write_frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(np.frombuffer(data, dtype=np.int16))
        if filename:
            write_frames.append(data)

    print("* Recording finished.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    if filename:
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(write_frames))

    return np.hstack(frames)


class RecordThread(threading.Thread):
    """
    A thread that continuously records audio and saves files at regular intervals.
    """

    def __init__(self, base_filename, piece_len=10, spacing=5):
        super().__init__()
        self.stop_request = threading.Event()
        self.frames = []
        self.audio = pyaudio.PyAudio()
        self.chunks_per_write = int((RATE / CHUNK) * piece_len)
        self.chunks_to_delete = int((RATE / CHUNK) * spacing)
        self.stream = self.audio.open(format=FORMAT,
                                      channels=CHANNELS,
                                      rate=RATE,
                                      input=True,
                                      frames_per_buffer=CHUNK)
        self.base_filename = base_filename
        self.file_num = self.get_file_num()

    def get_file_num(self):
        """
        Determines the next available file number based on existing files.
        """
        file_num = 1
        if not os.path.exists(SAVE_DIRECTORY):
            os.makedirs(SAVE_DIRECTORY)

        for f in os.listdir(SAVE_DIRECTORY):
            if self.base_filename not in f:
                continue
            num = int(f.split(".")[0][len(self.base_filename):])
            if num >= file_num:
                file_num = num + 1
        return file_num

    def write_piece(self):
        """
        Saves the current recording to a file.
        """
        filename = os.path.join(SAVE_DIRECTORY, f"{self.base_filename}{self.file_num}.wav")
        frames_to_write = self.frames[:self.chunks_per_write]

        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(self.audio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames_to_write))

        self.frames = self.frames[self.chunks_to_delete:]
        self.file_num += 1

    def run(self):
        """
        Starts the recording in the background.
        """
        while not self.stop_request.isSet():
            data = self.stream.read(CHUNK)
            self.frames.append(data)
            if len(self.frames) > self.chunks_per_write:
                self.write_piece()

        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()

    def join(self, timeout=None):
        """
        Stops the thread.
        """
        self.stop_request.set()
        super().join(timeout)


def gen_many_tests(base_filename, spacing=5, piece_len=10):
    """
    Continuously records overlapping audio files and saves them.

    :param base_filename: Base filename without extension.
    :param spacing: Time in seconds between recordings.
    :param piece_len: Duration of each recording in seconds.
    """
    if not os.path.exists(SAVE_DIRECTORY):
        os.makedirs(SAVE_DIRECTORY)

    rec_thread = RecordThread(base_filename, spacing=spacing, piece_len=piece_len)
    rec_thread.start()
    input("Press <Enter> to stop recording...")
    rec_thread.join()
