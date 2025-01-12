import streamlit as st
import wave
import numpy as np
import os
import wave
import soundfile as sf
from Databank.Amazon_DynamoDB import AmazonDBConnectivity as ADC
from Databank.Amazon_S3 import S3Manager
from pipeline.hashing import generate_hashes
from pipeline.audio_processing import record_audio
from equalizer.filters import butter_lowpass_filter, butter_highpass_filter, equalizer
from equalizer.visualization import plot_signal, plot_spectrum



class StreamlitApp:
    """
    Handles functionalities for a Streamlit-based song recognition and streaming application.

    The class provides methods for uploading songs with metadata, comparing uploaded or
    recorded songs against a database, and streaming available songs. It relies on an
    Amazon DynamoDB-based database manager (ADC) and an Amazon S3 manager for storage/streaming.

    :ivar db_manager: Manages database operations, including storing/retrieving song metadata
        and fingerprint data in DynamoDB.
    :type db_manager: ADC
    :ivar bucket_name: Name of the S3 bucket used for song file storage.
    :type bucket_name: str
    :ivar s3_manager: Manages S3 operations, such as uploading and streaming song files.
    :type s3_manager: S3Manager
    """
    def __init__(self, aws_access_key_id, aws_secret_access_key, region_name, table_name, bucket_name):
        self.db_manager = ADC(aws_access_key_id, aws_secret_access_key, region_name, table_name)
        self.bucket_name = bucket_name
        self.s3_manager = S3Manager(aws_access_key_id, aws_secret_access_key, region_name, bucket_name)

    def upload_song_with_metadata(self):
        st.header("Upload Song with Metadata")

        # Step 1: Upload File and get filetype
        uploaded_file = st.file_uploader("Upload a song (MP3/WAV)", type=["mp3", "wav"])

        # Step 2: Metadata Input
        artist = st.text_input("Artist", "Unknown")  # Default value as "Unknown"
        title = st.text_input("Title", "Unknown Title")
        album = st.text_input("Album", "Unknown Album")

        # Confirm upload
        if st.button("Upload Song"):
            if not uploaded_file:
                st.error("Please upload a valid MP3 or WAV file.")
                return

            try:
                # Step 3: Assign Metadata
                song_data = {
                    "artist": artist.strip() or "Unknown",
                    "title": title.strip() or "Unknown Title",
                    "album": album.strip() or "Unknown Album",
                    "s3_key": f"songs/{uploaded_file.name}"
                }
                st.info(
                    f"Processing: Title='{song_data['title']}', Artist='{song_data['artist']}', Album='{song_data['album']}'")

                # Step 4: Generate Song ID
                song_id = self.db_manager.get_latest_song_id() + 1

                # Step 5: Generate Fingerprints
                st.info("Generating fingerprints for the song...")
                file_type = os.path.splitext(uploaded_file.name)[1][1:]
                fingerprints = generate_hashes(
                    uploaded_file,  # Input file
                    file_type,
                    song_id,  # Song ID
                    song_data['artist'],  # Artist
                    song_data['title'],  # Title
                    song_data['album'], # Album
                    song_data['s3_key']  # S3-Key
                )

                if not fingerprints:
                    st.error("Fingerprint generation failed. Cannot proceed with uploading.")
                    return
                # Step 6: Check for Existing Song
                st.info("Checking if the song already exists in the database...")
                existing_match = self.db_manager.find_song_by_hashes(fingerprints)

                if existing_match:
                    st.warning(f"The song already exists in the database.")
                    st.json(existing_match)  # Display metadata or match information
                    return

                # Step 7: Store Metadata and Fingerprints in DynamoDB
                st.info("Storing song metadata and fingerprints in the database...")
                stored = self.db_manager.store_song(song_data, fingerprints)

                if not stored:
                    st.error("Failed to store the song data in the database. Please try again.")
                    return

                # Step 8: Upload Song File to S3
                st.info("Uploading the song file to S3...")
                self.s3_manager.upload_file(
                    uploaded_file.name,
                    f"songs/{uploaded_file.name}"  # Place files in the 'songs/' folder in S3
                )

                st.success(f"Successfully uploaded '{song_data['title']}' by '{song_data['artist']}'!")

            except Exception as e:
                st.error(f"Error occurred during upload: {str(e)}")

    def compare_uploaded_song(self):
        st.header("Compare Uploaded Song")
        compare_file = st.file_uploader("Upload a song to compare", type=["mp3", "wav"])
        if compare_file:
            if st.button("Compare"):
                try:
                    song_id = self.db_manager.get_latest_song_id() + 1
                    file_type = os.path.splitext(compare_file.name)[1][1:]
                    compare_hashes = generate_hashes(compare_file, file_type , song_id, "", "", "","")
                    match = self.db_manager.find_song_by_hashes(compare_hashes)
                    if match:
                        st.success("Match found!")
                        title = match.get('Title', 'Unknown Title')
                        artist = match.get('Artist', 'Unknown Artist')
                        album = match.get('Album', 'Unknown Album')
                        st.subheader(f"**Title**: {title}")
                        st.write(f"**Artist**: {artist}")
                        st.write(f"**Album**: {album}")

                    else:
                        st.warning("No match found.")
                except Exception as e:
                    st.error(f"Error comparing song: {e}")

    def compare_recorded_song(self):
        st.header("Compare Recorded Song")
        if st.button("Record and Compare"):
            try:
                record_audio("recorded_compare.wav", duration=5)
                with open("recorded_compare.wav", "rb") as recorded_file:
                    file_type = os.path.splitext("recorded_compare.wav")[1][1:]
                    compare_hashes = generate_hashes(recorded_file, file_type, self.db_manager.get_latest_song_id() + 1, "", "",
                                                     "", "")
                    match = self.db_manager.find_song_by_hashes(compare_hashes)
                    if match:
                        st.success("Match found!")
                        title = match.get('Title', 'Unknown Title')
                        artist = match.get('Artist', 'Unknown Artist')
                        album = match.get('Album', 'Unknown Album')
                        st.subheader(f"**Title**: {title}")
                        st.write(f"**Artist**: {artist}")
                        st.write(f"**Album**: {album}")
                    else:
                        st.warning("No match found.")
            except Exception as e:
                st.error(f"Error recording and comparing audio: {e}")

    def stream_uploaded_song(self):
        st.header("Stream Uploaded Songs")

        # Fetch songs from DynamoDB when the button is clicked
        if st.button("List Songs"):
            try:
                # Use self.db_manager to call the list_all_records method
                songs = self.db_manager.fetch_item()

                if songs:
                    st.info("Songs found in the database:")

                    for index, song in enumerate(songs):
                        # Fetch and display full metadata
                        title = song.get('Title', 'Unknown Title')
                        artist = song.get('Artist', 'Unknown Artist')
                        album = song.get('Album', 'Unknown Album')
                        s3_key = song.get('s3_key')

                        # Warn if required fields are missing
                        if not s3_key:
                            st.warning(f"Missing S3 key for song '{title}' at index {index}")
                            continue

                        # Display song metadata in a structured way
                        st.subheader(f"Song {index + 1}")
                        st.write(f"**Title**: {title}")
                        st.write(f"**Artist**: {artist}")
                        st.write(f"**Album**: {album}")

                        # Add a button for streaming
                        if st.button(f"Stream {title}", key=f"stream-{index}"):
                            song_uri = self.s3_manager.get_presigned_url(s3_key)
                            if song_uri:
                                st.audio(song_uri)
                            else:
                                st.error(f"Failed to stream the song: {title}")
                else:
                    st.warning("No songs found in the database.")
            except Exception as e:
                st.error(f"Error streaming songs: {e}")

    def run(self):
        st.title("Song Recognition and Streaming App")
        st.sidebar.title("Navigation")
        app_mode = st.sidebar.radio("Choose a function",
                                ["Upload Song", "Compare Uploaded Song",
                                 "Compare Recorded Song", "Stream Songs", "Equalizer"])
        
        
        if app_mode == "Upload Song":
            self.upload_song_with_metadata()
        elif app_mode == "Compare Uploaded Song":
            self.compare_uploaded_song()
        elif app_mode == "Compare Recorded Song":
            self.compare_recorded_song()
        elif app_mode == "Stream Songs":
            self.stream_uploaded_song()
        elif app_mode == "Equalizer":
            self.equalizer_features()


    def equalizer_features(self):
        st.header("Equalizer")
        st.write("This feature allows you to modify and equalize uploaded WAV files in real-time.")

        from matplotlib.figure import Figure
        import matplotlib.pyplot as plt

        # Step 1: File Upload
        uploaded_file = st.file_uploader("Upload a WAV or MP3 file", type=["wav", "mp3"])

        # Step 2: Adjust Equalizer
        if uploaded_file:
            st.subheader("Equalizer Settings")
            bass_gain = st.slider("Bass Gain (dB)", -10, 10, 1)
            midrange_gain = st.slider("Midrange Gain (dB)", -10, 10, 1)
            treble_gain = st.slider("Treble Gain (dB)", -10, 10, 1)

            # Step 3: Process WAV file
            import tempfile
            file_type = uploaded_file.name.split(".")[-1].lower()

            if file_type == "wav":
                with wave.open(uploaded_file, "rb") as wav_file:
                    params = wav_file.getparams()
                    n_channels, sample_width, frame_rate, n_frames, _, _ = params
                    raw_data = wav_file.readframes(n_frames)
            elif file_type == "mp3":
                data, samplerate = sf.read(uploaded_file)
                n_channels = data.shape[1] if len(data.shape) > 1 else 1
                sample_width = 2  # Assuming 16-bit PCM
                frame_rate = samplerate
                n_frames = len(data)
                raw_data = (data * (2**15 - 1)).astype(np.int16).tobytes()

            st.info("Processing the WAV file...")
            audio_signal = np.frombuffer(raw_data, dtype=np.int16)
            time = np.linspace(0, len(audio_signal) / frame_rate, num=len(audio_signal))

            # Apply filters using the custom equalizer module
            bass = butter_lowpass_filter(audio_signal, cutoff=200, fs=frame_rate, gain=bass_gain)
            midrange = equalizer(audio_signal, freq_range=(200, 3000), fs=frame_rate, gain=midrange_gain)
            treble = butter_highpass_filter(audio_signal, cutoff=3000, fs=frame_rate, gain=treble_gain)
            equalized_signal = bass + midrange + treble

            # Step 4: Visualization
            st.subheader("Equalized Signal Visualization")
            fig = Figure(figsize=(10, 4))
            ax = fig.add_subplot(1, 1, 1)
            ax.plot(time, equalized_signal, label="Equalized Signal")
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Amplitude")
            ax.legend()
            st.pyplot(fig)

            # Write to temporary WAV file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                with wave.open(temp_file.name, "wb") as out_wav:
                    out_wav.setnchannels(n_channels)
                    out_wav.setsampwidth(sample_width)
                    out_wav.setframerate(frame_rate)
                    equalized_signal = np.clip(equalized_signal, -32768, 32767).astype(np.int16)
                    out_wav.writeframes(equalized_signal.tobytes())
                temp_file_path = temp_file.name

        # Step 5: Play and Download Equalized WAV
            st.audio(temp_file_path, format="audio/wav")
            st.download_button(
                label="Download Equalized WAV",
                data=open(temp_file_path, "rb").read(),
                file_name="equalized.wav",
                mime="audio/wav"
            )

        else:
            st.warning("Please upload an MP3 file to use the equalizer.")
