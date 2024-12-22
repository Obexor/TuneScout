import boto3


# Initialize a DynamoDB client
def initialize_dynamodb_client(aws_access_key_id, aws_secret_access_key, region_name):
    return boto3.client(
        'dynamodb',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name
    )


# Initialize a DynamoDB resource
def initialize_dynamodb_resource(aws_access_key_id, aws_secret_access_key, region_name):
    return boto3.resource(
        'dynamodb',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name
    )


# Test connectivity by listing tables
def test_connectivity(dynamodb_client):
    try:
        response = dynamodb_client.list_tables()
        print("Connection successful. DynamoDB tables:", response['TableNames'])
    except Exception as e:
        print("Connection failed:", e)


# Insert an item into a DynamoDB table
def insert_item(dynamodb_resource, table_name, item):
    table = dynamodb_resource.Table(table_name)
    table.put_item(Item=item)
    print("Data inserted successfully.")


# Fetch an item from a DynamoDB table
def fetch_item(dynamodb_resource, table_name, key):
    table = dynamodb_resource.Table(table_name)
    response = table.get_item(Key=key)
    if "Item" in response:
        print("Retrieved data:", response["Item"])


# Update an item in a DynamoDB table
def update_item(dynamodb_resource, table_name, key, update_expression, expression_attribute_names,
                expression_attribute_values):
    table = dynamodb_resource.Table(table_name)
    table.update_item(
        Key=key,
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_attribute_names,
        ExpressionAttributeValues=expression_attribute_values,
        ReturnValues="UPDATED_NEW"
    )
    print("Data updated successfully.")


# Delete an item from a DynamoDB table
def delete_item(dynamodb_resource, table_name, key):
    table = dynamodb_resource.Table(table_name)
    table.delete_item(Key=key)
    print("Data deleted successfully.")