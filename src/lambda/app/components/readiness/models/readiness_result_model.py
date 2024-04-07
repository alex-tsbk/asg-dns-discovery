from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Optional

from app.utils.dataclass import DataclassBase


@dataclass
class ReadinessResultModel(DataclassBase):
    """Model representing the readiness result"""

    # Whether the instance is ready to serve traffic
    ready: bool = field(default=False)
    # Instance ID
    instance_id: str = field(default="")
    # Name of the scaling group
    scaling_group_name: str = field(default="")
    timestamp: Optional[datetime] = field(default=None)
    # Time taken to perform the readiness check
    time_taken_ms: float = field(default=0)

    def __bool__(self):
        return self.ready

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(UTC)
