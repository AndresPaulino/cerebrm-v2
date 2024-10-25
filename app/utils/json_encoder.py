# app/utils/json_encoder.py
from datetime import datetime
import json

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def json_serializer(obj):
    return json.dumps(obj, cls=CustomJSONEncoder)