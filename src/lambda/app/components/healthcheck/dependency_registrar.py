from app.config.runtime_context import RuntimeContext
from app.utils.di import DIContainer

from .health_check_interface import HealthCheckInterface
from .internal.health_check_service import HealthCheckService


def register_services(di_container: DIContainer):
    """Registers DNS services concrete implementations in the DI container.

    Args:
        di_container (DIContainer): DI container
    """

    di_container.register(HealthCheckInterface, HealthCheckService, lifetime="scoped")
