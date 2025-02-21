import boto3
import pytest
import os

# Get S3 bucket name from environment variable
BUCKET_NAME = os.getenv("AWS_BUCKET_NAME_TEST")
FILE_NAME = "test.txt"
CONTENT = "Hello, AWS S3!"


@pytest.fixture
def s3_client():
    """Create an S3 client using environment variables."""
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    region = os.getenv("AWS_REGION")

    return boto3.client(
        "s3",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region,
    )

def test_s3_connection(s3_client):
    """Test the connection to S3 by listing the buckets."""
    # List all buckets in S3
    response = s3_client.list_buckets()

    # Check that the response has the 'Buckets' key
    assert 'Buckets' in response, "No buckets found"

    # Print out the names of the S3 buckets
    print("Buckets in S3:")
    for bucket in response['Buckets']:
        print(f"- {bucket['Name']}")

    # Assert that there is at least one bucket (if any)
    assert len(response['Buckets']) >= 0

def test_s3_upload_and_fetch(s3_client):
    """Test uploading and retrieving a file from a real AWS S3 bucket."""
    # Upload file to S3
    s3_client.put_object(Bucket=BUCKET_NAME, Key=FILE_NAME, Body=CONTENT)

    # Fetch the file from S3
    response = s3_client.get_object(Bucket=BUCKET_NAME, Key=FILE_NAME)
    data = response["Body"].read().decode("utf-8")

    # Assert that the data is correct
    assert data == CONTENT
