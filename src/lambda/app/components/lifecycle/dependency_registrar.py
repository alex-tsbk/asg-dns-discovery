from app.components.lifecycle.models.lifecycle_event_model_factory import LifecycleEventModelFactory
from app.contexts.runtime_context import RUNTIME_CONTEXT
from app.utils.di import DIContainer

from .instance_lifecycle_interface import InstanceLifecycleInterface


def register_services(di_container: DIContainer):
    """Registers services concrete implementations in the DI container.

    Args:
        di_container (DIContainer): DI container
    """

    if RUNTIME_CONTEXT.is_aws:
        from .internal.aws.aws_instance_lifecycle_service import AwsInstanceLifecycleService

        di_container.register(InstanceLifecycleInterface, AwsInstanceLifecycleService)

    # Register factory so it can be consumed as a dependency
    lifecycle_event_mode_factory = LifecycleEventModelFactory()
    di_container.register_instance(lifecycle_event_mode_factory)
