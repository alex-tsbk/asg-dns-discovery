from threading import Lock
from typing import Any, Type


class Singleton(type):
    """Thread-safe metaclass for creating singleton classes"""

    _instances: dict[Type[Any], Any] = {}
    _lock = Lock()  # Class-level lock

    def __call__(cls, *args: Any, **kwargs: Any):
        if cls not in cls._instances:
            with cls._lock:  # Acquire lock
                if cls not in cls._instances:  # Double-checked locking
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]
