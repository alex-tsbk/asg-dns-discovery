from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Self, override

from app.utils import enums
from app.utils.dataclass import DataclassBase


class HealthCheckProtocol(Enum):
    """Describes supported protocols used for health checks on an EC2 instance.

    Raises:
        ValueError: When an unsupported protocol is requested.
    """

    TCP = "TCP"
    HTTP = "HTTP"
    HTTPS = "HTTPS"


@dataclass
class HealthCheckConfig(DataclassBase):
    """Model representing the health check configuration for an instance.

    Raises:
        ValueError: When the health check port is invalid.
        ValueError: When the health check timeout is invalid.
        ValueError: When the health check path is missing for HTTP(S) health checks.
    """

    enabled: bool = field(default=False)
    # The value source of the endpoint to resolve heath check endpoint from.
    # Supported values: ip:private, ip:public, tag:<tag_key>:<tag_value>
    endpoint_source: str = field(default="ip:private")
    path: str = field(default="")
    port: int = field(default=0)
    protocol: HealthCheckProtocol = field(default=HealthCheckProtocol.HTTP)
    # The interval in seconds to check the health of the instance
    timeout_seconds: int = field(default=5)

    @property
    def uid(self):
        """Unique identifier for the health check result"""
        return f"{self.enabled}/{self.endpoint_source}/{self.path}/{self.port}/{self.protocol}/{self.timeout_seconds}"

    def __post_init__(self):
        if self.port < 1 or self.port > 65535:
            raise ValueError(f"Invalid health check port: {self.port}")

        if not self.endpoint_source:
            raise ValueError(f"Invalid health check value source: {self.endpoint_source}")

        if self.timeout_seconds < 1 or self.timeout_seconds > 60:
            raise ValueError(f"Invalid health check timeout: {self.timeout_seconds}")

        if self.enabled and self.protocol in [HealthCheckProtocol.HTTP, HealthCheckProtocol.HTTPS] and not self.path:
            raise ValueError("Health check path is required when HTTP(S) health check is enabled")

    @override
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """
        Create a HealthCheckConfig from a dictionary.
        Example:
        {
            "enabled": "true",
            "endpoint_source": "ip:private",
            "path": "/health",
            "port": 80,
            "protocol": "HTTP",
            "timeout_seconds": 5
        }
        """
        return cls(
            enabled=str(data.get("enabled", False)).lower() == "true",
            endpoint_source=data.get("endpoint_source", "ip:private"),
            path=data.get("path", ""),
            port=int(data.get("port", "")),
            protocol=enums.to_enum(data.get("protocol"), default=HealthCheckProtocol.HTTP),
            timeout_seconds=data.get("timeout_seconds", 5),
        )
