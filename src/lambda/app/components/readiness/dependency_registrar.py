from app.config.env_configuration_service import EnvironmentConfigurationService
from app.config.runtime_context import RUNTIME_CONTEXT
from app.utils.di import DIContainer

from .instance_readiness_interface import InstanceReadinessInterface
from .internal.awaitable_instance_readiness_service import AwaitableInstanceReadinessService


def register_services(di_container: DIContainer, env_config_service: EnvironmentConfigurationService):
    """Registers services concrete implementations in the DI container.

    Args:
        di_container (DIContainer): DI container
    """
    if RUNTIME_CONTEXT.is_aws:
        from .internal.aws.aws_instance_readiness_service import AwsInstanceReadinessService

        # Registers AWS instance readiness service implementation
        di_container.register(InstanceReadinessInterface, AwsInstanceReadinessService, lifetime="scoped")
    # Register decorator that augments the service with awaitable functionality.
    # This allows to keep only platform-specific logic in the concrete implementation.
    di_container.decorate(InstanceReadinessInterface, AwaitableInstanceReadinessService)
