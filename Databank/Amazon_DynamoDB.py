import boto3

# your_access_key = 'AKIA5CBDRHXJNKCGQ4WJ'
# your_secret_key = '6tM0ELbIx1kdhDhQptoMAaTkCDAriwefAqNEJEnk'
# region = 'eu-north-1'

# Initialize DynamoDB client
dynamodb = boto3.client(   'dynamodb',
            aws_access_key_id='AKIA5CBDRHXJNKCGQ4WJ',
            aws_secret_access_key='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',
            region_name='eu-north-1'
                           )

try:
    # List tables
    response = dynamodb.list_tables()
    print("Connection successful. DynamoDB tables:", response['TableNames'])
except Exception as e:
    print("Connection failed:", e)

# Initialize DynamoDB resource
dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id='AKIA5CBDRHXJNKCGQ4WJ',
            aws_secret_access_key='6tM0ELbIx1kdhDhQptoMAaTkCDAriwefAqNEJEnk',
            region_name='eu-north-1'
                            )
# Access your table
table_name = 'SongsFingerprints'
table = dynamodb.Table(table_name)

# Insert an item
item = {
    "SongID": "12345",
    "fingerprint": "[0.1, 0.2, 0.3, 0.4]",
    "metadata": {
        "title": "Song Title",
        "artist": "Artist Name",
        "album": "Album Name",
        "duration": 180  # Duration in seconds
    }
}

# Insert the item into the table
table.put_item(Item=item)
print("Data inserted successfully.")

# Fetch the item
response = table.get_item(Key={"SongID": "12345"})
if "Item" in response:
    print("Retrieved data:", response["Item"])

# Update the item
table.update_item(
    Key={"SongID": "12345"},
    UpdateExpression="SET metadata.#genre = :genre",
    ExpressionAttributeNames={"#genre": "genre"},
    ExpressionAttributeValues={":genre": "Pop"},
    ReturnValues="UPDATED_NEW"
)
print("Data updated successfully.")

# Delete the item
# table.delete_item(Key={"SongID": "12345"})
# print("Data deleted successfully.")



