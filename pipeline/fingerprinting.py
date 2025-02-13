import uuid
import numpy as np
from scipy.signal import spectrogram
from scipy.ndimage import maximum_filter
from scipy.io import wavfile  # For loading WAV files
from pipeline import settings


def my_spectrogram(audio):
    """
    Helper function: Computes a spectrogram based on the settings.

    :param audio: The audio data as a numpy array.
    :returns: Frequencies (f), timestamps (t), spectrogram data (Sxx)
    """
    nperseg = int(settings.SAMPLE_RATE * settings.FFT_WINDOW_SIZE)
    return spectrogram(audio, settings.SAMPLE_RATE, nperseg=nperseg)


def preprocess_audio_file(filename):
    """
    Processes an audio file:
    - Loads the WAV file.
    - Converts it to mono if necessary.
    - Checks the sampling rate and adjusts it if needed.

    :param filename: Path to the audio file.
    :returns: The audio data as a numpy array.
    """
    sample_rate, audio_data = wavfile.read(filename)

    # If stereo (two channels), convert to mono
    if len(audio_data.shape) == 2:
        audio_data = audio_data.mean(axis=1).astype(np.int16)

    # Check the sampling rate
    if sample_rate != settings.SAMPLE_RATE:
        raise ValueError(
            f"The file's sampling rate is {sample_rate}. Expected: {settings.SAMPLE_RATE}"
        )

    # Return the processed audio data
    return audio_data


def file_to_spectrogram(filename):
    """
    Computes the spectrogram from a file.

    :param filename: Path to the audio file (WAV).
    :returns: Frequencies (f), timestamps (t), spectrogram data (Sxx)
    """
    audio_data = preprocess_audio_file(filename)
    return my_spectrogram(audio_data)


def find_peaks(Sxx):
    """
    Finds peak values in the spectrogram.

    Uses settings in `settings` to determine the size of the region and efficiency.

    :param Sxx: The spectrogram (power values for each frequency/time pair).
    :returns: A list of peak points.
    """
    data_max = maximum_filter(Sxx, size=settings.PEAK_BOX_SIZE, mode='constant', cval=0.0)
    peak_goodmask = (Sxx == data_max)  # Identify peak values
    y_peaks, x_peaks = peak_goodmask.nonzero()

    # Peak values
    peak_values = Sxx[y_peaks, x_peaks]
    sorted_indices = peak_values.argsort()[::-1]
    peaks = [(y_peaks[idx], x_peaks[idx]) for idx in sorted_indices]

    # Filter based on efficiency and compute the maximum number
    area = Sxx.shape[0] * Sxx.shape[1]
    peak_limit = int((area / (settings.PEAK_BOX_SIZE ** 2)) * settings.POINT_EFFICIENCY)

    return peaks[:peak_limit]


def idxs_to_tf_pairs(idxs, t, f):
    """
    Helper function to convert time and frequency indices into values.

    :param idxs: List of peak point indices.
    :param t: Timestamps.
    :param f: Frequencies.
    :returns: An array of (frequency, time) pairs.
    """
    return np.array([(f[i[0]], t[i[1]]) for i in idxs])


def hash_point_pair(p1, p2):
    """
    Generates a hash for a time-frequency pair.

    :param p1: First time-frequency pair.
    :param p2: Second time-frequency pair.
    :returns: The computed hash.
    """
    return hash((p1[0], p2[0], p2[1] - p1[1]))


def target_zone(anchor, points, width, height, offset):
    """
    Generates a target zone for a time-frequency anchor pair.

    :param anchor: Anchor point (starting point of the target zone).
    :param points: List of points (time/frequency).
    :param width: Width of the target zone.
    :param height: Height of the target zone.
    :param offset: Start offset after the anchor point.
    :returns: Points within the target zone.
    """
    x_min = anchor[1] + offset
    x_max = x_min + width
    y_min = anchor[0] - (height * 0.5)
    y_max = y_min + height

    for point in points:
        if y_min <= point[0] <= y_max and x_min <= point[1] <= x_max:
            yield point


def hash_points(points, filename):
    """
    Creates all hashes for a list of peak points.

    :param points: The peak points (time/frequency).
    :param filename: The file name (used to generate the song ID).
    :returns: A list of hashes as (hash, time offset, song_id) tuples.
    """
    hashes = []
    song_id = uuid.uuid5(uuid.NAMESPACE_OID, filename).int

    for anchor in points:
        for target in target_zone(
                anchor, points, settings.TARGET_T, settings.TARGET_F, settings.TARGET_START
        ):
            hashes.append((
                hash_point_pair(anchor, target),  # Hash value
                anchor[1],  # Time offset
                str(song_id)  # Song ID
            ))

    return hashes


def fingerprint_file(filename):
    """
    Generates fingerprint hashes for a file.

    :param filename: Path to the file.
    :returns: A list of generated hashes.
    """
    f, t, Sxx = file_to_spectrogram(filename)
    peaks = find_peaks(Sxx)
    peaks = idxs_to_tf_pairs(peaks, t, f)

    hashes = hash_points(peaks, filename)
    print(f"\nGenerated {len(hashes)} hashes for file '{filename}'.\n")
    print(f"Example hashes: {hashes[:5]} (showing first 5)")
    return hashes


def fingerprint_audio(frames):
    """
    Generates fingerprint hashes for audio data (e.g., while streaming a recording).

    :param frames: A mono audio stream.
    :returns: A list of generated hashes.
    """
    f, t, Sxx = my_spectrogram(frames)
    peaks = find_peaks(Sxx)
    peaks = idxs_to_tf_pairs(peaks, t, f)

    hashes = hash_points(peaks, "recorded")
    print(f"\nGenerated {len(hashes)} hashes from audio stream.\n")
    return hashes
