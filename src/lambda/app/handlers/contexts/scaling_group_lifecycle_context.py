from dataclasses import dataclass, field

from app.components.healthcheck.models.health_check_result_model import HealthCheckResultModel
from app.components.lifecycle.models.lifecycle_event_model import LifecycleEventModel
from app.components.readiness.models.readiness_result_model import ReadinessResultModel
from app.config.models.health_check_config import HealthCheckConfig
from app.config.models.readiness_config import ReadinessConfig
from app.config.models.scaling_group_dns_config import ScalingGroupConfiguration
from app.handlers.contexts.instance_lifecycle_context import InstanceLifecycleContext
from app.handlers.handler_context import HandlerContext
from app.handlers.handler_interface import HandlerInterface
from app.utils.dataclass import DataclassBase


@dataclass
class ScalingGroupLifecycleContext(HandlerContext):
    """Represents the context for handling Scaling Group lifecycle events."""

    # Event that triggered the lifecycle handler
    event: LifecycleEventModel
    # Instance context handler pipeline
    instance_context_handler: HandlerInterface
    # Scaling group may have multiple DNS configurations declared,
    # which themselves may have different readiness and health check configurations.
    instances_contexts: list[InstanceLifecycleContext] = field(default_factory=list)

    def register_instance_context(self, instance_context: InstanceLifecycleContext):
        """Register an instance context that is part of the current scaling group lifecycle.

        Args:
            instance_context (InstanceLifecycleContext): Instance lifecycle context to be registered

        Returns:
            LifecycleContext: self
        """
        self.instances_contexts.append(instance_context)
        self.instance_context_handler.handle(instance_context)
        return self
