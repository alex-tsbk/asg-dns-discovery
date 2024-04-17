from abc import ABCMeta, abstractmethod
from typing import Any


class DatabaseRepositoryInterface(metaclass=ABCMeta):
    """Contract for accessing data in storage implementation."""

    @abstractmethod
    def get(self, key: str) -> dict[str, Any] | None:
        """Gets item from storage.

        Args:
            key (str):Key that uniquely identifies the item.

        Returns:
            dict: Item resolved from storage. None if not found.
        """
        pass

    @abstractmethod
    def create(self, key: str, item: dict[str, Any]) -> dict[str, Any] | None:
        """Create item in DynamoDB table.

        Args:
            key (str):  Not applicable to DynamoDB, but required for interface compatibility.
            item (dict): Item to be created in DynamoDB table.

        Returns:
            dict: Item created in storage. None if already exists.
        """
        pass

    @abstractmethod
    def put(self, key: str, item: dict[str, Any]) -> dict[str, Any] | None:
        """Put item in storage.

        Args:
            item (dict): Item to be put

        Returns:
            dict: Item created/updated in storage.
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete item from storage.

        Args:
            key (str): Key that uniquely identifies the resource.

        Returns:
            bool: True if item was deleted, False otherwise
        """
        pass
