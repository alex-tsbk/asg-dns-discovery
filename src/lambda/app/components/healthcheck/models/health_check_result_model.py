from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Optional

from app.utils.dataclass import DataclassBase


@dataclass
class HealthCheckResultModel(DataclassBase):
    """Model representing the result of a health check for an endpoint associate with instance.

    Remarks:
        Most of the properties are optional, these are used primarily for telemetry and observability purposes.
        When something is not healthy, it's important to know why. It's then up to consumer to decide what to do with this information.
        One way is to proceed only with healthy endpoints, ignoring unhealthy.
    """

    # Whether the endpoint is healthy
    healthy: bool
    # Hash of the health check configuration used
    health_check_config_hash: str = field(default="")
    # Instance id
    instance_id: str = field(default="")
    # Protocol used for the health check
    protocol: str = field(default="")
    # Endpoint that was checked
    endpoint: str = field(default="")
    # Status of the health check. Optional.
    status: str = field(default="")
    # Message from the health check. Optional.
    message: str = field(default="")
    # Timestamp when the health check was performed. Optional.
    timestamp: Optional[datetime] = field(default=None)
    # Time taken for instance to become ready. In seconds. Optional.
    time_taken_ms: float = field(default=0)

    def __bool__(self):
        return self.healthy

    def __str__(self) -> str:
        return f"HealthCheckResultModel(protocol:{self.protocol}, endpoint:{self.endpoint}, healthy:{self.healthy}, instance_id:{self.instance_id}, status:{self.status}, msg:{self.message}, time_s:{self.time_taken_ms})"

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(UTC)
