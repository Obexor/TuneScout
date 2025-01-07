import hashlib
import wave


def generate_hashes(audio_file, file_format):
    try:
        # Process WAV files
        if file_format == 'wav':
            with wave.open(audio_file, 'rb') as wav_file:
                # Read all frame data from the WAV file
                frames = wav_file.readframes(wav_file.getnframes())
                fingerprint = hashlib.sha256(frames).hexdigest()

        # Process MP3 files
        elif file_format == 'mp3':
            # Read raw byte data directly from the MP3 file
            with open(audio_file, 'rb') as f:
                raw_data = f.read()
                fingerprint = hashlib.sha256(raw_data).hexdigest()

        else:
            raise ValueError("Unsupported file format. Use 'wav' or 'mp3'.")

        return fingerprint
    except Exception as e:
        print(f"Error generating fingerprint: {e}")
        return None