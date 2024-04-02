from dataclasses import dataclass, field

from app.utils.dataclass import DataclassBase


@dataclass
class MetadataResultModel(DataclassBase):
    """Model containing instance metadata resolved values."""

    # Scaling Group Name
    scaling_group_name: str
    # Instance id
    instance_id: str
    # Value resolved
    value: str
    # State of the instance (Running, Stopped, etc.)
    instance_state: str = field(default="")
    # Lifecycle state of the instance (Pending, InService, Standby, etc.)
    sg_lifecycle_state: str = field(default="")
    # Instance launch timestamp (epoch)
    instance_launch_timestamp: int = field(default=0)
    # Source of the value
    source: str = field(default="")
