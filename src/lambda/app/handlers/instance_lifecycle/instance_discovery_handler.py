from app.components.discovery.instance_discovery_interface import InstanceDiscoveryInterface
from app.entities.instance import Instance
from app.handlers.contexts.instance_lifecycle_context import InstanceLifecycleContext
from app.handlers.handler_base import HandlerBase
from app.handlers.handler_context import HandlerContext
from app.utils.exceptions import BusinessException
from app.utils.logging import get_logger


class InstanceDiscoveryHandler(HandlerBase[InstanceLifecycleContext]):
    """Handles resolving instance metadata in the instance lifecycle"""

    def __init__(self, instance_discovery_service: InstanceDiscoveryInterface):
        self.logger = get_logger()
        self.instance_discovery_service = instance_discovery_service
        super().__init__()

    def handle(self, context: InstanceLifecycleContext) -> HandlerContext:
        """Handle instance discovery lifecycle step

        Args:
            context (InstanceLifecycleContext): Context in which the handler is executed
        """

        # Perform instance discovery
        instance_models: list[Instance] = self.instance_discovery_service.describe_instances(context.instance_id)
        if not instance_models:
            raise BusinessException(f"Instance {context.instance_id} not found")

        # Instance model
        instance_model = instance_models[0]
        if instance_model.instance_id != context.instance_id:
            raise BusinessException(f"Instance {context.instance_id} not found")

        # Update context
        context.instance_model = instance_model

        # Continue handling
        return super().handle(context)
