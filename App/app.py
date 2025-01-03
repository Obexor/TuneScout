import streamlit as st
from Databank.Amazon_DynamoDB import AmazonDBConnectivity as ADC
from Databank.Amazon_S3 import S3Manager
from pipeline.hashing import generate_hashes
from pipeline.audio_processing import record_audio


class StreamlitApp:
    def __init__(self, aws_access_key_id, aws_secret_access_key, region_name, table_name, bucket_name):
        self.db_manager = ADC(aws_access_key_id, aws_secret_access_key, region_name, table_name)
        self.bucket_name = bucket_name
        self.s3_manager = S3Manager(aws_access_key_id, aws_secret_access_key, region_name, bucket_name)

    def upload_song_with_metadata(self):
        st.header("Upload Song with Metadata")

        # Step 1: Upload File
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
                    "album": album.strip() or "Unknown Album"
                }
                st.info(
                    f"Processing: Title='{song_data['title']}', Artist='{song_data['artist']}', Album='{song_data['album']}'")

                # Step 4: Generate Song ID
                song_id = self.db_manager.get_latest_song_id() + 1

                # Step 5: Generate Fingerprints
                st.info("Generating fingerprints for the song...")
                fingerprints = generate_hashes(
                    uploaded_file,  # Input file
                    song_id,
                    song_data["artist"],
                    song_data["title"],
                    song_data["album"]
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
                    compare_hashes = generate_hashes(compare_file, song_id, "", "", "")
                    match = self.db_manager.find_song_by_hashes(compare_hashes)
                    if match:
                        st.success("Match found!")
                        st.json(match)  # Display matched metadata
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
                    compare_hashes = generate_hashes(recorded_file, self.db_manager.get_latest_song_id() + 1, "", "",
                                                     "")
                    match = self.db_manager.find_song_by_hashes(compare_hashes)
                    if match:
                        st.success("Match found!")
                        st.json(match)  # Display matched metadata
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
                songs = self.db_manager.list_all_records()

                if songs:
                    st.info("Songs found in the database:")
                    for index, song in enumerate(songs):
                        title = song.get('title', 'Unknown Title')
                        artist = song.get('artist', 'Unknown Artist')

                        # Display the song metadata
                        st.write(f"Title: {title}, Artist: {artist}")

                        # Add a button to stream each song
                        if st.button(f"Stream {title}",
                                     key=f"stream-{title}-{index}"):  # Add index to ensure uniqueness
                            # Generate pre-signed URL for the song on S3
                            s3_key = f"songs/{title}.mp3"  # Make sure the key matches your S3 structure
                            song_uri = self.s3_manager.get_presigned_url(s3_key)  # Get pre-signed URL

                            if song_uri:
                                st.audio(song_uri)  # Use Streamlit's audio player to play the song
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
                                     "Compare Recorded Song", "Stream Songs"])

        if app_mode == "Upload Song":
            self.upload_song_with_metadata()
        elif app_mode == "Compare Uploaded Song":
            self.compare_uploaded_song()
        elif app_mode == "Compare Recorded Song":
            self.compare_recorded_song()
        elif app_mode == "Stream Songs":
            self.stream_uploaded_song()
