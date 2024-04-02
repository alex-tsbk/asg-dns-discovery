from dataclasses import dataclass, field
from app.utils.dataclass import DataclassBase


@dataclass
class InstanceDiscoveryMetadataModel(DataclassBase):
    public_ip_v4: str = field(default="")
    private_ip_v4: str = field(default="")
    public_ip_v6: str = field(default="")
    private_ip_v6: str = field(default="")
    public_dns: str = field(default="")
    private_dns: str = field(default="")


@dataclass
class InstanceDiscoveryTagModel(DataclassBase):
    """Model containing information about the tag entry of the instance."""

    key: str
    value: str


@dataclass
class InstanceDiscoveryResultModel(DataclassBase):
    """Model containing information about instance."""

    # Instance id
    instance_id: str
    # Scaling Group Name
    scaling_group_name: str
    # State of the instance (Running, Stopped, etc.)
    instance_state: str = field(default="")
    # Lifecycle state of the instance in Scaling Group (Pending, InService, Standby, etc.)
    lifecycle_state: str = field(default="")
    # Instance launch timestamp (epoch)
    instance_launch_timestamp: int = field(default=0)
    # Instance metadata
    metadata: InstanceDiscoveryMetadataModel = field(default_factory=InstanceDiscoveryMetadataModel)
    # Instance tags
    tags: list[InstanceDiscoveryTagModel] = field(default_factory=list)

    def get_tag_value(self, tag_name: str) -> str:
        """Get tag value by tag name.

        Args:
            tag_name (str): The name of the tag.

        Returns:
            str: The value of the tag.
        """
        tag = next(filter(lambda t: t.key == tag_name, self.tags), None)
        return tag.value if tag else None
