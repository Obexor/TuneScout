from datetime import datetime, date
from tinydb.storages import JSONStorage
from tinydb_serialization import Serializer, SerializationMiddleware

class DateSerializer(Serializer):
    # Serializer for handling Python date objects in TinyDB
    OBJ_CLASS = date  # Specify that this serializer handles the 'date' class

    def encode(self, obj):
        # Convert a date object to an ISO 8601 string format
        return obj.isoformat()

    def decode(self, s):
        # Convert an ISO 8601 string back to a date object
        return datetime.fromisoformat(s).date()

# Create a serialization middleware for TinyDB
serializer = SerializationMiddleware(JSONStorage)

# Register the DateSerializer with a custom tag 'TinyDate'
serializer.register_serializer(DateSerializer(), 'TinyDate')
