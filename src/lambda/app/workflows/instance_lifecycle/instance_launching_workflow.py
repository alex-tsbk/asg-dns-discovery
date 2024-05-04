from app.domain.handlers.handler_context import HandlerContext
from app.utils.di import Injectable, NamedInjectable
from app.workflows.instance_lifecycle.instance_lifecycle_context import InstanceLifecycleContext
from app.workflows.instance_lifecycle.instance_lifecycle_step import InstanceLifecycleStep
from app.workflows.workflow_interface import WorkflowInterface


class InstanceLaunchingLifecycleWorkflow(WorkflowInterface[InstanceLifecycleContext]):
    """Workflow for handling instance lifecycle events."""

    def __init__(
        self,
        instance_load_metadata: Injectable[InstanceLifecycleStep, NamedInjectable("metadata-loader")],
        instance_check_ready: Injectable[InstanceLifecycleStep, NamedInjectable("readiness-check")],
        instance_check_healthy: Injectable[InstanceLifecycleStep, NamedInjectable("health-check")],
    ):  # fmt: skip
        # Chain the handlers into a pipeline
        self.pipeline = (instance_load_metadata >> instance_check_ready >> instance_check_healthy).head()

    def handle(self, context: InstanceLifecycleContext) -> HandlerContext:
        """Handles the request by invoking chained handlers in workflow pipeline.

        Args:
            context (T): Context in which the handler is executed
        """

        return self.pipeline.handle(context)
