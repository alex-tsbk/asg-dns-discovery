from app.config.env_configuration_service import EnvironmentConfigurationService
from app.utils.di import DIContainer, DILifetimeScope

from .internal.concurrent_task_scheduler import ConcurrentTaskScheduler
from .task_scheduler_interface import TaskSchedulerInterface


def register_services(di_container: DIContainer, env_config_service: EnvironmentConfigurationService):
    """Registers services concrete implementations in the DI container.

    Args:
        di_container (DIContainer): DI container
    """

    di_container.register(TaskSchedulerInterface, ConcurrentTaskScheduler, lifetime=DILifetimeScope.SCOPED)
