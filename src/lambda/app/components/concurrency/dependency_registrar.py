from app.utils.di import DIContainer, DILifetimeScope

from .internal.concurrent_task_scheduler import ConcurrentTaskScheduler
from .task_scheduler_interface import TaskSchedulerInterface


def register_services(di_container: DIContainer):
    """Registers services concrete implementations in the DI container.

    Args:
        di_container (DIContainer): DI container
    """

    # Ensure it's dependency get's it's own task scheduler
    di_container.register(TaskSchedulerInterface, ConcurrentTaskScheduler, lifetime=DILifetimeScope.TRANSIENT)
