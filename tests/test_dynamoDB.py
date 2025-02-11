import boto3
import pytest
import os

# Get DynamoDB table name from environment variable
TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME")


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


def test_dynamodb_insert_and_fetch(dynamodb_resource):
    """Test inserting and retrieving an item from a real DynamoDB table."""
    table = dynamodb_resource.Table(TABLE_NAME)

    # Insert an item
    item = {"user_id": "123", "name": "Alice"}
    table.put_item(Item=item)

    # Fetch the item
    response = table.get_item(Key={"user_id": "123"})
    fetched_item = response.get("Item")

    # Assert that the item was fetched successfully
    assert fetched_item is not None
    assert fetched_item["name"] == "Alice"
