from app.contexts.instance_lifecycle_context import InstanceLifecycleContext
from app.domain.handlers.handler_base import HandlerBase
from app.domain.handlers.handler_context import HandlerContext
from app.utils.di import Injectable, NamedInjectable
from app.workflows.workflow_interface import WorkflowInterface


class InstanceLifecycleWorkflow(WorkflowInterface[InstanceLifecycleContext]):
    """Workflow for handling instance lifecycle events."""

    def __init__(
        self,
        instance_discovery_handler: Injectable[HandlerBase[InstanceLifecycleContext], NamedInjectable("discovery")],  # noqa: F821
        instance_health_check_handler: Injectable[HandlerBase[InstanceLifecycleContext], NamedInjectable("health_check")],  # noqa: F821
        instance_readiness_handler: Injectable[HandlerBase[InstanceLifecycleContext], NamedInjectable("readiness")],  # noqa: F821
    ):  # fmt: skip
        # Chain the handlers into a pipeline
        self.pipeline = instance_discovery_handler \
            .chain(instance_health_check_handler) \
            .chain(instance_readiness_handler)  # fmt: skip

    def handle(self, context: InstanceLifecycleContext) -> HandlerContext:
        """Handles the request by invoking chained handlers in workflow pipeline.

        Args:
            context (T): Context in which the handler is executed
        """

        return self.pipeline.handle(context)
