# fingerprint.py

import numpy as np
from scipy.ndimage import maximum_filter
import uuid
from pipeline import settings
from pipeline.audio_processing import file_to_spectrogram


def find_peaks(Sxx):
    """
    Identify peaks in a spectrogram using a frequency × time region.

    :param Sxx: Spectrogram matrix
    :return: List of peak indices
    """
    data_max = maximum_filter(Sxx, size=settings.PEAK_BOX_SIZE)
    peaks = (Sxx == data_max)
    y_peaks, x_peaks = peaks.nonzero()

    # Limit by POINT_EFFICIENCY
    peak_values = Sxx[y_peaks, x_peaks]
    sorted_indices = peak_values.argsort()[::-1]
    num_peaks = int((Sxx.size / (settings.PEAK_BOX_SIZE ** 2)) * settings.POINT_EFFICIENCY)

    return [(y_peaks[i], x_peaks[i]) for i in sorted_indices[:num_peaks]]


def idxs_to_coordinates(idxs, f, t):
    """
    Convert spectrogram indices to frequency-time coordinates.
    """
    return np.array([(f[idx[0]], t[idx[1]]) for idx in idxs])


def generate_hash(anchor, target):
    """
    Generate a hash for a point pair.
    """
    return hash((anchor[0], target[0], target[1] - anchor[1]))


def fingerprint_file(filename):
    """
    Fingerprints an audio file and returns hashes.
    """
    f, t, Sxx = file_to_spectrogram(filename)
    peaks = find_peaks(Sxx)
    coordinates = idxs_to_coordinates(peaks, f, t)

    hashes = []
    song_id = uuid.uuid4()
    for anchor in coordinates:
        # Create a target zone
        for target in coordinates:
            if target[1] < anchor[1] + settings.TARGET_START:
                continue
            if target[1] > anchor[1] + settings.TARGET_T:
                break
            hashes.append((generate_hash(anchor, target), anchor[1], str(song_id)))
    return hashes
