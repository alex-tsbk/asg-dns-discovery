from typing import Any

from app.contexts.runtime_context import RUNTIME_CONTEXT
from app.domain.handlers.handler_protocol import HandlerProtocol
from app.utils.di import DIContainer
from app.utils.exceptions import BusinessException

from . import startup


def event_request_handler(*args: Any, **kwargs: Any) -> Any:
    """Pass-through function for the event request handler.
    Application is bootstrapped before the handler is imported,
    and request is passed through to the handler.

    Returns:
        Any: Response from the handler
    """
    # Bootstrap the application
    di_container: DIContainer = startup.build_container()

    # Placeholder for the handler that will be loaded based on the cloud provider
    handler: HandlerProtocol | None = None

    # Load the handler based on the cloud provider
    if RUNTIME_CONTEXT.is_aws:
        # Import handler and pass through the event
        from app.handlers.aws.scaling_group_lifecycle_event_handler import AwsScalingGroupLifecycleEventHandler

        handler = di_container.resolve(AwsScalingGroupLifecycleEventHandler)

    if handler is None:
        raise BusinessException(f"Handler not found for the specified cloud provider: {RUNTIME_CONTEXT.cloud_provider}")

    return handler.handle(*args, **kwargs)


def reconciliation_handler(*args: Any, **kwargs: Any) -> Any:
    """Pass-through function for the reconciliation handler.
    Application is bootstrapped before the handler is imported,
    and request is passed through to the handler.

    Returns:
        Any: Response from the handler
    """
    startup.build_container()
