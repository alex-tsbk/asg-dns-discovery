from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Self, override

from app.config.models.dns_record_config import DnsRecordConfig
from app.config.models.health_check_config import HealthCheckConfig
from app.config.models.readiness_config import ReadinessConfig
from app.utils.dataclass import DataclassBase


class ScalingGroupProceedMode(Enum):
    """Describes the proceed mode for the Scaling Group when ASG has multiple DNS configurations"""

    # When ASG has multiple DNS configurations, proceed with applying changes only if all other configurations
    # for the same ASG are considered 'ready' and 'healthy'.
    ALL_OPERATIONAL = "ALL_OPERATIONAL"
    # When ASG has multiple DNS configurations, proceed with applying changes if current configuration
    # is considered 'ready' and 'healthy'.
    SELF_OPERATIONAL = "SELF_OPERATIONAL"
    # When ASG has multiple DNS configurations, proceed with applying changes if at least 50% of configurations
    # for the same ASG are considered 'ready' and 'healthy'. If there are 2 configurations, at least 1 configuration
    # should be considered 'ready' and 'healthy' (50%).
    HALF_OPERATIONAL = "HALF_OPERATIONAL"


@dataclass
class ScalingGroupConfiguration(DataclassBase):
    """Model representing the Scaling Group configuration"""

    # Name of the Scaling Group
    scaling_group_name: str
    # DNS configuration
    dns_config: DnsRecordConfig
    # Describes how to proceed with changes for the situations when Scaling Group
    # has multiple DNS configurations
    multiple_config_proceed_mode: ScalingGroupProceedMode = field(default=ScalingGroupProceedMode.ALL_OPERATIONAL)
    # Health check configuration
    health_check_config: Optional[HealthCheckConfig] = field(default=None)
    # Readiness config
    readiness_config: Optional[ReadinessConfig] = field(default=None)

    def __post_init__(self):
        if not self.scaling_group_name:
            raise ValueError("ASG name is required")
        # Assign default valid states if not provided
        if not self.scaling_group_valid_states:
            self.scaling_group_valid_states = ["InService"]

    def __str__(self) -> str:
        return f"ASG Config:({self.scaling_group_name}/{self.dns_config.dns_zone_id}/{self.dns_config.record_name}/{self.dns_config.record_type})"

    def __hash__(self) -> int:
        return hash(str(self))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ScalingGroupConfiguration):
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
        key = f"{self.scaling_group_name}-{self.dns_config.dns_zone_id}-{self.dns_config.record_name}-{self.dns_config.record_type}"
        return key

    @override
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        kwargs: dict[str, Any] = {
            "scaling_group_name": data.get("scaling_group_name"),
            "dns_config": DnsRecordConfig.from_dict(data.get("dns_config", {})),
        }
        # Optional fields
        if "multiple_config_proceed_mode" in data:
            kwargs["multiple_config_proceed_mode"] = ScalingGroupProceedMode(
                str(data["multiple_config_proceed_mode"]).upper()
            )
        # Only create health check config if it's present in the config
        health_check_config = data.get("health_check_config", {})
        if health_check_config:
            kwargs["health_check_config"] = HealthCheckConfig.from_dict(health_check_config)
        # Only create readiness config if it's present in the config
        readiness_config = data.get("readiness_config", {})
        if readiness_config:
            kwargs["readiness_config"] = ReadinessConfig.from_dict(readiness_config)
        # Initialize the config
        return cls(**kwargs)


@dataclass
class ScalingGroupConfigurations(DataclassBase):
    config_items: list[ScalingGroupConfiguration] = field(default_factory=list)

    def for_scaling_group(self, name: str) -> list[ScalingGroupConfiguration]:
        """Resolves Scaling Group DNS configurations by Scaling Group name

        Args:
            name (str): AutoScalingGroup name

        Returns:
            list[AsgDnsConfigItem]: List of Scaling Group DNS configurations items
        """
        items = [item for item in self.config_items if item.scaling_group_name == name]
        return items
