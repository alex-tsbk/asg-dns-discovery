from app.config.env_configuration_service import EnvironmentConfigurationService
from app.config.models.scaling_group_config import ScalingGroupConfiguration
from app.config.sg_configuration_service import ScalingGroupConfigurationsService
from app.domain.handlers.handler_context import HandlerContext
from app.utils.exceptions import BusinessException
from app.utils.logging import get_logger
from app.workflows.instance_lifecycle.instance_lifecycle_context import InstanceLifecycleContext
from app.workflows.scaling_group_lifecycle.sgl_context import ScalingGroupLifecycleContext
from app.workflows.scaling_group_lifecycle.sgl_step import ScalingGroupLifecycleStep


class ScalingGroupLifecycleInitStep(ScalingGroupLifecycleStep):
    """
    Handler responsible for initializing the scaling group lifecycle event
    """

    def __init__(
        self,
        env_configuration_service: EnvironmentConfigurationService,
        sg_configuration_service: ScalingGroupConfigurationsService,
    ) -> None:
        super().__init__()
        self.logger = get_logger()
        self.env_configuration_service = env_configuration_service
        self.sg_configuration_service = sg_configuration_service

    def handle(self, context: ScalingGroupLifecycleContext) -> HandlerContext:
        """Handles the scaling group lifecycle event

        Args:
            context (ScalingGroupLifecycleContext): Context in which the handler is executed
        """

        event = context.event

        # Load all Scaling Group DNS configurations
        all_scaling_groups_configs = self.sg_configuration_service.get_configs()
        if not all_scaling_groups_configs:
            self.logger.error("Unable to load Scaling Group DNS configurations.")
            raise BusinessException("Unable to load Scaling Group DNS configurations.")

        # Resolve all scaling group configurations for the current scaling group
        scaling_group_configs: list[ScalingGroupConfiguration] = all_scaling_groups_configs.for_scaling_group(
            event.scaling_group_name
        )
        if not scaling_group_configs:
            self.logger.warning(f"Scaling Group DNS configurations not found for ASG: {event.scaling_group_name}")
            raise BusinessException(f"Scaling Group DNS configurations not found for ASG: {event.scaling_group_name}")

        # Augment context with scaling group configurations
        context.scaling_group_configs = scaling_group_configs

        # For each scaling group dns configuration, gather information and perform appropriate actions.
        # The reason we're spawning multiple instances of InstanceLifecycleContext is because instance might be
        # tracked by multiple scaling group configurations.

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
