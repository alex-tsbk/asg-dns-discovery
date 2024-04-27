from app.utils.di import DIContainer

from .internal.concurrent_task_scheduler import ConcurrentTaskScheduler
from .task_scheduler_interface import TaskSchedulerInterface


def register_services(di_container: DIContainer):
    """Registers services concrete implementations in the DI container.

    Args:
        di_container (DIContainer): DI container
    """

    di_container.register(TaskSchedulerInterface, ConcurrentTaskScheduler)
