from app.components.mutex.distributed_lock_interface import DistributedLockInterface
from app.domain.handlers.handler_context import HandlerContext
from app.utils.di import Injectable, NamedInjectable
from app.utils.exceptions import BusinessException
from app.workflows.scaling_group_lifecycle.scaling_group_lifecycle_context import ScalingGroupLifecycleContext
from app.workflows.scaling_group_lifecycle.scaling_group_lifecycle_step import ScalingGroupLifecycleStep
from app.workflows.workflow_interface import WorkflowInterface


class ScalingGroupLifecycleWorkflow(WorkflowInterface[ScalingGroupLifecycleContext]):
    """Workflow for handling instance lifecycle events."""

    def __init__(
        self,
        distributed_lock_service: DistributedLockInterface,
        scaling_group_lifecycle_init_handler: Injectable[ScalingGroupLifecycleStep, NamedInjectable("init")],
        scaling_group_lifecycle_metadata_handler: Injectable[ScalingGroupLifecycleStep, NamedInjectable("metadata")],
    ):  # fmt: skip
        self.distributed_lock_service = distributed_lock_service
        # Chain the handlers into a pipeline
        self.pipeline = (
            scaling_group_lifecycle_init_handler >> scaling_group_lifecycle_metadata_handler
        ).head()  # Need to call head() to get the first handler in the pipeline

    def handle(self, context: ScalingGroupLifecycleContext) -> HandlerContext:
        """Handles the request by invoking chained handlers in workflow pipeline.

        Args:
            context (T): Context in which the handler is executed
        """
        scaling_group_name = context.event.scaling_group_name
        try:
            # Ensure nothing else mutates the DNS for the scaling group
            if not self.distributed_lock_service.acquire_lock(scaling_group_name):
                raise BusinessException(f"Failed to acquire lock for scaling group: {scaling_group_name}")

            return self.pipeline.handle(context)
        except Exception as e:
            # TODO: Record data point
            raise BusinessException(f"Failed to handle scaling group lifecycle event: {e}") from e
        finally:
            self.distributed_lock_service.release_lock(scaling_group_name)
