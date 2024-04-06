from dataclasses import dataclass, field
from typing import Optional

from app.components.healthcheck.models.health_check_result_model import HealthCheckResultModel
from app.components.readiness.models.readiness_result_model import ReadinessResultModel
from app.config.models.health_check_config import HealthCheckConfig
from app.config.models.readiness_config import ReadinessConfig
from app.config.models.scaling_group_dns_config import ScalingGroupConfiguration
from app.handlers.handler_context import HandlerContext


@dataclass(kw_only=True)
class InstanceLifecycleContext(HandlerContext):
    """Context that tracks change of state over time for a single instance."""

    request_id: str
    instance_id: str
    # config
    scaling_group_config: ScalingGroupConfiguration
    readiness_config: ReadinessConfig
    health_check_config: HealthCheckConfig
    # state
    readiness_result: Optional[ReadinessResultModel] = field(default=None)
    health_check_result: Optional[HealthCheckResultModel] = field(default=None)

    def __post_init__(self):
        return super().__post_init__()
