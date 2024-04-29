from dataclasses import dataclass, field

from app.components.lifecycle.models.lifecycle_event_model import LifecycleEventModel
from app.contexts.instance_lifecycle_context import InstanceLifecycleContext
from app.domain.handlers.handler_context import HandlerContext


@dataclass(kw_only=True)
class ScalingGroupLifecycleContext(HandlerContext):
    """Represents the context for handling Scaling Group lifecycle events."""

    # Event that triggered the lifecycle handler
    event: LifecycleEventModel

    # Scaling group may have multiple DNS configurations declared,
    # which themselves may have different readiness and health check configurations.
    # Thus, same instance may be passing readiness and health checks for one DNS configuration,
    # but not for another. This is why it is necessary to track readiness and health checks
    # for each DNS configuration separately.
    instances_contexts: list[InstanceLifecycleContext] = field(init=False, default_factory=list)

    def register_instance_context(self, instance_context: InstanceLifecycleContext):
        """Register an instance context that is part of the current scaling group lifecycle.

        Args:
            instance_context (InstanceLifecycleContext): Instance lifecycle context to be registered
        """
        self.instances_contexts.append(instance_context)

    def __post_init__(self):
        return super().__post_init__()
