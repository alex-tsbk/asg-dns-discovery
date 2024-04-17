import time

from app.components.mutex.distributed_lock_interface import DistributedLockInterface
from app.components.persistence.database_repository_interface import DatabaseRepositoryInterface
from app.utils.exceptions import BusinessException, CloudProviderException
from app.utils.logging import get_logger
from app.utils.serialization import to_json


class DistributedLockService(DistributedLockInterface):
    """Service class for acquiring and releasing shared state resource locks."""

    def __init__(self, repository: DatabaseRepositoryInterface) -> None:
        self.logger = get_logger()
        self.repository = repository

    def check_lock(self, lock_key: str) -> bool:
        """Checks if a lock exists on a resource.

        Args:
            resource_id (str): Resource ID that uniquely identifies the resource lock is to be checked for.

        Returns:
            bool: True if lock exists, False otherwise

        Raises:
            CloudProviderException: When underlying cloud provider operation fails.
        """
        resource_id = lock_key  # Explicit naming for context clarity
        self.logger.debug(f"Checking lock for resource: {resource_id}")
        item = self.repository.get(resource_id)
        self.logger.debug(f"check_lock item: {to_json(item)}")
        return bool(item)

    def acquire_lock(self, lock_key: str) -> bool:
        """Acquires a lock on a resource.

        Args:
            resource_id (str): Resource ID that uniquely identifies the resource lock is to be acquired on.

        Returns:
            bool: True if lock is acquired, False otherwise

        Raises:
            CloudProviderException: When underlying cloud provider operation fails.
        """
        resource_id = lock_key  # Explicit naming for context clarity
        self.logger.debug(f"Acquiring lock for resource: {resource_id}")
        try:
            item = {"timestamp": int(time.time())}
            response = self.repository.create(resource_id, item)
            self.logger.debug(f"acquire_lock response: {to_json(response)}")
            return bool(response)
        except CloudProviderException as e:
            raise e
        except Exception as e:
            raise BusinessException(f"Error acquiring lock for resource: {resource_id}")

    def release_lock(self, lock_key: str) -> None:
        """Releases a lock on a resource.

        Args:
            resource_id (str): Resource ID that uniquely identifies the resource lock is to be released for.

        Raises:
            CloudProviderException: When underlying cloud provider operation fails.
        """
        resource_id = lock_key  # Explicit naming for context clarity
        self.logger.debug(f"Releasing lock for resource: {resource_id}")
        try:
            self.repository.delete(resource_id)
        except CloudProviderException as e:
            raise e
        except Exception as e:
            raise BusinessException(f"Error acquiring lock for resource: {resource_id}")
