from app.utils.di import DIContainer

from .distributed_lock_interface import DistributedLockInterface
from .internal.awaitable_distributed_lock_service import AwaitableDistributedLockService
from .internal.distributed_lock_service import DistributedLockService


def register_services(di_container: DIContainer):
    """Registers services concrete implementations in the DI container.

    Args:
        di_container (DIContainer): DI container
    """
    di_container.register(DistributedLockInterface, DistributedLockService)
    # Register decorator service
    di_container.decorate(DistributedLockInterface, AwaitableDistributedLockService)
