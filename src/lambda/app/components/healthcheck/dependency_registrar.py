from app.config.env_configuration_service import EnvironmentConfigurationService
from app.utils.di import DIContainer, DILifetimeScope

from .health_check_interface import HealthCheckInterface
from .internal.health_check_service import HealthCheckService


def register_services(di_container: DIContainer, env_config_service: EnvironmentConfigurationService):
    """Registers services concrete implementations in the DI container.

    Args:
        di_container (DIContainer): DI container
    """

    di_container.register(HealthCheckInterface, HealthCheckService, lifetime=DILifetimeScope.SCOPED)
