import hashlib
import wave
import numpy as np

def generate_hashes(audio_file, song_id, artist, title, album):
    try:
        # Open the audio file using the wave module
        with wave.open(audio_file, 'rb') as wf:
            # Read raw audio frames
            frames = wf.readframes(wf.getnframes())
            # Convert frames to a numpy array
            audio_samples = np.frombuffer(frames, dtype=np.int16)

        # Generate a unique fingerprint using SHA-256
        fingerprint = hashlib.sha256(audio_samples.tobytes()).hexdigest()

        # Return fingerprint and metadata
        return [
            {
                "Hash": fingerprint,
                "Offset": "0",
                "SongID": song_id,
                "Artist": artist,
                "Title": title,
                "Album": album,
            }
        ]
    except wave.Error as e:
        print(f"Error processing audio file: {e}")
        return []
