import streamlit as st
import os
from Databank.Amazon_DynamoDB import AmazonDBConnectivity as ADC
from Databank.Amazon_S3 import S3Manager
from pipeline.hashing import generate_hashes
from pipeline.audio_processing import record_audio
from equalizer.features import equalizer_features
from Databank.User_Management import UserManager
import bcrypt
from streamlit import session_state

# Initialize the Streamlit application
# Check if authentication status and user session variables exist, initialize them if not
# These variables will track user authentication and app initialization states
if "authenticated" not in session_state:
    session_state["authenticated"] = False
if "user" not in session_state:
    session_state["user"] = None
session_state["initialize_app"] = False


class StreamlitApp:
    # Main class to handle the song recognition and streaming app functionalities
    # Provides methods for authentication, song uploading, comparison, streaming, and more
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
    :ivar user_manager: Manages user operations, including authentication and user creation.
    :type user_manager: UserManager
    """
    def __init__(self, aws_access_key_id, aws_secret_access_key, region_name, table_name, bucket_name, user_table):
        # Constructor initializes AWS-related managers (DynamoDB for metadata, S3 for storage)
        # Sets up database manager, bucket name, and user management functionality
        self.db_manager = ADC(aws_access_key_id, aws_secret_access_key, region_name, table_name)
        self.bucket_name = bucket_name
        self.user_manager = UserManager(aws_access_key_id, aws_secret_access_key, region_name, user_table)

    def authenticate_user(self):
        # Handles user authentication by verifying username and password
        # Updates session state upon successful login
        st.header("Login")
        username = st.text_input("Username")  # Input field for username
        password = st.text_input("Password", type="password")  # Input field for password (masked)
        if st.button("Login"):  # Login button triggers authentication process

            enc_password = self.user_manager.get_user_password(password)  # Encrypt the input password for comparison
            # Check if the username exists in the database
            if enc_password is None:
                st.error("Invalid username or password.")
                return
            hashed_password = self.user_manager.get_user_password(username)  # Retrieve stored hashed password
            # Validate the input password against the stored hashed password
            if not bcrypt.checkpw(enc_password.encode(), hashed_password.encode()):
                session_state["authenticated"] = True
                session_state["user"] = username
                st.success(f"Welcome, {username}!")

            else:  # Handle failed authentication
                st.error("Invalid username or password.")

    def sign_up_user(self):
        # Allows users to sign up by creating a username and password
        # Performs data validation and saves the user information in DynamoDB
        st.header("Sign Up")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Sign Up"):
            if not username or not password:  # Ensure both fields are filled
                st.error("All fields are required.")
                return
            hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()  # Encrypt the password
            # Save the new user credentials in the database
            success = self.user_manager.create_user(username, hashed_password)
            if success:  # Provide user feedback on successful or failed sign-up
                st.success("User created successfully! Please log in.")
            else:
                st.error("Sign-up failed. The username may already exist.")

    def upload_song_with_metadata(self):
        # Handles song uploads with metadata input by user
        # Steps: File upload, metadata entry, fingerprint generation, duplicate check, and S3 upload
        st.header("Upload Song with Metadata")

        # Step 1: File Upload
        # User uploads a song (supported types: MP3/WAV)
        uploaded_file = st.file_uploader("Upload a song (MP3/WAV)", type=["mp3", "wav"])

        # Step 2: Metadata Input
        artist = st.text_input("Artist", "Unknown")  # Artist input (default: "Unknown")
        title = st.text_input("Title", "Unknown Title")  # Title input (default: "Unknown Title")
        album = st.text_input("Album", "Unknown Album")  # Album input (default: "Unknown Album")

        # Confirm upload
        if st.button("Upload Song"):  # Upload button triggers the file and metadata processing
            # Validate uploaded file and metadata input
            if not uploaded_file:
                st.error("Please upload a valid MP3 or WAV file.")
                return

            try:
                # Step 3: Assign Metadata
                # Organize the metadata provided by the user into a dictionary
                song_data = {
                    "artist": artist.strip() or "Unknown",
                    "title": title.strip() or "Unknown Title",  # Use default title if input is empty
                    "album": album.strip() or "Unknown Album",
                    "s3_key": f"songs/{uploaded_file.name}"
                }
                st.info(
                    f"Processing: Title='{song_data['title']}', Artist='{song_data['artist']}', Album='{song_data['album']}'")

                # Step 4: Generate Song ID
                song_id = self.db_manager.get_latest_song_id() + 1  # Generate unique Song ID based on the latest ID

                # Step 5: Generate Fingerprints
                st.info("Generating fingerprints for the song...")  # Inform user about the fingerprinting process
                # Determine the file extension of the uploaded file
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

                if not fingerprints:  # Stop process if fingerprint generation fails
                    st.error("Fingerprint generation failed. Cannot proceed with uploading.")
                    return
                # Step 6: Check for Existing Song
                st.info("Checking if the song already exists in the database...")
                existing_match = self.db_manager.find_song_by_hashes(fingerprints)  # Check for duplicates in the database

                if existing_match:
                    st.warning(f"The song already exists in the database.")
                    st.json(existing_match)  # Display metadata or match information
                    return

                # Step 7: Store Metadata and Fingerprints in DynamoDB
                st.info("Storing song metadata and fingerprints in the database...")  # Feedback for database storage process
                # Save the song metadata and fingerprints in DynamoDB
                stored = self.db_manager.store_song(song_data, fingerprints)

                if not stored:
                    st.error("Failed to store the song data in the database. Please try again.")
                    return

                # Step 8: Upload Song File to S3
                st.info("Uploading the song file to S3...")  # Feedback for S3 upload process
                # Temporarily save the song locally for S3 upload
                # Save the uploaded file locally
                with open(uploaded_file.name, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                # Upload to S3
                self.s3_manager.upload_file(
                    uploaded_file.name,
                    f"songs/{uploaded_file.name}"  # Place files in the 'songs/' folder in S3
                )

                st.success(f"Successfully uploaded '{song_data['title']}' by '{song_data['artist']}'!")

            except Exception as e:  # Catch any issues during upload and fingerprint generation
                st.error(f"Error occurred during upload: {str(e)}")

    def compare_uploaded_song(self):
        # Allows users to upload a song and compare it against songs in the database
        # Steps: Upload song, generate fingerprints, retrieve matches from database
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
                record_audio("recorded_compare.wav")
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
                                # Generate the pre-signed URL for streaming from S3
                                song_uri = self.s3_manager.get_presigned_url(s3_key)
                                if not song_uri:
                                    st.error(f"Failed to generate a streaming URL for '{title}'.")
                                else:
                                    # Stream the audio using the Streamlit audio player
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
