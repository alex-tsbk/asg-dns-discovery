from typing import Self


class DebugContext:
    """Singleton class to store debug context information. Accessed only by the decorators of the debug module."""

    _instance = None

    def __init__(self):
        if DebugContext._instance:
            return
        # Initialize instance variables
        self.instance_passing_health_checks: list[str] = []
        DebugContext._instance = self

    def __new__(cls) -> Self:
        if cls._instance:
            return cls._instance
        # Proceed with instantiation
        cls._instance = super().__new__(cls)
        return cls._instance
