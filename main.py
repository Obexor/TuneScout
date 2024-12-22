from pipeline.audio_processing import record_audio
from pipeline.hashing import generate_hashes
from pipeline.database import DatabaseManager
from pipeline.config import DB_PATH
import streamlit as st

db_manager = DatabaseManager(DB_PATH)

st.title("Song Recognition Pipeline")

# Upload a song
uploaded_file = st.file_uploader("Upload a song", type=["mp3", "wav"])
if uploaded_file:
    song_data = {
        "song_id": "1",
        "artist": "Unknown",
        "title": "Uploaded Song",
        "album": "Unknown Album"
    }
    hashes = generate_hashes(uploaded_file)
    if db_manager.store_song(song_data, hashes):
        st.success("Song stored in the database.")
    else:
        st.warning("Song already exists.")

# Record audio
if st.button("Record Audio"):
    record_audio("recorded.wav", 5)
    st.success("Recording complete.")

