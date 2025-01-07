import hashlib
import wave
import numpy as np
from pydub import AudioSegment
import io

def generate_hashes(audio_file, song_id, artist, title, album, s3_key):
    try:
        # Load the audio file using pydub
        audio = AudioSegment.from_file(audio_file)
        
        # Convert audio to raw data
        audio_samples = np.array(audio.get_array_of_samples())

        # Generate a unique fingerprint using SHA-256
        fingerprint = hashlib.sha256(audio_samples.tobytes()).hexdigest()

        # Return fingerprint and metadata
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
        print(f"Error processing audio file: {e}")
        return []
