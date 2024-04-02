from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.config.models.readiness_config import ReadinessConfig
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
    # Readiness configuration
    readiness_config: ReadinessConfig = field(default=None)
    # Timestamp when the readiness check was performed
    timestamp: datetime = field(default=None)

    def __bool__(self):
        return self.ready

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(UTC)
