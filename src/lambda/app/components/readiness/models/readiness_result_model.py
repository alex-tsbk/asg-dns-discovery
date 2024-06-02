from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Optional

from app.utils.dataclass import DataclassBase


@dataclass
class ReadinessResultModel(DataclassBase):
    """Model representing the readiness result"""

    # Whether the instance is ready to serve traffic
    ready: bool = field(default=False)
    # Hash of the readiness configuration used
    readiness_config_hash: str = field(default="")
    # Instance ID
    instance_id: str = field(default="")
    # Timestamp when the readiness check was performed. Optional.
    timestamp: Optional[datetime] = field(default=None)
    # Time taken to perform the readiness check
    time_taken_ms: float = field(default=0)

    def __bool__(self):
        return self.ready

    def __str__(self) -> str:
        return f"ReadinessResultModel({self.ready}, cfg:{self.readiness_config_hash}, instance_id:{self.instance_id}, time_s:{self.time_taken_ms})"

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(UTC)
