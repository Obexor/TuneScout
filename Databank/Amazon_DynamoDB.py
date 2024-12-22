import boto3
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
        except Exception as e:
            print("Connection failed:", e)

    def insert_item(self, table_name, item):
        table = self.dynamodb_resource.Table(table_name)
        table.put_item(Item=item)
        print("Data inserted successfully.")

    def fetch_item(self, table_name, key):
        table = self.dynamodb_resource.Table(table_name)
        response = table.get_item(Key=key)
        if "Item" in response:
            print("Retrieved data:", response["Item"])

    def update_item(self, table_name, key, update_expression, expression_attribute_names, expression_attribute_values):
        table = self.dynamodb_resource.Table(table_name)
        table.update_item(
            Key=key,
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="UPDATED_NEW"
        )
        print("Data updated successfully.")

    def delete_item(self, table_name, key):
        table = self.dynamodb_resource.Table(table_name)
        table.delete_item(Key=key)
        print("Data deleted successfully.")