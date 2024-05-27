from typing import Optional

from app.components.concurrency.task_scheduler_interface import TaskSchedulerInterface
from app.components.discovery.instance_discovery_interface import InstanceDiscoveryInterface
from app.components.lifecycle.models.lifecycle_event_model import LifecycleTransition
from app.domain.handlers.handler_context import HandlerContext
from app.utils.di import Injectable, NamedInjectable
from app.utils.exceptions import BusinessException
from app.utils.logging import get_logger
from app.workflows.instance_lifecycle.instance_lifecycle_context import InstanceLifecycleContext
from app.workflows.scaling_group_lifecycle.sgl_context import ScalingGroupLifecycleContext
from app.workflows.scaling_group_lifecycle.sgl_step import ScalingGroupLifecycleStep
from app.workflows.workflow_interface import WorkflowInterface


class ScalingGroupLifecycleHandleTransitionStep(ScalingGroupLifecycleStep):
    """
    Handles lifecycle event transitions for instances in a scaling group
    """

    def __init__(
        self,
        task_scheduler_service: TaskSchedulerInterface,
        instance_discovery_service: InstanceDiscoveryInterface,
        instance_launching_workflow: Injectable[WorkflowInterface[InstanceLifecycleContext], NamedInjectable(LifecycleTransition.LAUNCHING.value)],
        instance_draining_workflow: Injectable[WorkflowInterface[InstanceLifecycleContext], NamedInjectable(LifecycleTransition.DRAINING.value)],
    ) -> None:  # fmt: skip
        super().__init__()
        self.logger = get_logger()
        self.task_scheduler_service = task_scheduler_service
        self.instance_discovery_service = instance_discovery_service
        # Workflows for handling instance lifecycle events
        self.instance_launching_workflow = instance_launching_workflow
        self.instance_draining_workflow = instance_draining_workflow

    def handle(self, context: ScalingGroupLifecycleContext) -> HandlerContext:
        """Handles the scaling group lifecycle event

        Args:
            context (ScalingGroupLifecycleContext): Context in which the handler is executed
        """

        event = context.event

        workflow: Optional[WorkflowInterface[InstanceLifecycleContext]] = None

        if event.transition == LifecycleTransition.LAUNCHING:
            workflow = self.instance_launching_workflow

        if event.transition == LifecycleTransition.DRAINING:
            workflow = self.instance_draining_workflow

        if workflow is None:
            raise BusinessException(f"Unsupported lifecycle event transition: {event.transition}")

        # Schedule instance workflow on background thread, so they don't block the main thread
        # TODO: Need to rework this. We need only to run distinct readiness checks for each instance,
        # as well as health checks. Also, we don't need to load metadata for same instances multiple times.
        for instance_lifecycle_context in context.instances_contexts:
            self.task_scheduler_service.place(workflow.handle, instance_lifecycle_context)

        self.logger.debug(f"Dispatched {event.transition} event for {len(context.instances_contexts)} instances")

        for done_item in self.task_scheduler_service.retrieve():
            self.logger.debug(f"Instance lifecycle event completed: {done_item}")

        return super().handle(context)
