import boto3
from Databank.Amazon_DynamoDB import AmazonDBConnectivity as ADC

class DatabaseManager:
    def __init__(self, aws_access_key_id, aws_secret_access_key, region_name, table_name):
        # Initialize the AmazonDBConnectivity instance
        self.db = ADC(aws_access_key_id, aws_secret_access_key, region_name)
        self.table_name = table_name

    def store_song(self, song_data, hashes):
        # Check if the song already exists in the database using its song_id
        existing_song = self.fetch_item({"song_id": song_data['song_id']})
        if not existing_song:
            # If the song does not exist, insert its metadata into the DynamoDB table
            self.db.insert_item(self.table_name, song_data)

            # Store the associated hashes in the DynamoDB table
            self.store_hashes(hashes)
            return True  # Return True to indicate the song was successfully stored
        return False  # Return False if the song already exists

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