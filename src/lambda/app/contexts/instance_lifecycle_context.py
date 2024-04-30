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

    def __post_init__(self):
        return super().__post_init__()

    def __str__(self) -> str:
        return f"InstanceLifecycleContext(instance_id={self.instance_id}, scaling_group={self.scaling_group_config.scaling_group_name})"
