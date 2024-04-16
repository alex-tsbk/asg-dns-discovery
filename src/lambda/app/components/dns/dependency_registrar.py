from app.config.env_configuration_service import EnvironmentConfigurationService
from app.context import RUNTIME_CONTEXT
from app.utils.di import DIContainer, DILifetimeScope

from .dns_management_interface import DnsManagementInterface


def register_services(di_container: DIContainer, env_config_service: EnvironmentConfigurationService):
    """Registers services concrete implementations in the DI container.

    Args:
        di_container (DIContainer): DI container
    """

    if RUNTIME_CONTEXT.is_aws:
        from .internal.aws.aws_dns_management_service import AwsDnsManagementService

        di_container.register(
            DnsManagementInterface, AwsDnsManagementService, name="route53", lifetime=DILifetimeScope.SCOPED
        )
