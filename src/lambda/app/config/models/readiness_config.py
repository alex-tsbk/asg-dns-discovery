from dataclasses import dataclass, field
from typing import Any, override, Self

from app.utils.dataclass import DataclassBase


@dataclass
class ReadinessConfig(DataclassBase):
    # When set to true, the readiness check is enabled
    enabled: bool = field(default=False)
    # The interval in seconds to check the readiness of the instance
    interval_seconds: int = field(default=5)
    # The timeout in seconds to check the readiness of the instance
    timeout_seconds: int = field(default=60)
    # The tag key to check for readiness
    tag_key: str = field(default="app:readiness:status")
    # The tag value to check for readiness
    tag_value: str = field(default="ready")

    @property
    def uid(self):
        """Unique identifier for the readiness configuration"""
        return f"{self.enabled}/{self.interval_seconds}/{self.timeout_seconds}/{self.tag_key}/{self.tag_value}"

    @override
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """
        Converts dictionary to ReadinessConfig object

        Example:
        {
            "enabled": "<enabled>",
            "interval_seconds": "<interval>",
            "timeout_seconds": "<timeout>",
            "tag_key": "<tag_key>",
            "tag_value": "<tag_value>"
        }
        """
        return cls(**data)
