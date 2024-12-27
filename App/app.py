import streamlit as st
from pipeline.database import DatabaseManager
from pipeline.audio_processing import record_audio
from pipeline.hashing import generate_hashes
from Databank.Amazon_S3 import S3Manager
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

class StreamlitApp:
    def __init__(self, aws_access_key_id, aws_secret_access_key, region_name, table_name, bucket_name):
        try:
            self.db_manager = DatabaseManager(aws_access_key_id, aws_secret_access_key, region_name, table_name)
            self.s3_manager = S3Manager(aws_access_key_id, aws_secret_access_key, region_name, bucket_name)
            self.table_name = table_name
        except (NoCredentialsError, PartialCredentialsError) as e:
            st.error(f"Failed to initialize DatabaseManager or S3Manager: {e}")

    def add_fingerprint(self, song_id, fingerprint, metadata):
        try:
            item = {
                "SongID": song_id,
                "fingerprint": fingerprint,
                "metadata": metadata,
            }
            self.db_manager.store_song(item, [])
            return "Song fingerprint added successfully!"
        except ClientError as e:
            return f"Failed to add fingerprint: {e.response['Error']['Message']}"

    def get_fingerprint(self, song_id):
        try:
            result = self.db_manager.fetch_item({"SongID": song_id})
            if result:
                return result
            else:
                return "No record found for the given SongID."
        except ClientError as e:
            return f"Failed to retrieve fingerprint: {e.response['Error']['Message']}"

    def list_all_records(self):
        try:
            response = self.db_manager.db.dynamodb_resource.Table(self.table_name).scan()
            return response.get("Items", [])
        except ClientError as e:
            print(f"Failed to list records: {e.response['Error']['Message']}")
            return []

    def compare_song(self, hashes):
        try:
            for hash_item in hashes:
                result = self.db_manager.find_song_by_hashes([hash_item])
                if result:
                    return result
            return None
        except ClientError as e:
            st.error(f"Failed to compare song: {e.response['Error']['Message']}")
            return None

    def run(self):
        st.title("Song Recognition Pipeline")

        st.header("Upload a Song")
        uploaded_file = st.file_uploader("Upload a song", type=["mp3", "wav"])
        if uploaded_file:
            try:
                song_data = {
                    "artist": "Unknown",
                    "title": "Uploaded Song",
                    "album": "Unknown Album"
                }
                song_id = self.db_manager.get_latest_song_id() + 1
                fingerprints = generate_hashes(uploaded_file, song_id, song_data["artist"], song_data["title"], song_data["album"])

                if fingerprints:  # Proceed only if fingerprint generation was successful
                    # Store fingerprints and metadata in DynamoDB
                    if self.db_manager.store_song(song_data, fingerprints):
                        st.success("Song stored in the database.")
                        self.s3_manager.upload_file(uploaded_file.name, f"songs/{uploaded_file.name}")
                        st.success("Song uploaded to S3.")
                    else:
                        st.warning("Song already exists.")
                else:
                    st.error("Failed to generate fingerprints.")
            except Exception as e:
                st.error(f"Failed to process uploaded song: {e}")

        st.header("All Songs and Fingerprints")
        if st.button("List All Songs"):
            try:
                records = self.list_all_records()
                if records:
                    st.write(records)
                else:
                    st.warning("No records found.")
            except Exception as e:
                st.error(f"Failed to fetch records: {e}")

        st.header("All Records in the Table")
        if st.button("List All Records"):
            try:
                records = self.list_all_records()
                st.write(records)
            except Exception as e:
                st.error(f"Failed to list records: {e}")

        st.header("Compare Uploaded Song")
        uploaded_compare_file = st.file_uploader("Upload a song to compare", type=["mp3", "wav"])
        if uploaded_compare_file:
            try:
                compare_hashes = generate_hashes(uploaded_compare_file, self.db_manager.current_song_id + 1, "", "", "")
                match = self.compare_song(compare_hashes)
                if match:
                    st.success("Match found in the database!")
                    st.json(match)
                else:
                    st.warning("No match found in the database.")
            except Exception as e:
                st.error(f"Failed to compare uploaded song: {e}")

        st.header("Compare Recorded Song")
        if st.button("Record and Compare Audio"):
            try:
                record_audio("recorded_compare.wav", 5)
                with open("recorded_compare.wav", "rb") as recorded_file:
                    compare_hashes = generate_hashes(recorded_file, self.db_manager.current_song_id + 1, "", "", "")
                match = self.compare_song(compare_hashes)
                if match:
                    st.success("Match found in the database!")
                    st.json(match)
                else:
                    st.warning("No match found in the database.")
            except Exception as e:
                st.error(f"Failed to record and compare audio: {e}")