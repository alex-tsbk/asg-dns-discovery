from dataclasses import dataclass, field

from app.components.lifecycle.models.lifecycle_event_model import LifecycleEventModel
from app.config.models.scaling_group_config import ScalingGroupConfiguration
from app.domain.entities.instance import Instance
from app.domain.handlers.handler_context import HandlerContext
from app.workflows.instance_lifecycle.instance_lifecycle_context import InstanceLifecycleContext
from app.workflows.scaling_group_lifecycle.models.sgl_dns_change_model import ScalingGroupLifecycleDnsChangeModel


@dataclass(kw_only=True)
class ScalingGroupLifecycleContext(HandlerContext):
    """Represents the context for handling Scaling Group lifecycle events."""

    # Event that triggered the lifecycle handler
    event: LifecycleEventModel

    # Instance Metadata
    instance_metadata: Instance | None = field(default=None)

    # Scaling group configurations that are part of the current lifecycle
    scaling_group_configs: list[ScalingGroupConfiguration] = field(init=False, default_factory=list)

    # DNS change request accumulated during the lifecycle context
    dns_change_requests: list[ScalingGroupLifecycleDnsChangeModel] = field(init=False, default_factory=list)

    # Scaling group may have multiple configurations declared,
    # which themselves may have different readiness and health check configurations.
    # Thus, same instance may be passing readiness and health checks for one DNS configuration,
    # but not for another. This is why it is necessary to track unique combinations of readiness
    # and health checks for each DNS configuration separately. This also allows to prevent
    # duplicate processing of the same instance when the readiness and health check configurations are the same.
    instances_contexts: list[InstanceLifecycleContext] = field(init=False, default_factory=list)

    def register_instance_context(self, instance_context: InstanceLifecycleContext):
        """Register an instance context that is part of the current scaling group lifecycle.

        Args:
            instance_context (InstanceLifecycleContext): Instance lifecycle context to be registered
        """
        self.instances_contexts.append(instance_context)

    def __post_init__(self):
        return super().__post_init__()
