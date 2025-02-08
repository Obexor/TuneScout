import hashlib
import wave
import os
import hashlib
from scipy.ndimage import maximum_filter
import numpy as np


def generate_hashes(audio_file, file_format, song_id, artist, title, album, s3_key):
    """
    Generate a SHA-256 hash for the given audio file.

    :param audio_file: The audio file to hash (file-like object or file path)
    :param file_format: The format of the audio file ('wav' or 'mp3')
    :param song_id: Unique identifier for the song
    :param artist: Artist name
    :param title: Song title
    :param album: Album name
    :param s3_key: S3 key for the audio file
    :return: A list containing a dictionary with the hash and metadata, or None if an error occurs
    """
    try:
        # Process WAV files
        if file_format == 'wav':
            if hasattr(audio_file, 'read'):  # If it's a file-like object
                audio_file.seek(0)  # Ensure file pointer is at the beginning
                with wave.open(audio_file, 'rb') as wav_file:
                    frames = wav_file.readframes(wav_file.getnframes())
            else:  # If it's a file path
                with wave.open(audio_file, 'rb') as wav_file:
                    frames = wav_file.readframes(wav_file.getnframes())
            fingerprint = hashlib.sha256(frames).hexdigest()  # Generate SHA-256 hash

        # Process MP3 files
        elif file_format == 'mp3':
            if hasattr(audio_file, 'read'):  # If it's a file-like object
                audio_file.seek(0)  # Ensure file pointer is at the beginning
                raw_data = audio_file.read()
            else:  # If it's a file path
                with open(audio_file, 'rb') as f:
                    raw_data = f.read()
            fingerprint = hashlib.sha256(raw_data).hexdigest()  # Generate SHA-256 hash

        else:
            raise ValueError("Unsupported file format. Use 'wav' or 'mp3'.")

        return [
            {
                "Hash": fingerprint,
                "s3_key": s3_key,
                "SongID": song_id,
                "Artist": artist,
                "Title": title,
                "Album": album,
            }
        ]

    except Exception as e:
        print(f"Error generating fingerprint: {e}")
        return None

def get_file_format(file_path):
    """
    Extract the file format from the file path.

    :param file_path: The path to the file
    :return: The file format (e.g., 'wav', 'mp3')
    """
    file_format = os.path.splitext(file_path)[1][1:]  # Extract the file extension and remove the dot
    return file_format

def find_peaks(Sxx, threshold=0.1):
    """
    Find peak points in the spectrogram data.

    :param Sxx: Spectrogram (2D array)
    :param threshold: Amplitude threshold to treat peaks as significant
    :return: Boolean mask of peak positions
    """
    # Apply maximum filter to find local maxima
    neighborhood = maximum_filter(Sxx, size=(20, 20), mode='constant')
    peaks = (Sxx == neighborhood)  # Keep only maxima

    # Apply threshold
    peaks &= (Sxx >= threshold * Sxx.max())
    return peaks

def idxs_to_tf_pairs(peaks, t, f):
    """
    Convert peak indices into frequency-time pairs.

    :param peaks: 2D boolean matrix with peak positions
    :param t: Array of time points
    :param f: Array of frequency values
    :return: List of (time, frequency) pairs
    """
    peak_idxs = np.argwhere(peaks)  # Retrieve indices of True values
    return [(t[idx[1]], f[idx[0]]) for idx in peak_idxs]

def hash_point_pair(point_pair, song_id):
    """
    Hash a (time, frequency) point pair with the song ID.

    :param point_pair: Tuple (time, frequency)
    :param song_id: Song identifier
    :return: SHA-256 hash of the point pair and song ID
    """
    hash_input = f"{point_pair[0]:.5f}-{point_pair[1]:.5f}-{song_id}"
    return hashlib.sha256(hash_input.encode()).hexdigest()


def hash_points(points, song_id):
    """
    Hash a list of time-frequency points.

    :param points: List of (time, frequency) pairs
    :param song_id: Song identifier
    :return: List of hashes for the points
    """
    return [hash_point_pair(point, song_id) for point in points]

def get_file_format(file_path):
    """
    Extract the file format from the file path.

    :param file_path: The path to the file
    :return: The file format (e.g., 'wav', 'mp3')
    """
    file_format = os.path.splitext(file_path)[1][1:].lower()  # Extract the file extension and make lowercase
    return file_format

