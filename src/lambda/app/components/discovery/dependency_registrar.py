from app.config.env_configuration_service import EnvironmentConfigurationService
from app.runtime_context import RUNTIME_CONTEXT
from app.utils.di import DIContainer, DILifetimeScope

from .instance_discovery_interface import InstanceDiscoveryInterface


def register_services(di_container: DIContainer, env_config_service: EnvironmentConfigurationService):
    """Registers services concrete implementations in the DI container.

    Args:
        di_container (DIContainer): DI container
    """
    if RUNTIME_CONTEXT.is_aws:
        from .internal.aws.aws_instance_discovery_service import AwsInstanceDiscoveryService

        di_container.register(InstanceDiscoveryInterface, AwsInstanceDiscoveryService, lifetime=DILifetimeScope.SCOPED)
