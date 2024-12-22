import boto3
from botocore.exceptions import BotoCoreError, ClientError

class AmazonDBConnectivity:
    def __init__(self, aws_access_key_id, aws_secret_access_key, region_name):
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

    def test_connectivity(self):
        try:
            response = self.dynamodb_client.list_tables()
            print("Connection successful. DynamoDB tables:", response['TableNames'])
        except (BotoCoreError, ClientError) as e:
            print("Connection failed:", e)

    def insert_item(self, table_name, item):
        try:
            table = self.dynamodb_resource.Table(table_name)
            table.put_item(Item=item)
            print("Data inserted successfully.")
        except (BotoCoreError, ClientError) as e:
            print("Failed to insert data:", e)

    def fetch_item(self, table_name, key):
        try:
            table = self.dynamodb_resource.Table(table_name)
            response = table.get_item(Key=key)
            if "Item" in response:
                print("Retrieved data:", response["Item"])
                return response["Item"]
            else:
                print("No data found for the given key.")
                return None
        except (BotoCoreError, ClientError) as e:
            print("Failed to fetch data:", e)
            return None

    def update_item(self, table_name, key, update_expression, expression_attribute_names, expression_attribute_values):
        try:
            table = self.dynamodb_resource.Table(table_name)
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

    def delete_item(self, table_name, key):
        try:
            table = self.dynamodb_resource.Table(table_name)
            table.delete_item(Key=key)
            print("Data deleted successfully.")
        except (BotoCoreError, ClientError) as e:
            print("Failed to delete data:", e)