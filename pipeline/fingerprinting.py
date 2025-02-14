import uuid
import numpy as np
from scipy.io import wavfile
from scipy.signal import spectrogram
from scipy.ndimage import maximum_filter
from pipeline import settings  # Global settings for processing


# ========================
# Helper Functions
# ========================

def compute_spectrogram(audio):
    """
    Computes a spectrogram based on global settings.
    :param audio: NumPy array of audio data.
    :returns: Frequencies (f), timestamps (t), spectrogram data (Sxx)
    """
    nperseg = int(settings.SAMPLE_RATE * settings.FFT_WINDOW_SIZE)
    return spectrogram(audio, settings.SAMPLE_RATE, nperseg=nperseg)


def load_audio_file(filename):
    """
    Loads a WAV file and converts stereo to mono if needed.
    Ensures the sample rate matches the expected value.

    :param filename: Path to the WAV file.
    :returns: NumPy array of audio data, sampling rate
    """
    sample_rate, audio_data = wavfile.read(filename)

    # Convert stereo to mono if necessary
    if len(audio_data.shape) == 2:
        audio_data = audio_data.mean(axis=1).astype(np.int16)

    # Verify that the sample rate matches the expected settings
    if sample_rate != settings.SAMPLE_RATE:
        raise ValueError(
            f"File has sampling rate {sample_rate}, but {settings.SAMPLE_RATE} was expected."
        )

    return audio_data


def convert_to_tf_pairs(peaks, t, f):
    """
    Converts frequency and time indices into actual frequency-time values.
    :param peaks: List of peaks as (y, x) indices.
    :param t: Timestamps from the spectrogram.
    :param f: Frequencies from the spectrogram.
    :returns: Array of (frequency, time) pairs.
    """
    return np.array([(f[i[0]], t[i[1]]) for i in peaks])


def generate_hash(p1, p2):
    """
    Generates a hash from two frequency-time points.
    :param p1: Starting point as (frequency, time).
    :param p2: Target point as (frequency, time).
    :returns: Hash combining the two points.
    """
    return hash((p1[0], p2[0], p2[1] - p1[1]))


# ========================
# Core Functions
# ========================

def extract_spectrogram(filename):
    """
    Converts an audio file to a spectrogram.
    :param filename: Path to the audio file.
    :returns: Frequencies (f), timestamps (t), spectrogram data (Sxx)
    """
    audio_data = load_audio_file(filename)
    return compute_spectrogram(audio_data)


def find_spectrogram_peaks(Sxx):
    """
    Identifies frequency peaks in the spectrogram using a maximum filter.
    Peaks are chosen as the loudest points within a region.

    :param Sxx: Spectrogram data matrix.
    :returns: List of peaks as (y, x) indices.
    """
    data_max = maximum_filter(Sxx, size=settings.PEAK_BOX_SIZE, mode='constant', cval=0.0)
    peak_mask = (Sxx == data_max)
    y_peaks, x_peaks = peak_mask.nonzero()

    # Sort peaks by intensity
    peak_values = Sxx[y_peaks, x_peaks]
    sorted_indices = peak_values.argsort()[::-1]
    peaks = [(y_peaks[idx], x_peaks[idx]) for idx in sorted_indices]

    # Limit number of peaks based on efficiency
    total_area = Sxx.shape[0] * Sxx.shape[1]
    peak_limit = int((total_area / (settings.PEAK_BOX_SIZE ** 2)) * settings.POINT_EFFICIENCY)

    return peaks[:peak_limit]


def compute_target_zone(anchor, points, width, height, offset):
    """
    Defines the target zone for pairing frequency-time points relative to an anchor point.

    :param anchor: Anchor point (frequency, time).
    :param points: List of frequency-time points.
    :param width: Width of the target zone (time range).
    :param height: Height of the target zone (frequency range).
    :param offset: Start time offset after the anchor point.
    :returns: Generator of points within the target zone.
    """
    x_min = anchor[1] + offset
    x_max = x_min + width
    y_min = anchor[0] - (height * 0.5)
    y_max = y_min + height

    for point in points:
        if y_min <= point[0] <= y_max and x_min <= point[1] <= x_max:
            yield point


def generate_hashes(points, filename):
    """
    Generates hashes from frequency-time peak pairs.
    Uses the filename to create a unique song ID.

    :param points: List of frequency-time points.
    :param filename: Path to the file (used for generating a song ID).
    :returns: List of hashes in the form (hash, time offset, song_id).
    """
    hashes = []
    song_id = str(uuid.uuid5(uuid.NAMESPACE_OID, filename).int)  # Unique song ID

    for anchor in points:
        for target in compute_target_zone(
                anchor, points, settings.TARGET_T, settings.TARGET_F, settings.TARGET_START):
            hashes.append((
                str(generate_hash(anchor, target)),
                str(int(anchor[1])),
                song_id
            ))

    return hashes


# ========================
# Main Processing Functions
# ========================

def fingerprint_file(filename):
    """
    Generates a unique fingerprint for an audio file.
    :param filename: Path to the audio file.
    :returns: List of hashes.
    """
    f, t, Sxx = extract_spectrogram(filename)
    peaks = find_spectrogram_peaks(Sxx)
    peak_points = convert_to_tf_pairs(peaks, t, f)
    hashes = generate_hashes(peak_points, filename)

    print(f"\n[✓] Fingerprinting completed for: {filename}")
    print(f"    - Total hashes: {len(hashes)}")
    print(f"    - Example hashes: {hashes[:3]} ... (showing 3 of {len(hashes)})\n")
    return hashes


def fingerprint_audio_stream(frames):
    """
    Generates a fingerprint for live audio streams.
    :param frames: Audio frames as a NumPy array.
    :returns: List of hashes.
    """
    f, t, Sxx = compute_spectrogram(frames)
    peaks = find_spectrogram_peaks(Sxx)
    peak_points = convert_to_tf_pairs(peaks, t, f)
    hashes = generate_hashes(peak_points, "streamed_audio")

    print(f"\n[✓] Fingerprinting for audio stream completed.")
    print(f"    - Total hashes: {len(hashes)}\n")
    return hashes
