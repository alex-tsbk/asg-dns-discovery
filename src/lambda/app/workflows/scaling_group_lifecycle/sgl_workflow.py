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
        sgl_load_instance_configs: Injectable[ScalingGroupLifecycleStep, NamedInjectable("configs-loader")],
        sgl_handle_readiness_check: Injectable[ScalingGroupLifecycleStep, NamedInjectable("readiness-checks-handler")],
        sgl_handle_health_check: Injectable[ScalingGroupLifecycleStep, NamedInjectable("health-checks-handler")],
        sgl_load_metadata: Injectable[ScalingGroupLifecycleStep, NamedInjectable("metadata-loader")],
        sgl_hook_notifier: Injectable[ScalingGroupLifecycleStep, NamedInjectable("lch-handler")],
        sgl_plan_dns_changes: Injectable[ScalingGroupLifecycleStep, NamedInjectable("dns-planner")],
        sgl_apply_dns_changes: Injectable[ScalingGroupLifecycleStep, NamedInjectable("dns-applier")],
    ):  # fmt: skip
        self.distributed_lock_service = distributed_lock_service
        # Chain the handlers into a pipeline
        self.pipeline = (
            sgl_load_instance_configs
            >> sgl_handle_readiness_check
            >> sgl_handle_health_check
            >> sgl_load_metadata
            >> sgl_plan_dns_changes
            >> sgl_apply_dns_changes
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
