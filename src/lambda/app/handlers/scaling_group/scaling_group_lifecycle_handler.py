from __future__ import annotations

from time import sleep

from app.components.dns.dns_management_interface import DnsManagementInterface
from app.components.dns.models.dns_change_request_model import DnsChangeRequestModel
from app.components.dns.models.dns_change_response_model import DnsChangeResponseModel
from app.components.healthcheck.health_check_interface import HealthCheckInterface
from app.components.lifecycle.instance_lifecycle_interface import InstanceLifecycleInterface
from app.components.lifecycle.models.lifecycle_event_model import LifecycleAction, LifecycleEventModel
from app.components.lifecycle.models.lifecycle_event_model_factory import LifecycleEventModelFactory
from app.components.mutex.distributed_lock_interface import DistributedLockInterface
from app.components.readiness.instance_readiness_interface import InstanceReadinessInterface
from app.config.env_configuration_service import EnvironmentConfigurationService
from app.config.models.readiness_config import ReadinessConfig
from app.config.models.scaling_group_dns_config import ScalingGroupConfiguration, ScalingGroupConfigurations
from app.config.runtime_configuration_service import RuntimeConfigurationService
from app.handlers.contexts.instance_lifecycle_context import InstanceLifecycleContext
from app.handlers.contexts.scaling_group_lifecycle_context import ScalingGroupLifecycleContext
from app.handlers.handler_base import HandlerBase
from app.handlers.handler_interface import HandlerInterface
from app.handlers.instance.instance_readiness_handler import InstanceReadinessHandler
from app.utils.di import Injectable, NamedInjectable
from app.utils.exceptions import BusinessException
from app.utils.logging import get_logger


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

    def handle(self, context: ScalingGroupLifecycleContext) -> ScalingGroupLifecycleContext:
        """Handle instance readiness lifecycle

        Args:
            context (ScalingGroupLifecycleContext): Context in which the handler is executed
        """

        event = context.event

        # Load all Scaling Group DNS configurations
        all_scaling_groups_configs = self.runtime_configuration_service.get_scaling_groups_dns_configs()
        if not all_scaling_groups_configs:
            self.logger.error("Unable to load Scaling Group DNS configurations.")
            return False

        # Resolve all scaling group configurations for the current scaling group
        scaling_group_configs = all_scaling_groups_configs.for_scaling_group(event.scaling_group_name)
        if not scaling_group_configs:
            self.logger.warning(f"Scaling Group DNS configurations not found for ASG: {event.scaling_group_name}")
            return False

        # For each scaling group dns configuration, gather information and perform appropriate actions
        for scaling_group_config in scaling_group_configs:

            readiness_config = scaling_group_config.readiness_config
            if not readiness_config:
                readiness_config = self.env_configuration_service.readiness_config

            instance_lifecycle_context = InstanceLifecycleContext(
                request_id=context.request_id,
                instance_id=event.instance_id,
                scaling_group_config=scaling_group_config,
                readiness_config=readiness_config,
                health_check_config=scaling_group_config.health_check_config,
            )

            context.register_instance_context(instance_lifecycle_context)

        return super().handle(context)
        # # Check if health check is enabled
        # health_check_enabled = (
        #     scaling_group_config.health_check_config and scaling_group_config.health_check_config.enabled
        # )
        # if health_check_enabled:
        #     # Perform health check
        #     health_check_result = self.health_check_service.check(event.instance_id, scaling_group_config)
        #     if not health_check_result:
        #         completion_status = self.lifecycle_service.complete_lifecycle_action(event, LifecycleAction.ABANDON)
        #         self.logger.info(f"Lifecycle completed successfully: {completion_status}")
        #         return False
