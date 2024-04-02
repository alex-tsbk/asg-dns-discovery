from time import sleep

from app.components.mutex.distributed_lock_interface import DistributedLockInterface
from app.utils.logging import get_logger


class AwaitableDistributedLockService(DistributedLockInterface):
    """Decorator implementation of service for acquiring and releasing shared state resource locks."""

    def __init__(self, distributed_lock_service: DistributedLockInterface) -> None:
        self.logger = get_logger()
        self.distributed_lock_service = distributed_lock_service

    def check_lock(self, resource_id: str) -> bool:
        return self.distributed_lock_service.check_lock(resource_id)

    def acquire_lock(self, resource_id: str) -> bool:
        """Acquires lock for the resource.
        Will attempt to acquire lock with incremental backoff ( up to ~1 minute).

        Args:
            resource_id (str): Resource ID that uniquely identifies the resource lock is to be acquired on.

        Returns:
            bool: True if lock is acquired, False otherwise
        """
        lock_obtained = False
        lock_request_count = 1
        lock_request_max_attempts = 10
        while not lock_obtained or lock_request_count <= 10:
            lock_obtained = self.distributed_lock_service.acquire_lock(resource_id)
            if lock_obtained:
                break
            self.logger.debug(
                f"Waiting for lock to be obtained: {resource_id} [{lock_request_count}/{lock_request_max_attempts}]"
            )
            sleep(lock_request_count)  # Incremental backoff
            lock_request_count += 1
        return lock_obtained

    def release_lock(self, resource_id: str) -> None:
        self.distributed_lock_service.release_lock(resource_id)
