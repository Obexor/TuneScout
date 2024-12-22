import boto3
from Databank.Amazon_DynamoDB import AmazonDBConnectivity as ADC

class DatabaseManager:
    def __init__(self, aws_access_key_id, aws_secret_access_key, region_name, table_name):
        self.db = ADC(aws_access_key_id, aws_secret_access_key, region_name)
        self.table_name = table_name
        self.current_song_id = 0  # Initialize the current song ID

    def store_song(self, song_data, hashes):
        # Increment the song ID for each new song
        self.current_song_id += 1
        song_data["SongID"] = str(self.current_song_id)

        # Store the song metadata
        self.db.insert_item(self.table_name, song_data)

        # Store the hashes with the updated song ID
        for hash_item in hashes:
            hash_item["SongID"] = song_data["SongID"]
            self.db.insert_item(self.table_name, hash_item)

        return True

    def store_hashes(self, hashes):
        # Insert multiple hashes into the DynamoDB table
        for hash_item in hashes:
            self.db.insert_item(self.table_name, hash_item)

    def find_song_by_hashes(self, hashes):
        # Search for a song by matching hashes in the DynamoDB table
        for hash_item in hashes:
            # Look for a matching hash in the DynamoDB table
            result = self.db.fetch_item(self.table_name, {"hash": hash_item})
            if result:
                # If a matching hash is found, return the associated song_id
                return result.get("song_id", None)
        return None  # Return None if no match is found

    def fetch_item(self, key):
        # Fetch an item from the DynamoDB table
        return self.db.fetch_item(self.table_name, key)