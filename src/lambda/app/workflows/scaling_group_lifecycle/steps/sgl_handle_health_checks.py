from app.components.concurrency.task_scheduler_interface import TaskSchedulerInterface
from app.components.discovery.instance_discovery_interface import InstanceDiscoveryInterface
from app.components.healthcheck.health_check_interface import HealthCheckInterface
from app.components.healthcheck.models.health_check_result_model import HealthCheckResultModel
from app.components.lifecycle.models.lifecycle_event_model import LifecycleTransition
from app.components.metadata.instance_metadata_interface import InstanceMetadataInterface
from app.components.metadata.models.metadata_result_model import MetadataResultModel
from app.config.models.health_check_config import HealthCheckConfig
from app.domain.entities.instance import Instance
from app.domain.handlers.handler_context import HandlerContext
from app.utils import strings
from app.utils.exceptions import BusinessException
from app.utils.logging import get_logger
from app.workflows.instance_lifecycle.instance_lifecycle_context import InstanceLifecycleContext
from app.workflows.scaling_group_lifecycle.sgl_context import ScalingGroupLifecycleContext
from app.workflows.scaling_group_lifecycle.sgl_step import ScalingGroupLifecycleStep


class ScalingGroupLifecycleHandleHealthChecksStep(ScalingGroupLifecycleStep):
    """
    Handles checking instance health for instance tracked health configurations
    """

    def __init__(
        self,
        task_scheduler_service: TaskSchedulerInterface,
        instance_health_check_service: HealthCheckInterface,
        instance_discovery_service: InstanceDiscoveryInterface,
        instance_metadata_service: InstanceMetadataInterface,
    ) -> None:  # fmt: skip
        super().__init__()
        self.logger = get_logger()
        self.task_scheduler_service = task_scheduler_service
        self.instance_health_check_service = instance_health_check_service
        self.instance_discovery_service = instance_discovery_service
        self.instance_metadata_service = instance_metadata_service

    def handle(self, context: ScalingGroupLifecycleContext) -> HandlerContext:
        """Handles the scaling group lifecycle event

        Args:
            context (ScalingGroupLifecycleContext): Context in which the handler is executed
        """

        event = context.event
        instance_id = context.event.instance_id

        if event.transition == LifecycleTransition.DRAINING:
            # There is no need to check health for instances that are draining
            return super().handle(context)

        # Select only distinct health checks configurations from all instances contexts which do require validation
        health_check_configs_require_checking: dict[str, tuple[HealthCheckConfig, list[InstanceLifecycleContext]]] = (
            context.instance_contexts_manager.get_health_check_configs_require_checking()
        )

        # Perform instance discovery
        instance_models: list[Instance] = self.instance_discovery_service.describe_instances(instance_id)
        if not instance_models:
            raise BusinessException(f"Instance {instance_id} could not be described.")

        # Instance model
        instance_model = instance_models[0]
        if not strings.alike(instance_model.instance_id, instance_id):
            raise BusinessException(
                f"Instance {instance_id} metadata was requested, received response for '{instance_model.instance_id}'."
            )

        # Schedule health checks on background thread, so they don't block the main thread
        for config_to_instance_map in health_check_configs_require_checking.values():
            health_check_config = config_to_instance_map[0]
            destination: MetadataResultModel = self.instance_metadata_service.resolve_value(
                instance_model, health_check_config.endpoint_source
            )
            self.task_scheduler_service.place(
                self.instance_health_check_service.check,
                destination.value,
                health_check_config,
            )

        # State the fact that health checks have been dispatched and now in progress
        self.logger.debug(
            f"Running {len(health_check_configs_require_checking)} health checks for {event.instance_id} on background thread."
        )

        # Retrieve health check results
        for done_item in self.task_scheduler_service.retrieve():
            # 'done_item' is HealthCheckResultModel
            if not isinstance(done_item, HealthCheckResultModel):
                self.logger.error(f"Unexpected result type: {type(done_item)}")
                continue

            # Backfill health check results into instance contexts
            for instance_context in health_check_configs_require_checking[done_item.health_check_config_hash][1]:
                instance_context.health_check_result = done_item
            self.logger.debug(f"Health check completed: {done_item}")

        return super().handle(context)
