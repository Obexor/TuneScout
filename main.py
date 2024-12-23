from pipeline.audio_processing import record_audio
from pipeline.hashing import generate_hashes
from pipeline.database import DatabaseManager
from botocore.exceptions import ClientError
import streamlit as st

# AWS credentials and DynamoDB table name
aws_access_key_id = 'AKIA5CBDRHXJNKCGQ4WJ'
aws_secret_access_key = '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'
region_name = 'eu-north-1'
table_name = 'SongsFingerprints'

# Initialize the database manager with the specified AWS credentials and table name
db_manager = DatabaseManager(aws_access_key_id, aws_secret_access_key, region_name, table_name)

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
    hashes = generate_hashes(uploaded_file,db_manager.current_song_id + 1, song_data["artist"], song_data["title"], song_data["album"])

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


# Initialize the database manager with the specified AWS credentials and table name
db_manager = DatabaseManager(aws_access_key_id, aws_secret_access_key, region_name, table_name)

# Streamlit UI
st.title("DynamoDB Song Fingerprint Manager")

# Function to add a song fingerprint
def add_fingerprint(song_id, fingerprint, metadata):
    try:
        item = {
            "SongID": song_id,
            "fingerprint": fingerprint,
            "metadata": metadata,
        }
        db_manager.store_song(item, [])
        return "Song fingerprint added successfully!"
    except ClientError as e:
        return f"Failed to add fingerprint: {e}"

# Function to retrieve a song fingerprint
def get_fingerprint(song_id):
    try:
        result = db_manager.fetch_item({"SongID": song_id})
        if result:
            return result
        else:
            return "No record found for the given SongID."
    except ClientError as e:
        return f"Failed to retrieve fingerprint: {e}"

# Function to list all records
def list_all_records():
    try:
        response = db_manager.db.dynamodb_resource.Table(table_name).scan()
        return response.get("Items", [])
    except ClientError as e:
        return f"Failed to list records: {e}"

def compare_song(hashes):
    # Search for a song by matching hashes in the DynamoDB table
    for hash_item in hashes:
        # Look for a matching hash in the DynamoDB table
        result = db_manager.find_song_by_hashes([hash_item])
        if result:
            # If a matching hash is found, return the associated song metadata
            return result
    return None  # Return None if no match is found

# Retrieve a fingerprint
st.header("Retrieve a Song Fingerprint")
retrieve_song_id = st.text_input("Enter SongID to Retrieve:")
if st.button("Retrieve Fingerprint"):
    result = get_fingerprint(retrieve_song_id)
    st.json(result)

# List all records
st.header("All Records in the Table")
if st.button("List All Records"):
    records = list_all_records()
    st.write(records)

# Section for comparing an uploaded song
st.header("Compare Uploaded Song")
uploaded_compare_file = st.file_uploader("Upload a song to compare", type=["mp3", "wav"])
if uploaded_compare_file:
    # Generate hashes from the uploaded audio file
    compare_hashes = generate_hashes(uploaded_compare_file, db_manager.current_song_id + 1, "", "", "")

    # Compare the song hashes to the database
    match = compare_song(compare_hashes)

    if match:
        st.success("Match found in the database!")
        st.json(match)
    else:
        st.warning("No match found in the database.")

# Section for comparing a recorded song
st.header("Compare Recorded Song")
if st.button("Record and Compare Audio"):
    # Record an audio file with a duration of 5 seconds
    record_audio("recorded_compare.wav", 5)

    # Generate hashes from the recorded audio file
    with open("recorded_compare.wav", "rb") as recorded_file:
        compare_hashes = generate_hashes(recorded_file, db_manager.current_song_id + 1, "", "", "")

    # Compare the song hashes to the database
    match = compare_song(compare_hashes)

    if match:
        st.success("Match found in the database!")
        st.json(match)
    else:
        st.warning("No match found in the database.")
