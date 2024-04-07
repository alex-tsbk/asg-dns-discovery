from __future__ import annotations

from app.components.dns.dns_management_interface import DnsManagementInterface
from app.components.healthcheck.health_check_interface import HealthCheckInterface
from app.components.lifecycle.instance_lifecycle_interface import InstanceLifecycleInterface
from app.components.lifecycle.models.lifecycle_event_model_factory import LifecycleEventModelFactory
from app.components.mutex.distributed_lock_interface import DistributedLockInterface
from app.components.readiness.instance_readiness_interface import InstanceReadinessInterface
from app.config.env_configuration_service import EnvironmentConfigurationService
from app.config.runtime_configuration_service import RuntimeConfigurationService
from app.handlers.contexts.instance_lifecycle_context import InstanceLifecycleContext
from app.handlers.contexts.scaling_group_lifecycle_context import ScalingGroupLifecycleContext
from app.handlers.handler_base import HandlerBase
from app.utils.exceptions import BusinessException
from app.utils.logging import get_logger
from app.handlers.handler_context import HandlerContext


class ScalingGroupLifecycleHandler(HandlerBase[ScalingGroupLifecycleContext]):
    """Service responsible for handling lifecycle event"""

    def __init__(
        self,
        env_configuration_service: EnvironmentConfigurationService,
        runtime_configuration_service: RuntimeConfigurationService,
        lifecycle_event_model_factory: LifecycleEventModelFactory,
        lifecycle_service: InstanceLifecycleInterface,
        health_check_service: HealthCheckInterface,
        readiness_service: InstanceReadinessInterface,
        distributed_lock_service: DistributedLockInterface,
        dns_management_service: DnsManagementInterface,
    ) -> None:
        self.logger = get_logger()
        self.env_configuration_service = env_configuration_service
        self.runtime_configuration_service = runtime_configuration_service
        self.lifecycle_event_model_factory = lifecycle_event_model_factory
        self.lifecycle_service = lifecycle_service
        self.health_check_service = health_check_service
        self.readiness_service = readiness_service
        self.distributed_lock_service = distributed_lock_service
        self.dns_management_service = dns_management_service

    def handle(self, context: ScalingGroupLifecycleContext) -> HandlerContext:
        """Handle instance readiness lifecycle

        Args:
            context (ScalingGroupLifecycleContext): Context in which the handler is executed
        """

        event = context.event

        # Load all Scaling Group DNS configurations
        all_scaling_groups_configs = self.runtime_configuration_service.get_scaling_groups_dns_configs()
        if not all_scaling_groups_configs:
            self.logger.error("Unable to load Scaling Group DNS configurations.")
            raise BusinessException("Unable to load Scaling Group DNS configurations.")

        # Resolve all scaling group configurations for the current scaling group
        scaling_group_configs = all_scaling_groups_configs.for_scaling_group(event.scaling_group_name)
        if not scaling_group_configs:
            self.logger.warning(f"Scaling Group DNS configurations not found for ASG: {event.scaling_group_name}")
            raise BusinessException(f"Scaling Group DNS configurations not found for ASG: {event.scaling_group_name}")

        # For each scaling group dns configuration, gather information and perform appropriate actions
        for scaling_group_config in scaling_group_configs:

            readiness_config = scaling_group_config.readiness_config
            if not readiness_config:
                readiness_config = self.env_configuration_service.readiness_config

            instance_lifecycle_context = InstanceLifecycleContext(
                context_id=context.context_id,
                instance_id=event.instance_id,
                scaling_group_config=scaling_group_config,
                readiness_config=readiness_config,
                health_check_config=scaling_group_config.health_check_config,
            )

            context.register_instance_context(instance_lifecycle_context)

        return super().handle(context)
