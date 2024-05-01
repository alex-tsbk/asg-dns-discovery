from app.contexts.scaling_group_lifecycle_context import ScalingGroupLifecycleContext
from app.domain.handlers.handler_base import HandlerBase
from app.domain.handlers.handler_context import HandlerContext
from app.utils.di import Injectable, NamedInjectable
from app.workflows.workflow_interface import WorkflowInterface


class ScalingGroupLifecycleWorkflow(WorkflowInterface[ScalingGroupLifecycleContext]):
    """Workflow for handling instance lifecycle events."""

    def __init__(
        self,
        scaling_group_lifecycle_init_handler: Injectable[HandlerBase[ScalingGroupLifecycleContext], NamedInjectable("init")],
        scaling_group_lifecycle_metadata_handler: Injectable[HandlerBase[ScalingGroupLifecycleContext], NamedInjectable("metadata")],
    ):  # fmt: skip
        # Chain the handlers into a pipeline
        self.pipeline = (
            scaling_group_lifecycle_init_handler >> scaling_group_lifecycle_metadata_handler
        ).head()  # Need to call head() to get the first handler in the pipeline

    def handle(self, context: ScalingGroupLifecycleContext) -> HandlerContext:
        """Handles the request by invoking chained handlers in workflow pipeline.

        Args:
            context (T): Context in which the handler is executed
        """

        return self.pipeline.handle(context)
