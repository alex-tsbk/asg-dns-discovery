from dataclasses import dataclass, field

from app.utils import strings
from app.utils.dataclass import DataclassBase


@dataclass
class InstanceMetadataModel(DataclassBase):
    public_ip_v4: str = field(default="")
    private_ip_v4: str = field(default="")
    public_ip_v6: str = field(default="")
    private_ip_v6: str = field(default="")
    public_dns: str = field(default="")
    private_dns: str = field(default="")


@dataclass
class InstanceTagModel(DataclassBase):
    """Model containing information about the tag entry of the instance."""

    key: str
    value: str


@dataclass
class InstanceModel(DataclassBase):
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
    metadata: InstanceMetadataModel = field(default_factory=InstanceMetadataModel)
    # Instance tags
    tags: list[InstanceTagModel] = field(default_factory=list)

    def get_tag_value(self, tag_name: str, case_sensitive: bool = True) -> str:
        """Get tag value by tag name.

        Args:
            tag_name (str): The name of the tag.
            case_sensitive (bool): Whether to perform case-sensitive search for tag name. Defaults to True.

        Returns:
            str: The value of the tag.
        """

        def comparator(t: InstanceTagModel) -> bool:
            return t.key == tag_name if case_sensitive else strings.alike(t.key, tag_name)

        tag = next(filter(comparator, self.tags), None)

        return tag.value if tag else str()
