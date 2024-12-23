from Databank.Amazon_DynamoDB import AmazonDBConnectivity as ADC
from botocore.exceptions import ClientError

class DatabaseManager:
    def __init__(self, aws_access_key_id, aws_secret_access_key, region_name, table_name):
        # Initialize the database connection and table name
        self.db = ADC(aws_access_key_id, aws_secret_access_key, region_name)
        self.table_name = table_name
        self.current_song_id = 0  # Initialize the current song ID

    def store_song(self, song_data, hashes):
        try:
            # Check if the song already exists in the database
            if self.song_exists(hashes):
                return False

            # Increment the song ID for each new song
            self.current_song_id = self.get_latest_song_id() + 1
            song_data["SongID"] = str(self.current_song_id)

            # Store the song metadata
            self.db.insert_item(self.table_name, song_data)

            # Store the hashes with the updated song ID
            for hash_item in hashes:
                hash_item["SongID"] = song_data["SongID"]
                self.db.insert_item(self.table_name, hash_item)

            return True
        except ClientError as e:
            print(f"Failed to store song: {e.response['Error']['Message']}")
            return False

    def get_latest_song_id(self):
        try:
            # Fetch all items from the table and find the maximum SongID
            response = self.db.dynamodb_resource.Table(self.table_name).scan()
            items = response.get("Items", [])
            if not items:
                return 0
            max_song_id = max(int(item["SongID"]) for item in items)
            return max_song_id
        except ClientError as e:
            print(f"Failed to get latest song ID: {e.response['Error']['Message']}")
            return 0

    def song_exists(self, hashes):
        try:
        # Check if any of the provided hashes already exist in the database
            for hash_item in hashes:
                if hash not in hash_item:
                    print("Hash key missing in hash_item")
                    continue
                result = self.db.fetch_item(self.table_name, {"Hash": hash_item["Hash"]})
                if result:
                    return True
            return False
        except ClientError as e:
            print(f"Failed to check if song exists: {e.response['Error']['Message']}")
            return False

    def store_hashes(self, hashes):
        try:
            # Insert multiple hashes into the DynamoDB table
            for hash_item in hashes:
                self.db.insert_item(self.table_name, hash_item)
        except ClientError as e:
            print(f"Failed to store hashes: {e.response['Error']['Message']}")

    def find_song_by_hashes(self, hashes):
        try:
            # Search for a song by matching hashes in the DynamoDB table
            for hash_item in hashes:
                # Look for a matching hash in the DynamoDB table
                result = self.db.fetch_item(self.table_name, {"hash": hash_item})
                if result:
                    # If a matching hash is found, return the associated song_id
                    return result.get("song_id", None)
            return None  # Return None if no match is found
        except ClientError as e:
            print(f"Failed to find song by hashes: {e.response['Error']['Message']}")
            return None

    def fetch_item(self, key):
        try:
            # Fetch an item from the DynamoDB table
            return self.db.fetch_item(self.table_name, key)
        except ClientError as e:
            print(f"Failed to fetch item: {e.response['Error']['Message']}")
            return None