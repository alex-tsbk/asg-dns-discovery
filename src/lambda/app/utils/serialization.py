import json
from typing import Any


def to_json(o: Any):
    """Returns JSON representation of a given object"""

    def default_serializer(obj: Any):
        if isinstance(obj, bytes) or hasattr(obj, "value") and isinstance(obj.value, bytes):
            return "BINARY_DATA"
        return str(obj)

    return json.dumps(o, default=default_serializer)
