from app.config.env_configuration_service import EnvironmentConfigurationService
from app.config.runtime_context import RUNTIME_CONTEXT
from app.utils.di import DIContainer

from .instance_readiness_interface import InstanceReadinessInterface


def register_services(di_container: DIContainer, env_config_service: EnvironmentConfigurationService):
    """Registers services concrete implementations in the DI container.

    Args:
        di_container (DIContainer): DI container
    """
    if RUNTIME_CONTEXT.is_aws:
        from .internal.aws.aws_readiness_service import AwsInstanceReadinessService

        di_container.register(InstanceReadinessInterface, AwsInstanceReadinessService, lifetime="scoped")
