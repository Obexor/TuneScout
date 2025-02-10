import streamlit as st
import bcrypt
import tempfile
from Databank.Amazon_DynamoDB import AmazonDBConnectivity as ADC
from Databank.Amazon_S3 import S3Manager
from pipeline.audio_processing import record_audio
from equalizer.features import equalizer_features
from Databank.User_Management import UserManager
from pydub import AudioSegment
from streamlit import session_state
from pipeline.audio_processing import file_to_spectrogram
from pipeline.hashing import find_peaks, idxs_to_tf_pairs, hash_points
from pipeline.hashing import get_file_format

# Initialize the Streamlit application
if "authenticated" not in session_state:
    session_state["authenticated"] = False
if "user" not in session_state:
    session_state["user"] = None
session_state["initialize_app"] = False


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
    def __init__(self, aws_access_key_id, aws_secret_access_key, region_name, table_name, bucket_name, user_table):
        self.db_manager = ADC(aws_access_key_id, aws_secret_access_key, region_name, table_name)
        self.s3_manager = S3Manager(aws_access_key_id, aws_secret_access_key, region_name, bucket_name)
        self.user_manager = UserManager(aws_access_key_id, aws_secret_access_key, region_name, user_table)

    def authenticate_user(self):
        st.header("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            enc_password = self.user_manager.get_user_password(password)
            if enc_password is None:
                st.error("Invalid username or password.")
                return
            hashed_password = self.user_manager.get_user_password(username)
            if not bcrypt.checkpw(enc_password.encode(), hashed_password.encode()):
                session_state["authenticated"] = True
                session_state["user"] = username
                st.success(f"Welcome, {username}!")

            else:
                st.error("Invalid username or password.")

    def sign_up_user(self):
        st.header("Sign Up")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Sign Up"):
            if not username or not password:
                st.error("All fields are required.")
                return
            hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            success = self.user_manager.create_user(username, hashed_password)
            if success:
                st.success("User created successfully! Please log in.")
            else:
                st.error("Sign-up failed. The username may already exist.")

    def upload_song_with_metadata(self):
        st.header("Upload Song with Metadata")

        # Step 1: Upload file
        uploaded_file = st.file_uploader("Upload a song (MP3/WAV)", type=["mp3", "wav"])

        # Step 2: Input metadata
        artist = st.text_input("Artist", "Unknown")
        title = st.text_input("Title", "Unknown Title")
        album = st.text_input("Album", "Unknown Album")

        # Confirm upload
        if st.button("Upload Song"):
            if not uploaded_file:
                st.error("Please upload a valid MP3 or WAV file.")
                return

            try:
                # Step 3: Detect file format
                file_format = get_file_format(uploaded_file.name)
                if file_format not in ["wav", "mp3"]:
                    st.error("Unsupported file format.")
                    return

                # Convert MP3 to WAV if necessary
                if file_format == "mp3":
                    st.info("Converting MP3 to WAV format...")
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav_file:
                        audio = AudioSegment.from_file(uploaded_file, format="mp3")
                        audio.export(temp_wav_file.name, format="wav")
                        wav_file_path = temp_wav_file.name
                else:
                    uploaded_file.seek(0)
                    wav_file_path = uploaded_file

                # Step 4: Prepare metadata
                song_data = {
                    "artist": artist.strip() or "Unknown",
                    "title": title.strip() or "Unknown Title",
                    "album": album.strip() or "Unknown Album",
                    "s3_key": f"songs/{uploaded_file.name}"
                }
                st.info(f"Processing: {song_data}")

                # Step 5: Generate Song ID
                song_id = self.db_manager.get_latest_song_id() + 1

                # Step 6: Generate fingerprints
                st.info("Generating fingerprints...")
                f, t, Sxx = file_to_spectrogram(wav_file_path)
                peaks = find_peaks(Sxx)
                tf_pairs = idxs_to_tf_pairs(peaks, t, f)
                fingerprints = hash_points(tf_pairs, title)

                if not fingerprints:
                    st.error("Fingerprint generation failed.")
                    return

                # Step 7: Check for existing song
                st.info("Checking if song already exists...")
                existing_match = self.db_manager.find_song_by_hashes(fingerprints)
                if existing_match:
                    st.warning("The song already exists in the database.")
                    st.json(existing_match)
                    return

                # Step 8: Store metadata and fingerprints
                st.info("Storing song data in the database...")
                if not self.db_manager.store_song(song_data, fingerprints):
                    st.error("Failed to store the song data. Try again.")
                    return

                # Step 9: Upload song file to S3
                st.info("Uploading the song file to S3...")
                with open(uploaded_file.name, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                self.s3_manager.upload_file(uploaded_file.name, f"songs/{uploaded_file.name}")

                st.success(f"Successfully uploaded '{song_data['title']}' by '{song_data['artist']}'!")

            except Exception as e:
                st.error(f"Error during upload: {str(e)}")

    def compare_uploaded_song(self):
        st.header("Compare Uploaded Song")
        compare_file = st.file_uploader("Upload a song to compare", type=["mp3", "wav"])

        if compare_file:
            if st.button("Compare"):
                try:
                    # Step 1: Generate Fingerprints for the uploaded file
                    st.info("Calculating Spectrogram and generating Fingerprints for the file...")
                    f, t, Sxx = file_to_spectrogram(compare_file)
                    peaks = find_peaks(Sxx)
                    peaks_t_f = idxs_to_tf_pairs(peaks, t, f)
                    compare_hashes = hash_points(peaks_t_f, compare_file.name)

                    # Step 2: Find matches in the database
                    st.info("Matching against the database...")
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
                # Step 1: Record audio
                audio = record_audio("recorded_compare.wav")

                # Step 2: Process the recorded audio
                st.info("Calculating Spectrogram and generating Fingerprints for the recorded audio...")
                f, t, Sxx = file_to_spectrogram(audio)
                peaks = find_peaks(Sxx)
                peaks_t_f = idxs_to_tf_pairs(peaks, t, f)
                compare_hashes = hash_points(peaks_t_f, "recorded_compare.wav")

                # Step 3: Find matches in the database
                st.info("Matching against the database...")
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

        # Fetch songs from the database
        try:
            # Fetch songs dynamically (can be cached for improved performance)
            songs = self.db_manager.fetch_item()

            if songs:
                st.info("Songs found in the database:")

                # Display a list of songs with streaming buttons
                for index, song in enumerate(songs):
                    title = song.get('Title', 'Unknown Title')
                    artist = song.get('Artist', 'Unknown Artist')
                    album = song.get('Album', 'Unknown Album')
                    s3_key = song.get('s3_key')  # Fetch the S3 object key for this song

                    # Ensure the s3_key exists
                    if not s3_key:
                        st.warning(f"Missing S3 key for song: {title}")
                        continue  # Skip this song since it can't be streamed

                    # Display song details
                    st.subheader(f"Song {index + 1}")
                    st.write(f"**Title**: {title}")
                    st.write(f"**Artist**: {artist}")
                    st.write(f"**Album**: {album}")

                    # Button to stream the song
                    if st.button(f"Stream {title}", key=f"stream-{index}"):
                        with st.spinner("Fetching the song..."):  # Show a spinner while streaming is initialized
                            try:
                                try:
                                    song_uri = self.s3_manager.get_presigned_url(s3_key)
                                    if not song_uri:
                                        st.error(f"Failed to generate a streaming URL for '{title}'.")
                                    else:
                                        # Stream the audio using the Streamlit audio player
                                        st.audio(song_uri, format="audio/mp3")  # Use the URI to play the audio
                                except Exception as e:
                                    st.error(f"Error: The song '{title}' is missing or could not be accessed in S3. Details: {e}")
                                    st.audio(song_uri, format="audio/mp3")  # Use the URI to play the audio
                            except Exception as e:
                                st.error(f"Error while streaming '{title}': {e}")
            else:
                st.warning("No songs available in the database.")

        except Exception as e:
            # Provide a meaningful error message if song fetching fails
            st.error(f"Error fetching songs: {e}")

    def run(self):

        if not session_state["authenticated"]:
            st.sidebar.title("Welcome")
            auth_mode = st.sidebar.radio("Choose an option", ["Login", "Sign Up"])
            if auth_mode == "Login":
                self.authenticate_user()
            elif auth_mode == "Sign Up":
                self.sign_up_user()
            return

        st.sidebar.title(f"Welcome, {session_state['user']}!")
        if st.sidebar.button("Logout"):
            session_state["authenticated"] = False
            session_state["user"] = None
            return

        if session_state["authenticated"]:
            st.title("Song Recognition and Streaming App")
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
                equalizer_features()
