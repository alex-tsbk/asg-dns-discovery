from dataclasses import dataclass, field
from typing import Any, Optional, Self, override

from app.components.lifecycle.models.lifecycle_event_model import LifecycleEventModel, LifecycleTransition


@dataclass(kw_only=True)
class AwsLifecycleEventModel(LifecycleEventModel):
    origin: str  # Describes the origin state of the VM
    destination: str  # Describes the destination state of the VM
    service: str  # Service that triggered the event
    lifecycle_action_token: str  # Token to prevent duplicate processing of lifecycle event
    lifecycle_transition: str  # In AWS:autoscaling:EC2_INSTANCE_TERMINATING
    notification_metadata: Optional[dict[str, Any]] = field(default_factory=dict)  # Notification metadata

    @override
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        origin = data.get("Origin", "")
        destination = data.get("Destination", "")

        return cls(
            # Base class fields
            transition=cls._determine_transition(origin, destination),
            lifecycle_hook_name=data.get("LifecycleHookName", ""),
            scaling_group_name=data.get("AutoScalingGroupName", ""),
            instance_id=data.get("EC2InstanceId", ""),
            # Additional fields
            origin=origin,
            destination=destination,
            service=data.get("Service", ""),
            lifecycle_action_token=data.get("LifecycleActionToken", ""),
            lifecycle_transition=data.get("LifecycleTransition", ""),
            notification_metadata=data.get("NotificationMetadata", None),
        )

    def get_lifecycle_action_args(self) -> dict[str, Any]:
        """Returns arguments required for completion of AWS lifecycle action"""
        return {
            "life_cycle_hook_name": self.lifecycle_hook_name,
            "autoscaling_group_name": self.scaling_group_name,
            "lifecycle_action_token": self.lifecycle_action_token,
            "instance_id": self.instance_id,
        }

    @classmethod
    def _determine_transition(cls, origin: str, destination: str) -> LifecycleTransition:
        """Based on the origin and destination states, determine the lifecycle transition

        Args:
            origin (str): Source state of the EC2 instance (e.g. AutoScalingGroup, EC2, WarmPool)
            destination (str): Destination state of the EC2 instance (e.g. AutoScalingGroup, EC2, WarmPool)

        Returns:
            LifecycleTransition: Lifecycle transition based on the combination of origin and destination states

        Reference:
            https://docs.aws.amazon.com/autoscaling/ec2/userguide/lifecycle-hooks.html
        """
        if origin == "AutoScalingGroup" and destination in ["EC2", "WarmPool"]:
            return LifecycleTransition.DRAINING
        elif origin in ["EC2", "WarmPool"] and destination == "AutoScalingGroup":
            return LifecycleTransition.LAUNCHING
        # If the origin and destination are not related to the lifecycle event
        return LifecycleTransition.UNRELATED

    def __post_init__(self):
        # Ensure mandatory fields are set
        if not self.origin:
            raise ValueError("Origin state is required")
        if not self.destination:
            raise ValueError("Destination state is required")
        if not self.service:
            raise ValueError("Service is required")
        if not self.lifecycle_action_token:
            raise ValueError("Lifecycle action token is required")
        if not self.lifecycle_transition:
            raise ValueError("Lifecycle transition is required")
        # Ensure base class fields are initialized
        return super().__post_init__()
