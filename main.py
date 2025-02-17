from App.app import StreamlitApp
from dynaconf import settings

# Load the configuration settings
aws_access_key = os.getenv(AWS_ACCESS_KEY_ID)
aws_secret_key = os.getenv(AWS_SECRET_ACCESS_KEY)
aws_region = os.getenv(AWS_REGION)
table_name_fingerprints = os.getenv(AWS_TABLE_NAME_SONGDATA)
table_name_data = os.getenv(AWS_TABLE_NAME_HASHES)
bucket_name = os.getenv(AWS_BUCKET_NAME)
user_table_name = os.getenv(AWS_USER_TABLE_NAME)

# Initialize and run the Streamlit app
app = StreamlitApp(aws_access_key, aws_secret_key, aws_region, table_name_fingerprints, table_name_data, bucket_name, user_table_name)
app.run()

