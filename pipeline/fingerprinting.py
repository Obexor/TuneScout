import uuid
import numpy as np
from scipy.io import wavfile  # Used for reading WAV files
from scipy.signal import spectrogram
from scipy.ndimage import maximum_filter
from pipeline import settings  # Load global settings


def my_spectrogram(audio):
    """Computes a spectrogram based on settings."""
    nperseg = int(settings.SAMPLE_RATE * settings.FFT_WINDOW_SIZE)
    return spectrogram(audio, settings.SAMPLE_RATE, nperseg=nperseg)


def file_to_spectrogram(filename):
    """
    Converts an audio file into a spectrogram:
    - Loads the WAV file.
    - Converts stereo to mono if needed.
    - Ensures the sampling rate matches `settings.SAMPLE_RATE`.

    :param filename: Path to the WAV file.
    :returns: Frequencies (f), timestamps (t), spectrogram data (Sxx)
    """
    sample_rate, audio_data = wavfile.read(filename)

    # Convert stereo to mono if needed
    if len(audio_data.shape) == 2:
        audio_data = audio_data.mean(axis=1).astype(np.int16)

    # Ensure correct sampling rate
    if sample_rate != settings.SAMPLE_RATE:
        raise ValueError(
            f"File has sampling rate {sample_rate}, expected {settings.SAMPLE_RATE}"
        )

    return my_spectrogram(audio_data)


def find_peaks(Sxx):
    """
    Identifies peak frequencies in the spectrogram using a maximum filter.
    - Peaks are the loudest frequencies in each region.
    - The number of peaks is controlled by `POINT_EFFICIENCY`.
    """
    data_max = maximum_filter(Sxx, size=settings.PEAK_BOX_SIZE, mode='constant', cval=0.0)
    peak_goodmask = (Sxx == data_max)
    y_peaks, x_peaks = peak_goodmask.nonzero()

    # Sort peaks by intensity
    peak_values = Sxx[y_peaks, x_peaks]
    sorted_indices = peak_values.argsort()[::-1]
    peaks = [(y_peaks[idx], x_peaks[idx]) for idx in sorted_indices]

    # Limit number of peaks based on efficiency setting
    area = Sxx.shape[0] * Sxx.shape[1]
    peak_limit = int((area / (settings.PEAK_BOX_SIZE ** 2)) * settings.POINT_EFFICIENCY)

    return peaks[:peak_limit]


def idxs_to_tf_pairs(idxs, t, f):
    """Converts time & frequency indices into actual values."""
    return np.array([(f[i[0]], t[i[1]]) for i in idxs])


def hash_point_pair(p1, p2):
    """Helper function to generate a hash from two time/frequency points."""
    return hash((p1[0], p2[0], p2[1]-p2[1]))


def target_zone(anchor, points, width, height, offset):
    """
    Defines the target zone for frequency-time pairs.
    - Selects points that fall within the specified time and frequency range after the anchor.

    :param anchor: The anchor point.
    :param points: List of time-frequency points.
    :param width: Width of the target zone (time range).
    :param height: Height of the target zone (frequency range).
    :param offset: Start time after the anchor point.
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
    Generates hashes from a list of peak points.
    - Uses the filename to generate a unique song ID.
    - Combines frequency peaks into pairs for unique matching.

    :param points: List of peak frequency-time points.
    :param filename: Path to the file (used for song ID generation).
    :returns: A list of hashes in the form (hash (as str), time offset (as str), song_id (as str)).
    """
    hashes = []
    song_id = str(uuid.uuid5(uuid.NAMESPACE_OID, filename).int)  # Song ID as STRING

    for anchor in points:
        for target in target_zone(
                anchor, points, settings.TARGET_T, settings.TARGET_F, settings.TARGET_START
        ):
            hashes.append((
                str(hash_point_pair(anchor, target)),  # Hash as STRING
                str(int(anchor[1])),  # Time offset as STRING
                song_id  # Song ID (already STRING)
            ))

    return hashes



def fingerprint_file(filename):
    """
    Generates a unique fingerprint for an audio file.
    """
    f, t, Sxx = file_to_spectrogram(filename)
    peaks = find_peaks(Sxx)
    peaks = idxs_to_tf_pairs(peaks, t, f)

    hashes = hash_points(peaks, filename)
    print(f"\n[✓] Fingerprinting completed for: {filename}")
    print(f"    - Total hashes: {len(hashes)}")
    print(f"    - Example hashes: {hashes[:3]} ... (showing 3 of {len(hashes)})\n")

    return hashes


def fingerprint_audio(frames):
    """
    Generates a fingerprint for streaming audio data.
    """
    f, t, Sxx = my_spectrogram(frames)
    peaks = find_peaks(Sxx)
    peaks = idxs_to_tf_pairs(peaks, t, f)

    hashes = hash_points(peaks, "recorded")
    print(f"\n[✓] Fingerprinting from audio stream completed.")
    print(f"    - Total hashes: {len(hashes)}\n")

    return hashes
