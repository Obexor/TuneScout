import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError

class S3Manager:
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

    def get_presigned_url(self, key, expiration=3600):
        """
        Generate a pre-signed URL for accessing the object.
        :param key: The key of the object in the S3 bucket (e.g., "songs/song.mp3").
        :param expiration: The time in seconds for which the URL remains valid.
        :return: Pre-signed URL string or None if there is an error.
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            print(f"Failed to generate pre-signed URL: {str(e)}")
            return None