from dataclasses import dataclass, field

from app.utils.dataclass import DataclassBase

from .instance_entity import Instance


@dataclass
class ScalingGroup(DataclassBase):
    """Model containing information about the scaling group."""

    # Scaling Group Name
    scaling_group_name: str
    # Instances in the scaling group
    instances: list[Instance] = field(default_factory=list)
