from dataclasses import dataclass, field

from app.utils.dataclass import DataclassBase

from .instance_model import InstanceModel


@dataclass
class ScalingGroupModel(DataclassBase):
    """Model containing information about the scaling group."""

    # Scaling Group Name
    scaling_group_name: str
    # Instances in the scaling group
    instances: list[InstanceModel] = field(default_factory=list)
