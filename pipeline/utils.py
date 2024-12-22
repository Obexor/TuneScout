from datetime import datetime, date
from tinydb.storages import JSONStorage
from tinydb_serialization import Serializer, SerializationMiddleware


class DateSerializer(Serializer):
    OBJ_CLASS = date

    def encode(self, obj):
        return obj.isoformat()

    def decode(self, s):
        return datetime.fromisoformat(s).date()


serializer = SerializationMiddleware(JSONStorage)
serializer.register_serializer(DateSerializer(), 'TinyDate')
