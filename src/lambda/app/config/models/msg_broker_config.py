from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Self, override

from app.utils import enums
from app.utils.dataclass import DataclassBase


class MessageBrokerProvider(Enum):
    """DNS record provider"""

    # Relies on an external message broker provider (SQS)
    EXTERNAL = "EXTERNAL"
    # Relies on an internal message broker provider (in-memory).
    # Do not use in production, as it is not scalable.
    INTERNAL = "INTERNAL"


@dataclass
class MessageBrokerConfig(DataclassBase):
    """Model representing the message broker configuration"""

    # Message broker provider
    provider: MessageBrokerProvider = field(default=MessageBrokerProvider.INTERNAL)
    # Endpoint
    endpoint: str = field(default="")

    def __post_init__(self):
        if self.provider == MessageBrokerProvider.EXTERNAL and not self.endpoint:
            raise ValueError("External message broker requires an endpoint")

    @override
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """
        Converts dictionary to ReadinessConfig object

        Example:
        {
            "provider": "external | internal",
            "endpoint": "<url>",
        }
        """
        return cls(
            provider=enums.to_enum(data.get("provider"), default=MessageBrokerProvider.INTERNAL),
            endpoint=data.get("endpoint", ""),
        )
