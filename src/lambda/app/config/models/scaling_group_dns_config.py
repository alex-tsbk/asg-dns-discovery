from dataclasses import field
from enum import Enum

from app.config.models.dns_record_config import DnsRecordConfig
from app.config.models.health_check_config import HealthCheckConfig
from app.utils.dataclass import DataclassBase


class DnsRecordMappingMode(Enum):
    """Enum representing the DNS record mapping modes"""

    # MULTIVALUE: Multiple records are created for the same record name.
    #   Example: domain.com resolves to multiple IP addresses
    MULTIVALUE = "MULTIVALUE"
    # SINGLE: Single record is created for the same record name.
    #   Example: domain.com resolves to a single IP address
    SINGLE = "SINGLE"

    @staticmethod
    def from_str(label: str):
        """Returns the DNS record mapping mode from the label"""
        if not hasattr(DnsRecordMappingMode, label.upper()):
            raise NotImplementedError(f"Unsupported mode: {label}")
        return DnsRecordMappingMode[label.upper()]


class ScalingGroupDnsConfigItem(DataclassBase):
    """Model representing the Scaling Group <--> DNS configuration"""

    # Name of the Scaling Group
    scaling_group_name: str
    # Specifies what to use as a value source for DNS record
    value_source: str = field(default="ip:private")
    # Specifies mode of how DNS records should be mapped
    mode: DnsRecordMappingMode = field(default=DnsRecordMappingMode.MULTIVALUE)
    # DNS configuration
    dns_config: DnsRecordConfig = field(default_factory=DnsRecordConfig)
    # Health check configuration
    health_check_config: HealthCheckConfig = field(default_factory=HealthCheckConfig)

    def __post_init__(self):
        if not self.scaling_group_name:
            raise ValueError("ASG name is required")

        RECORDS_SUPPORTING_MULTIVALUE = [
            "A",
            "AAAA",
            "MX",
            "TXT",
            "PTR",
            "SRV",
            "SPF",
            "NAPTR",
            "CAA",
        ]

        if (
            self.mode == DnsRecordMappingMode.MULTIVALUE
            and self.dns_config.record_type not in RECORDS_SUPPORTING_MULTIVALUE
        ):
            raise ValueError(
                f"Invalid record type: {self.dns_config.record_type} - for mode {self.mode.value}: only {RECORDS_SUPPORTING_MULTIVALUE} are supported"
            )

    def __str__(self) -> str:
        return f"ASG Config:({self.scaling_group_name}/{self.dns_config.dns_zone_id}/{self.dns_config.record_name}/{self.dns_config.record_type})"

    def __hash__(self) -> int:
        return hash(str(self))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ScalingGroupDnsConfigItem):
            return False
        return str(self) == str(other)

    @property
    def lock_key(self) -> str:
        """Builds lock key from ASG DNS config object.
        Used to prevent concurrent processing of lifecycle actions for the same resource.

        Args:
            event (LifecycleEventModel): Original event object received from SNS
            asg_dns_config (AsgDnsConfigItem): ASG DNS configuration

        Returns:
            str: Lock key composed of ASG name, hosted zone id, record name and record type
        """
        # Format: {asg_name}-{hosted_zone_id}-{record_name}-{record_type}
        key = f"{self.scaling_group_name}-{self.dns_zone_id}-{self.record_name}-{self.record_type}"
        return key

    @staticmethod
    def from_dict(item: dict):
        kwargs = {
            "scaling_group_name": item.get("scaling_group_name"),
            "value_source": item.get("value_source", "ip:private").lower(),
            "mode": DnsRecordMappingMode.from_str(item.get("mode", "MULTIVALUE")),
            "dns_config": DnsRecordConfig.from_dict(item.get("dns_config", {})),
            "health_check_config": HealthCheckConfig.from_dict(item.get("health_check_config", {})),
        }
        return ScalingGroupDnsConfigItem(**kwargs)


class ScalingGroupDnsConfig(DataclassBase):
    config_items: list[ScalingGroupDnsConfigItem] = field(default_factory=list)

    def for_scaling_group(self, name: str) -> list[ScalingGroupDnsConfigItem]:
        """Resolves Scaling Group DNS configurations by Scaling Group name

        Args:
            name (str): AutoScalingGroup name

        Returns:
            list[AsgDnsConfigItem]: List of Scaling Group DNS configurations items
        """
        items = [item for item in self.config_items if item.scaling_group_name == name]
        return items
