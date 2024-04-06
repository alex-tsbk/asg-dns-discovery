from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Optional

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
    readiness_config: Optional[ReadinessConfig] = field(default=None)
    # Timestamp when the readiness check was performed
    timestamp: Optional[datetime] = field(default=None)

    def __bool__(self):
        return self.ready

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(UTC)

    def with_ready(self, ready: bool = True):
        """Sets the readiness status to given value. Defaults to True."""
        self.ready = ready
        return self

    def with_instance_id(self, instance_id: str):
        """Sets the instance ID"""
        self.instance_id = instance_id
        return self

    def with_scaling_group_name(self, scaling_group_name: str):
        """Sets the scaling group name"""
        self.scaling_group_name = scaling_group_name
        return self
