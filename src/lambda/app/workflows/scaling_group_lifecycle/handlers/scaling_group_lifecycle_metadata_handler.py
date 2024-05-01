from typing import Optional

from app.components.concurrency.task_scheduler_interface import TaskSchedulerInterface
from app.components.discovery.instance_discovery_interface import InstanceDiscoveryInterface
from app.components.lifecycle.models.lifecycle_event_model import LifecycleTransition
from app.contexts.instance_lifecycle_context import InstanceLifecycleContext
from app.contexts.scaling_group_lifecycle_context import ScalingGroupLifecycleContext
from app.domain.handlers.handler_base import HandlerBase
from app.domain.handlers.handler_context import HandlerContext
from app.utils.di import Injectable, NamedInjectable
from app.utils.exceptions import BusinessException
from app.utils.logging import get_logger


class ScalingGroupLifecycleMetadataHandler(HandlerBase[ScalingGroupLifecycleContext]):
    """Service responsible for handling lifecycle event"""

    def __init__(
        self,
        task_scheduler_service: TaskSchedulerInterface,
        instance_discovery_service: InstanceDiscoveryInterface,
        instance_discovery_handler: Injectable[HandlerBase[InstanceLifecycleContext], NamedInjectable("discovery")],
        instance_readiness_handler: Injectable[HandlerBase[InstanceLifecycleContext], NamedInjectable("readiness")],
        instance_health_check_handler: Injectable[HandlerBase[InstanceLifecycleContext], NamedInjectable("health-check")],
    ) -> None:  # fmt: skip
        super().__init__()
        self.logger = get_logger()
        self.task_scheduler_service = task_scheduler_service
        self.instance_discovery_service = instance_discovery_service
        self.instance_discovery_handler = instance_discovery_handler
        self.instance_readiness_handler = instance_readiness_handler
        self.instance_health_check_handler = instance_health_check_handler

    def handle(self, context: ScalingGroupLifecycleContext) -> HandlerContext:
        """Handle instance readiness lifecycle

        Args:
            context (ScalingGroupLifecycleContext): Context in which the handler is executed
        """

        event = context.event

        instance_pipeline: Optional[HandlerBase[InstanceLifecycleContext]] = None

        if event.transition == LifecycleTransition.LAUNCHING:
            instance_pipeline = (
                self.instance_discovery_handler >> self.instance_readiness_handler >> self.instance_health_check_handler
            ).head()  # Calling head() is necessary to get the first handler in the pipeline, instead of the last one

        if event.transition == LifecycleTransition.DRAINING:
            instance_pipeline = self.instance_discovery_handler

        if instance_pipeline is None:
            raise BusinessException(f"Unsupported lifecycle event transition: {event.transition}")

        # Schedule instance pipeline on background thread, so they don't block the main thread
        for instance_context in context.instances_contexts:
            self.task_scheduler_service.place(instance_pipeline.handle, instance_context)

        self.logger.debug(f"Dispatched {event.transition} event for {len(context.instances_contexts)} instances")

        for done_item in self.task_scheduler_service.retrieve():
            self.logger.debug(f"Instance lifecycle event completed: {done_item}")

        return super().handle(context)
