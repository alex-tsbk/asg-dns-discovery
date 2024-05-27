from dataclasses import dataclass, field
from typing import Optional

from app.components.healthcheck.models.health_check_result_model import HealthCheckResultModel
from app.components.readiness.models.readiness_result_model import ReadinessResultModel
from app.config.models.health_check_config import HealthCheckConfig
from app.config.models.readiness_config import ReadinessConfig
from app.config.models.scaling_group_config import ScalingGroupConfiguration
from app.domain.entities.instance import Instance
from app.domain.handlers.handler_context import HandlerContext


@dataclass(kw_only=True)
class InstanceLifecycleContext(HandlerContext):
    """Context represent the lifecycle of a single instance in the scaling group.

    Lifecycle includes the following phases:
    - Instance is discovered in the target environment and metadata is resolved.
    - Instance readiness is checked - ensures the instance has passed 'bootstrap' phase.
    - Instance health is checked - ensures the instance is healthy and not in a degraded state.
    """

    instance_id: str
    # config
    scaling_group_config: ScalingGroupConfiguration
    readiness_config: ReadinessConfig | None
    health_check_config: HealthCheckConfig | None
    # metadata
    instance_model: Instance | None = field(default=None)
    # results
    readiness_result: Optional[ReadinessResultModel] = field(default=None)
    health_check_result: Optional[HealthCheckResultModel] = field(default=None)

    @property
    def readiness_check_passed(self) -> bool:
        """Returns True if the instance has passed the readiness check.
        Readiness check is considered passed if readiness check configuration is not defined or
        if readiness check has been executed and the instance is considered ready.

        Returns:
            bool: True if the instance is considered ready
        """
        return self.readiness_config is None or self.readiness_result.ready

    @property
    def health_check_passed(self) -> bool:
        """Returns True if the instance has passed the health check.
        Health check is considered passed if health check configuration is not defined or
        if health check has been executed and the instance is considered healthy.

        Returns:
            bool: True if the instance is considered healthy
        """
        return self.health_check_result is not None and self.health_check_result.healthy

    @property
    def operational(self) -> bool:
        """Returns True if the instance is operational.
        Instance is considered operational if both readiness and health checks have passed.

        Returns:
            bool: True if the instance is operational
        """
        return self.readiness_check_passed and self.health_check_passed

    @property
    def deduplication_key(self) -> str:
        """Returns the deduplication key for the instance lifecycle context.

        Deduplication key is used to uniquely identify the instance lifecycle context
        and is used to prevent duplicate processing of the same instance.

        Returns:
            str: Deduplication key
        """
        # Generate composite key to track unique readiness and health check configurations
        deduplication_key = f"{self.instance_id}"
        if self.readiness_config:
            deduplication_key += f"-{self.readiness_config}"
        if self.health_check_config:
            deduplication_key += f"-{self.health_check_config}"
        return deduplication_key

    def __post_init__(self):
        """Explicitly call the parent class __post_init__ method."""
        super().__post_init__()

    def __str__(self) -> str:
        return f"InstanceLifecycleContext(instance_id={self.instance_id}, scaling_group={self.scaling_group_config.scaling_group_name}, readiness={self.readiness_config}, health_check={self.health_check_config})"
