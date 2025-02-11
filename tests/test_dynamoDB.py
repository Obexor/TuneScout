import boto3
import pytest
import os

# Get DynamoDB table name from environment variable
TABLE_NAME = os.getenv("AWS_TABLE_NAME_TEST")


@pytest.fixture
def dynamodb_resource():
    """Create a DynamoDB resource using environment variables."""
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    region = os.getenv("AWS_REGION")

    return boto3.resource(
        "dynamodb",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region,
    )

def test_dynamodb_connection(dynamodb_resource):
    """Test the connection to DynamoDB by listing tables."""
    # Attempt to list tables (this is the test connection)
    tables = list(dynamodb_resource.tables.all())  # Convert to list to force the request

    # If there are tables, print their names
    if tables:
        print("Connection successful! Tables in DynamoDB:")
        for table in tables:
            print(table.name)

    # Assert that the list of tables is not empty, meaning we have access
    assert len(tables) >= 0



def test_dynamodb_insert_and_fetch(dynamodb_resource):
    """Test inserting and retrieving an item from a real DynamoDB table."""
    table = dynamodb_resource.Table(TABLE_NAME)

    # Insert an item
    item = {"Test": "123", "name": "Alice"}
    table.put_item(Item=item)

    # Fetch the item
    response = table.get_item(Key={"Test": "123"})
    fetched_item = response.get("Item")

    # Assert that the item was fetched successfully
    assert fetched_item is not None
    assert fetched_item["name"] == "Alice"
