import boto3
import bcrypt
from botocore.exceptions import ClientError

class UserManager:
    def __init__(self, aws_access_key_id, aws_secret_access_key, region_name, table_name):
        """
        Initialize the UserManager with the necessary DynamoDB table.

        :param table_name: Name of the DynamoDB table.
        :param region_name: AWS region where the table is located (default is 'us-east-1').
        """
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
        self.table_name = table_name
        self.table = self.dynamodb_resource.Table(table_name)

    @staticmethod
    def hash_password(password):
        """
        Hash a plain text password using bcrypt.

        :param password: The plain text password.
        :return: A hashed password (bytes).
        """
        salt = bcrypt.gensalt()  # Generate a salt to hash the password.
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed_password.decode('utf-8')  # Decode to store as a string in DynamoDB.

    @staticmethod
    def verify_password(plain_password, hashed_password):
        """
        Verify a plain text password against a hashed password.

        :param plain_password: The plain text password to verify.
        :param hashed_password: The hashed password to compare against.
        :return: True if the password matches, else False.
        """
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

    def create_user(self, user_id, password, additional_data=None):
        """
        Create a new user in the DynamoDB table.

        :param user_id: Unique username for the user.
        :param password: Plain text password for the user.
        :param additional_data: Dictionary containing any additional user details.
        :return: Response from DynamoDB.
        """
        try:
            if additional_data is None:
                additional_data = {}

            hashed_password = self.hash_password(password)

            user_data = {
                "UserID": user_id,
                "password": hashed_password,  # Hashed password
            }
            user_data.update(additional_data)  # Add any additional data if provided.

            if not self.table:
                raise ValueError("DynamoDB table is not initialized.")
            response = self.table.put_item(Item=user_data)
            return response
        except ClientError as e:
            print(f"Error creating user: {e.response['Error']['Message']}")
            return None

    def get_user(self, user_id):
        """
        Retrieve user information by user_id.

        :param user_id: Unique ID for the user.
        :return: The user's data if found; otherwise, None.
        """
        try:
            response = self.table.get_item(Key={"UserID": user_id})
            if "Item" in response:
                user_data = response["Item"]
                # Avoid returning the hashed password for security reasons.
                user_data.pop("password", None)
                return user_data
            else:
                print(f"User with ID {user_id} not found.")
                return None
        except ClientError as e:
            print(f"Error retrieving user: {e.response['Error']['Message']}")
            return None

    def authenticate_user(self, user_id, password):
        """
        Authenticate a user by verifying their user_id (used as username) and password.

        :param user_id: User ID (used as username) of the user.
        :param password: Plain text password to verify.
        :return: True if authenticated, False otherwise.
        """
        try:
            # Retrieve user data based on the user_id (primary key).
            response = self.table.get_item(Key={"UserID": user_id})
            if "Item" in response:
                user = response["Item"]
                hashed_password = user["password"]

                # Verify the password
                if self.verify_password(password, hashed_password):
                    return True
            return False  # Authentication failed
        except ClientError as e:
            print(f"Error authenticating user: {e.response['Error']['Message']}")
            return False

    def update_user(self, user_id, updates):
        """
        Update user information in DynamoDB.

        :param user_id: Unique ID of the user to update.
        :param updates: A dictionary of attributes to update and their new values.
        :return: Response from DynamoDB if successful; otherwise, None.
        """
        try:
            if "password" in updates:
                updates["password"] = self.hash_password(updates["password"])  # Re-hash the new password.

            update_expression = "SET " + ", ".join(f"#{k} = :{k}" for k in updates.keys())
            expression_attribute_names = {f"#{k}": k for k in updates.keys()}
            expression_attribute_values = {f":{k}": v for k, v in updates.items()}

            response = self.table.update_item(
                Key={"UserID": user_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues="UPDATED_NEW"
            )
            return response
        except ClientError as e:
            print(f"Error updating user: {e.response['Error']['Message']}")
            return None

    def delete_user(self, user_id):
        """
        Delete a user from the DynamoDB table.

        :param user_id: Unique ID for the user to delete.
        :return: Response from DynamoDB if successful; otherwise, None.
        """
        try:
            response = self.table.delete_item(Key={"UserID": user_id})
            return response
        except ClientError as e:
            print(f"Error deleting user: {e.response['Error']['Message']}")
            return None

    def get_user_password(self, user_id):
        """
        Retrieve the hashed password of a user by user_id (used as username).

        :param user_id: User ID (used as the username).
        :return: The user's hashed password if found; otherwise, None.
        """
        try:
            # Directly query for the user based on their primary key (UserID).
            response = self.table.get_item(Key={"UserID": user_id})
            if "Item" in response:
                return response["Item"].get("password")  # Return hashed password if it exists.
            return None  # User not found or password missing.
        except ClientError as e:
            print(f"Error retrieving password: {e.response['Error']['Message']}")
            return None