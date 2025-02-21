import streamlit as st
import os
from Databank.Amazon_DynamoDB import AmazonDBConnectivity as ADC
from Databank.Amazon_S3 import S3Manager
from pipeline.fingerprinting import fingerprint_file, fingerprint_audio_stream
from pipeline.record import record_audio
from equalizer.features import equalizer_features
from Databank.User_Management import UserManager
import bcrypt
import tempfile
from streamlit import session_state
from pipeline.audioconverter import convert_to_wav


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

    :ivar db_manager: Manages database operations, including storing/retrieving song metadata and
        fingerprints in separate tables, SongsFingerprints and Hashes, in DynamoDB.
    :type db_manager: ADC
    :ivar bucket_name: Name of the S3 bucket used for song file storage.
    :type bucket_name: str
    :ivar s3_manager: Manages S3 operations, such as uploading and streaming song files.
    :type s3_manager: S3Manager
    """
    def __init__(self, aws_access_key_id, aws_secret_access_key, region_name, songs_table_name, hashes_table_name, bucket_name, user_table):
        self.db_manager_data = ADC(aws_access_key_id, aws_secret_access_key, region_name, songs_table_name)
        self.db_manager_fingerprints = ADC(aws_access_key_id, aws_secret_access_key, region_name, hashes_table_name)
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
                song_id = self.db_manager_data.get_latest_song_id() + 1

                # Step 5: Generate Fingerprints
                st.info("Generating fingerprints for the song...")
                file_type = os.path.splitext(uploaded_file.name)[1][1:]
                # Save the uploaded file as a temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as temp:
                    temp.write(uploaded_file.read())
                    input_path = temp.name

                # Ensure the output path is different from the input path
                output_path = input_path.replace("." + input_path.split('.')[-1], "_converted.wav")

                # Convert MP3 (or other formats) to WAV
                convert_to_wav(input_path, output_path)

                # Generate fingerprints from the converted WAV file
                fingerprints = fingerprint_file(output_path)

                if not fingerprints:
                    st.error("Fingerprint generation failed. Cannot proceed with uploading.")
                    return

                # Step 6: Check for Existing Song
                st.info("Checking if the song already exists in the database...")
                existing_match = self.db_manager_fingerprints.find_song_by_hashes(fingerprints)

                if existing_match:
                    st.warning(f"The song already exists in the database.")
                    # Compare Song ID from the match and fetch metadata
                    song_id = existing_match.get('SongID', None)  # Extract SongID from the matched result
                    if not song_id:
                        st.error("No SongID found in the match data. Unable to fetch metadata.")
                    else:
                        # Fetch all metadata using the song_id
                        metadata = next(
                            (item for item in self.db_manager_data.fetch_item() if item.get('SongID') == song_id),
                            None
                        )

                        if metadata:
                            # If metadata found, display the details
                            title = metadata.get('title', 'Unknown Title')
                            artist = metadata.get('artist', 'Unknown Artist')
                            album = metadata.get('album', 'Unknown Album')
                            st.subheader(f"**Title**: {title}")
                            st.write(f"**Artist**: {artist}")
                            st.write(f"**Album**: {album}")
                        else:
                            st.error(f"Metadata not found for SongID: {song_id}")  # Display metadata or match information
                    return

                # Step 7: Store Metadata and Fingerprints in Separate Tables in DynamoDB
                st.info("Storing song metadata in the SongsFingerprints table...")
                stored_metadata = self.db_manager_data.store_metadata_in_songs_table(song_id, song_data)


                st.info("Storing song fingerprints in the Hashes table...")
                stored_hashes = self.db_manager_fingerprints.store_fingerprints_in_hashes_table(song_id, fingerprints)
                #if not stored_hashes:
                #    st.error("Failed to store the fingerprints in the Hashes table. Please try again.")
                #    return

                # Step 8: Upload Song File to S3
                st.info("Uploading the song file to S3...")
                # Save the uploaded file locally
                with open(uploaded_file.name, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                # Upload to S3
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
                    # Step 5: Generate Fingerprints
                    st.info("Generating fingerprints for the song...")
                    file_type = os.path.splitext(compare_file.name)[1][1:]
                    # Save the uploaded file as a temporary file
                    with tempfile.NamedTemporaryFile(delete=False,
                                                     suffix=f".{compare_file.name.split('.')[-1]}") as temp:
                        temp.write(compare_file.read())
                        input_path = temp.name

                    # Ensure the output path is different from the input path
                    output_path = input_path.replace("." + input_path.split('.')[-1], "_converted.wav")

                    # Convert MP3 (or other formats) to WAV
                    convert_to_wav(input_path, output_path)

                    # Generate fingerprints from the converted WAV file
                    fingerprints = fingerprint_file(output_path)

                    if not fingerprints:
                        st.error("Fingerprint generation failed. Cannot proceed with uploading.")
                        return

                    st.info("Check Databse for match...")
                    match = self.db_manager_fingerprints.find_song_by_hashes(fingerprints)

                    if match:
                        st.success("Match found!")

                        # Compare Song ID from the match and fetch metadata
                        song_id = match.get('SongID', None)  # Extract SongID from the matched result
                        if not song_id:
                            st.error("No SongID found in the match data. Unable to fetch metadata.")
                        else:
                            # Fetch all metadata using the song_id
                            metadata = next(
                                (item for item in self.db_manager_data.fetch_item() if item.get('SongID') == song_id),
                                None
                            )

                            if metadata:
                                # If metadata found, display the details
                                title = metadata.get('title', 'Unknown Title')
                                artist = metadata.get('artist', 'Unknown Artist')
                                album = metadata.get('album', 'Unknown Album')
                                st.subheader(f"**Title**: {title}")
                                st.write(f"**Artist**: {artist}")
                                st.write(f"**Album**: {album}")
                            else:
                                st.error(f"Metadata not found for SongID: {song_id}")
                    else:
                        st.warning("No match found.")
                except Exception as e:
                    st.error(f"Error comparing song: {e}")

    def compare_recorded_song(self):
        st.header("Compare Recorded Song")
        if st.button("Record and Compare"):
            try:
                # 1. Record audio as NumPy data
                recorded_audio_data = record_audio()

                # 2. Generate fingerprints using fingerprint_audio_stream
                compare_hashes = fingerprint_audio_stream(recorded_audio_data)

                # 3. Compare hashes with the database
                match = self.db_manager_fingerprints.find_song_by_hashes(compare_hashes)

                # 4. Display the result
                if match:
                    st.success("Match found!")

                    # Compare Song ID from the match and fetch metadata
                    song_id = match.get('SongID', None)  # Extract SongID from the matched result
                    if not song_id:
                        st.error("No SongID found in the match data. Unable to fetch metadata.")
                    else:
                        # Fetch all metadata using the song_id
                        metadata = next(
                            (item for item in self.db_manager_data.fetch_item() if item.get('SongID') == song_id),
                            None
                        )

                        if metadata:
                            # If metadata found, display the details
                            title = metadata.get('title', 'Unknown Title')
                            artist = metadata.get('artist', 'Unknown Artist')
                            album = metadata.get('album', 'Unknown Album')
                            st.subheader(f"**Title**: {title}")
                            st.write(f"**Artist**: {artist}")
                            st.write(f"**Album**: {album}")
                        else:
                            st.error(f"Metadata not found for SongID: {song_id}")
                else:
                    st.warning("No match found.")
            except Exception as e:
                st.error(f"Error recording and comparing audio: {e}")

    def stream_uploaded_song(self):
        st.header("Stream Uploaded Songs")

        # Fetch songs from the database
        try:
            # Fetch songs dynamically (can be cached for improved performance)
            songs = self.db_manager_data.fetch_item()

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
