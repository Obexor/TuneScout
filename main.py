from App.app import StreamlitApp
# AWS credentials and DynamoDB table name
aws_access_key_id = 'AKIA5CBDRHXJNKCGQ4WJ'
aws_secret_access_key = '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'
aws_region = 'eu-north-1'
table_name = 'SongsFingerprints'
bucket_name = 'song-storage-bucket'


# Initialize and run the Streamlit app
app = StreamlitApp(aws_access_key_id, aws_secret_access_key, aws_region, table_name, bucket_name)
app.run()