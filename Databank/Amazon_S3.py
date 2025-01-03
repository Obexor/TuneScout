import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError

class S3Manager:
    """
    Manager class for interacting with an Amazon S3 bucket.

    This class provides methods to upload files to, download files from, and
    generate pre-signed URLs for objects in an S3 bucket. It is initialized
    with AWS credentials and basic configuration details, enabling interaction
    with the specified S3 bucket.

    :ivar s3: Boto3 client used to communicate with Amazon S3.
    :type s3: botocore.client.BaseClient
    :ivar bucket_name: Name of the S3 bucket to manage.
    :type bucket_name: str
    """
    def __init__(self, aws_access_key_id, aws_secret_access_key, region_name, bucket_name):
        try:
            self.s3 = boto3.client(
                's3',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region_name
            )
            self.bucket_name = bucket_name
        except (NoCredentialsError, PartialCredentialsError) as e:
            print(f"Failed to connect to S3: {e}")

    def upload_file(self, file_name, object_name=None):
        try:
            if object_name is None:
                object_name = file_name
            self.s3.upload_file(file_name, self.bucket_name, object_name)
            print(f"File {file_name} uploaded to {self.bucket_name}/{object_name}")
        except ClientError as e:
            print(f"Failed to upload file: {e.response['Error']['Message']}")
        except Exception as e:
            print(f"An error occurred: {e}")

    def download_file(self, object_name, file_name=None):
        try:
            if file_name is None:
                file_name = object_name
            self.s3.download_file(self.bucket_name, object_name, file_name)
            print(f"File {object_name} downloaded from {self.bucket_name} to {file_name}")
        except ClientError as e:
            print(f"Failed to download file: {e.response['Error']['Message']}")
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def get_presigned_url(self, s3_key):
        try:
            # Generate the URL for the object
            response = self.s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
            )
            return response
        except ClientError as e:
            print(f"Failed to generate presigned URL: {e.response['Error']['Message']}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None
