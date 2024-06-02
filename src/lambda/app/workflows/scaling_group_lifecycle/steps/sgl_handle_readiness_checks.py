from app.components.concurrency.task_scheduler_interface import TaskSchedulerInterface
from app.components.lifecycle.models.lifecycle_event_model import LifecycleTransition
from app.components.readiness.instance_readiness_interface import InstanceReadinessInterface
from app.components.readiness.models.readiness_result_model import ReadinessResultModel
from app.config.models.readiness_config import ReadinessConfig
from app.domain.handlers.handler_context import HandlerContext
from app.utils.logging import get_logger
from app.workflows.instance_lifecycle.instance_lifecycle_context import InstanceLifecycleContext
from app.workflows.scaling_group_lifecycle.sgl_context import ScalingGroupLifecycleContext
from app.workflows.scaling_group_lifecycle.sgl_step import ScalingGroupLifecycleStep


class ScalingGroupLifecycleHandleReadinessChecksStep(ScalingGroupLifecycleStep):
    """
    Handles checking instance readiness for instance tracked readiness configurations
    """

    def __init__(
        self,
        task_scheduler_service: TaskSchedulerInterface,
        instance_readiness_service: InstanceReadinessInterface
    ) -> None:  # fmt: skip
        super().__init__()
        self.logger = get_logger()
        self.task_scheduler_service = task_scheduler_service
        self.instance_readiness_service = instance_readiness_service

    def handle(self, context: ScalingGroupLifecycleContext) -> HandlerContext:
        """Handles the scaling group lifecycle event

        Args:
            context (ScalingGroupLifecycleContext): Context in which the handler is executed
        """

        event = context.event

        if event.transition == LifecycleTransition.DRAINING:
            # There is no need to check readiness for instances that are draining
            return super().handle(context)

        # Select only distinct readiness configurations from all instances contexts which do require validation
        readiness_configs_require_checking: dict[str, tuple[ReadinessConfig, list[InstanceLifecycleContext]]] = (
            context.instance_contexts_manager.get_readiness_configs_require_checking()
        )

        # Schedule readiness checks on background thread, so they don't block the main thread
        for config_to_instance_map in readiness_configs_require_checking.values():
            self.task_scheduler_service.place(
                self.instance_readiness_service.is_ready,
                event.instance_id,
                config_to_instance_map[0],
            )

        # State the fact that readiness checks have been dispatched and now in progress
        self.logger.debug(
            f"Running {len(readiness_configs_require_checking)} readiness checks for {event.instance_id} on background thread."
        )

        # Retrieve readiness check results
        for done_item in self.task_scheduler_service.retrieve():
            # 'done_item' is ReadinessResultModel
            if not isinstance(done_item, ReadinessResultModel):
                self.logger.error(f"Unexpected result type: {type(done_item)}")
                continue

            # Backfill readiness results into instance contexts
            for instance_context in readiness_configs_require_checking[done_item.readiness_config_hash][1]:
                instance_context.readiness_result = done_item
            self.logger.debug(f"Readiness check completed: {done_item}")

        return super().handle(context)
