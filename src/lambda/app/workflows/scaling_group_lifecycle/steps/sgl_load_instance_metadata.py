from app.components.discovery.instance_discovery_interface import InstanceDiscoveryInterface
from app.domain.entities.instance import Instance
from app.domain.handlers.handler_context import HandlerContext
from app.utils import strings
from app.utils.exceptions import BusinessException
from app.utils.logging import get_logger
from app.workflows.scaling_group_lifecycle.sgl_context import ScalingGroupLifecycleContext
from app.workflows.scaling_group_lifecycle.sgl_step import ScalingGroupLifecycleStep


class ScalingGroupLifecycleLoadInstanceMetadataStep(ScalingGroupLifecycleStep):
    """
    Handles lifecycle event transitions for instances in a scaling group
    """

    def __init__(self, instance_discovery_service: InstanceDiscoveryInterface):
        self.logger = get_logger()
        self.instance_discovery_service = instance_discovery_service
        super().__init__()

    def handle(self, context: ScalingGroupLifecycleContext) -> HandlerContext:
        """Handles the scaling group lifecycle event

        Args:
            context (ScalingGroupLifecycleContext): Context in which the handler is executed
        """

        instance_id = context.event.instance_id

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

        # Update context
        context.instance_metadata = instance_model

        # Update each instance context
        for instance_context in context.instance_contexts_manager.get_all_contexts():
            instance_context.instance_model = instance_model

        # Continue handling
        return super().handle(context)
