import hashlib
import wave
import os

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