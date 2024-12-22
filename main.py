from pipeline.audio_processing import record_audio
from pipeline.hashing import generate_hashes
from pipeline.database import DatabaseManager
from pipeline.config import DB_PATH
import streamlit as st

# Initialize the database manager with the specified database path
db_manager = DatabaseManager(DB_PATH)

# Set the title of the Streamlit web app
st.title("Song Recognition Pipeline")

# Section for uploading a song
uploaded_file = st.file_uploader("Upload a song", type=["mp3", "wav"])
if uploaded_file:
    # Create a song record with basic information
    song_data = {
        "song_id": "1",  # Unique ID of the song (placeholder)
        "artist": "Unknown",  # Name of the artist (placeholder)
        "title": "Uploaded Song",  # Title of the song (placeholder)
        "album": "Unknown Album"  # Name of the album (placeholder)
    }
    
    # Generate hashes from the uploaded audio file
    hashes = generate_hashes(uploaded_file)
    
    # Store the song and its hashes in the database
    if db_manager.store_song(song_data, hashes):
        # Success message if the song was stored
        st.success("Song stored in the database.")
    else:
        # Warning if the song already exists
        st.warning("Song already exists.")

# Section for recording audio
if st.button("Record Audio"):
    # Record an audio file with a duration of 5 seconds
    record_audio("recorded.wav", 5)
    # Success message after recording is complete
    st.success("Recording complete.")
