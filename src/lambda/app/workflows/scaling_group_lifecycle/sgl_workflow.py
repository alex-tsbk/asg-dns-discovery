from app.components.mutex.distributed_lock_interface import DistributedLockInterface
from app.domain.handlers.handler_context import HandlerContext
from app.utils.di import Injectable, NamedInjectable
from app.utils.exceptions import BusinessException
from app.workflows.scaling_group_lifecycle.sgl_context import ScalingGroupLifecycleContext
from app.workflows.scaling_group_lifecycle.sgl_step import ScalingGroupLifecycleStep
from app.workflows.workflow_interface import WorkflowInterface


class ScalingGroupLifecycleWorkflow(WorkflowInterface[ScalingGroupLifecycleContext]):
    """Workflow for handling instance lifecycle events."""

    def __init__(
        self,
        distributed_lock_service: DistributedLockInterface,
        scaling_group_lifecycle_load_instance_configs: Injectable[ScalingGroupLifecycleStep, NamedInjectable("configs-loader")],
        scaling_group_lifecycle_load_metadata: Injectable[ScalingGroupLifecycleStep, NamedInjectable("metadata-loader")],
        scaling_group_lifecycle_handle_readiness_check: Injectable[ScalingGroupLifecycleStep, NamedInjectable("readiness-checks-handler")],
        scaling_group_lifecycle_plan_dns_changes: Injectable[ScalingGroupLifecycleStep, NamedInjectable("dns-planner")],
        scaling_group_lifecycle_apply_dns_changes: Injectable[ScalingGroupLifecycleStep, NamedInjectable("dns-applier")],
    ):  # fmt: skip
        self.distributed_lock_service = distributed_lock_service
        # Chain the handlers into a pipeline
        self.pipeline = (
            scaling_group_lifecycle_load_instance_configs
            >> scaling_group_lifecycle_load_metadata
            >> scaling_group_lifecycle_handle_readiness_check
            >> scaling_group_lifecycle_plan_dns_changes
            >> scaling_group_lifecycle_apply_dns_changes
        ).head()

    def handle(self, context: ScalingGroupLifecycleContext) -> HandlerContext:
        """Handles the request by invoking chained handlers in workflow pipeline.

        Args:
            context (T): Context in which the handler is executed
        """
        # TODO: Lock must be scaling group + dns hosted zone, record name, record type
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
