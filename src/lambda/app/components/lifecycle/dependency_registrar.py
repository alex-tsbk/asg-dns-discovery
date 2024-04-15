from app.config.env_configuration_service import EnvironmentConfigurationService
from app.runtime_context import RUNTIME_CONTEXT
from app.utils.di import DIContainer, DILifetimeScope

from .instance_lifecycle_interface import InstanceLifecycleInterface


def register_services(di_container: DIContainer, env_config_service: EnvironmentConfigurationService):
    """Registers services concrete implementations in the DI container.

    Args:
        di_container (DIContainer): DI container
    """

    if RUNTIME_CONTEXT.is_aws:
        from .internal.aws.aws_instance_lifecycle_service import AwsInstanceLifecycleService

        di_container.register(InstanceLifecycleInterface, AwsInstanceLifecycleService, lifetime=DILifetimeScope.SCOPED)
