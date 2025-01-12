from App.app import StreamlitApp
from dynaconf import settings

# Load the configuration settings
aws_access_key = settings.AWS_ACCESS_KEY_ID
aws_secret_key = settings.AWS_SECRET_ACCESS_KEY
aws_region = settings.AWS_REGION
table_name = settings.AWS_TABLE_NAME
bucket_name = settings.AWS_BUCKET_NAME

# Initialize and run the Streamlit app
app = StreamlitApp(aws_access_key, aws_secret_key, aws_region, table_name, bucket_name)
app.run()

