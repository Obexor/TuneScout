import uuid
from pipeline.audio_processing import file_to_spectrogram, find_peaks, idxs_to_tf_pairs
from pipeline import settings


def hash_point_pair(p1, p2):
    """
    Generates a hash from two time-frequency points.

    :param p1: First frequency-time pair
    :param p2: Second frequency-time pair
    :return: Hash value
    """
    return hash((p1[0], p2[0], p2[1] - p1[1]))


def target_zone(anchor, points, width, height, t):
    """
    Creates a target zone based on the given anchor point.

    :param anchor: The anchor point
    :param points: List of points
    :param width: Width of the target zone
    :param height: Height of the target zone
    :param t: Time offset of the target zone from the anchor
    :return: Iterator over points in the target zone
    """
    x_min = anchor[1] + t
    x_max = x_min + width
    y_min = anchor[0] - (height * 0.5)
    y_max = y_min + height

    for point in points:
        if point[0] < y_min or point[0] > y_max:
            continue
        if point[1] < x_min or point[1] > x_max:
            continue
        yield point


def hash_points(points, filename):
    """
    Generates hashes from a list of peaks.

    :param points: List of peaks
    :param filename: Filename to generate a song ID
    :return: List of hashes
    """
    hashes = []
    song_id = uuid.uuid5(uuid.NAMESPACE_OID, filename).int
    for anchor in points:
        for target in target_zone(
                anchor, points, settings.TARGET_T, settings.TARGET_F, settings.TARGET_START
        ):
            hashes.append((
                hash_point_pair(anchor, target),  # The computed hash
                anchor[1],  # Time offset
                str(song_id)  # Song ID
            ))
    return hashes


def fingerprint_file(filename):
    """
    Generates a fingerprint for a file.

    :param filename: File path
    :return: List of hashes
    """
    f, t, Sxx = file_to_spectrogram(filename)
    peaks = find_peaks(Sxx)
    peaks = idxs_to_tf_pairs(peaks, t, f)
    return hash_points(peaks, filename)
