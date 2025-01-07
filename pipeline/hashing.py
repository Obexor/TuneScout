import hashlib
import wave
import os


def generate_hashes(audio_file, file_format, song_id, artist, title, album, s3_key):
    try:
        # Process WAV files
        if file_format == 'wav':  # Handle WAV file
            if hasattr(audio_file, 'read'):  # If it's a file-like object
                audio_file.seek(0)  # Ensure file pointer is at the beginning
                with wave.open(audio_file, 'rb') as wav_file:
                    frames = wav_file.readframes(wav_file.getnframes())
            else:  # If it's a file path
                with wave.open(audio_file, 'rb') as wav_file:
                    frames = wav_file.readframes(wav_file.getnframes())
            fingerprint = hashlib.sha256(frames).hexdigest()

        # Process MP3 files
        elif file_format == 'mp3':  # Handle MP3 file
            if hasattr(audio_file, 'read'):  # If it's a file-like object
                audio_file.seek(0)  # Ensure file pointer is at the beginning
                raw_data = audio_file.read()
            else:  # If it's a file path
                with open(audio_file, 'rb') as f:
                    raw_data = f.read()
            fingerprint = hashlib.sha256(raw_data).hexdigest()

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
    # Extract the file extension and remove the dot (e.g., '.wav' -> 'wav')
    file_format = os.path.splitext(file_path)[1][1:]
    return file_format