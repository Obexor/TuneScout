import boto3
from botocore.exceptions import BotoCoreError, ClientError

class AmazonDBConnectivity:
    """
    Class for managing connectivity and operations with an Amazon DynamoDB table.

    This class provides methods to perform common operations on a DynamoDB table,
    such as inserting, fetching, updating, and deleting items. It also supports
    custom functionality for managing songs and their associated hashes in a
    DynamoDB table. Users must provide AWS credentials, the region, and the table
    name to establish a connection.

    :ivar dynamodb_client: Low-level DynamoDB client used for certain operations.
    :type dynamodb_client: botocore.client.DynamoDB
    :ivar dynamodb_resource: High-level DynamoDB resource providing table-based operations.
    :type dynamodb_resource: boto3.resources.factory.dynamodb.ServiceResource
    :ivar table_name: Name of the DynamoDB table on which operations are performed.
    :type table_name: str
    :ivar current_song_id: Counter for tracking the latest song ID used in the table.
    :type current_song_id: int
    """
    def __init__(self, aws_access_key_id, aws_secret_access_key, region_name, table_name):
        self.dynamodb_client = boto3.client(
            'dynamodb',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        self.dynamodb_resource = boto3.resource(
            'dynamodb',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        self.table_name = table_name
        self.current_song_id = 0

    def test_connectivity(self):
        try:
            response = self.dynamodb_client.list_tables()
            print("Connection successful. DynamoDB tables:", response['TableNames'])
        except (BotoCoreError, ClientError) as e:
            print("Connection failed:", e)

    def insert_item(self, item):
        try:
            table = self.dynamodb_resource.Table(self.table_name)
            table.put_item(Item=item)
            print("Data inserted successfully.")
        except (BotoCoreError, ClientError) as e:
            print("Failed to insert data:", e)

    def fetch_item(self):
        try:
            table = self.dynamodb_resource.Table(self.table_name)
            response = table.scan()
            items = response.get("Items", [])
            return items
        except (BotoCoreError, ClientError) as e:
            print("Failed to fetch data:", e)
            return []

    def update_item(self, key, update_expression, expression_attribute_names, expression_attribute_values):
        try:
            table = self.dynamodb_resource.Table(self.table_name)
            table.update_item(
                Key=key,
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues="UPDATED_NEW"
            )
            print("Data updated successfully.")
        except (BotoCoreError, ClientError) as e:
            print("Failed to update data:", e)

    def delete_item(self, key):
        try:
            table = self.dynamodb_resource.Table(self.table_name)
            table.delete_item(Key=key)
            print("Data deleted successfully.")
        except (BotoCoreError, ClientError) as e:
            print("Failed to delete data:", e)

    def store_song(self, song_data, hashes):
        try:
            if self.song_exists(hashes):
                return False

            self.current_song_id = self.get_latest_song_id() + 1
            song_data["SongID"] = str(self.current_song_id)

            self.insert_item(song_data)

            for hash_item in hashes:
                hash_item["SongID"] = song_data["SongID"]
                self.insert_item(hash_item)

            return True
        except ClientError as e:
            print(f"Failed to store song: {e.response['Error']['Message']}")
            return False

    def get_latest_song_id(self):
        try:
            response = self.dynamodb_resource.Table(self.table_name).scan()
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
            for hash_item in hashes:
                if "Hash" not in hash_item:
                    print("Hash key missing in hash_item")
                    continue
                result = self.find_song_by_hashes([hash_item])
                if result:
                    return True
            return False
        except ClientError as e:
            print(f"Failed to check if song exists: {e.response['Error']['Message']}")
            return False

    def store_hashes(self, hashes):
        try:
            for hash_item in hashes:
                self.insert_item(hash_item)
        except ClientError as e:
            print(f"Failed to store hashes: {e.response['Error']['Message']}")

    def find_song_by_hashes(self, hashes):
        try:
            for hash_item in hashes:
                result = self.fetch_item()
                if result:
                    for item in result:
                        if item.get("Hash") == hash_item.get("Hash"):
                            # Remove 'offset' and 'Hash' from the item
                            filtered_item = {k: v for k, v in item.items() if k not in ["s3_key", "Hash"]}
                            return filtered_item
            return None
        except ClientError as e:
            print(f"Failed to find song by hashes: {e.response['Error']['Message']}")
            return None

    def list_all_records(self):
        try:
            response = self.dynamodb_resource.Table(self.table_name).scan()
            return response.get("Items", [])
        except Exception as e:
            print(f"Failed to retrieve records: {str(e)}")

    def store_metadata_in_songs_table(self, song_id, song_data):
        """
        Stores song metadata in the SongsFingerprints table.

        :param song_id: Unique Song ID.
        :param song_data: Dictionary containing song metadata (artist, title, album, etc.).
        """
        try:
            table = self.dynamodb_resource.Table('SongsFingerprints')
            song_data["SongID"] = str(song_id)
            table.put_item(Item=song_data)
            print("Metadata stored successfully in SongsFingerprints table.")
        except (BotoCoreError, ClientError) as e:
            print("Failed to store metadata in SongsFingerprints table:", e)

    def store_fingerprints_in_hashes_table(self, song_id, fingerprints):
        """
        Stores song fingerprints in the Hashes table.

        :param song_id: Unique Song ID associated with the fingerprints.
        :param fingerprints: List of dictionaries, each containing a hash and its offset.
        """
        try:

            table = self.dynamodb_resource.Table('Hashes')
            for fingerprint in fingerprints:
                fingerprint_data = {
                    "Hash": fingerprint[0],
                    "Offset": fingerprint[1],
                    "SongID": str(song_id)
                }
                table.put_item(Item=fingerprint_data)
            print("Fingerprints stored successfully in Hashes table.")
        except (BotoCoreError, ClientError) as e:
            print("Failed to store fingerprints in Hashes table:", e)

