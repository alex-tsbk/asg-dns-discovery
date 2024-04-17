from app.config.env_configuration_service import EnvironmentConfigurationService
from app.context import RUNTIME_CONTEXT
from app.utils.di import DIContainer, DILifetimeScope

from .database_repository_interface import DatabaseRepositoryInterface


def register_services(di_container: DIContainer, env_config_service: EnvironmentConfigurationService):
    """Registers services concrete implementations in the DI container.

    Args:
        di_container (DIContainer): DI container
    """

    if RUNTIME_CONTEXT.is_aws:
        from .internal.aws.aws_database_repository import AwsDatabaseRepository

        di_container.register(DatabaseRepositoryInterface, AwsDatabaseRepository, lifetime=DILifetimeScope.SCOPED)
