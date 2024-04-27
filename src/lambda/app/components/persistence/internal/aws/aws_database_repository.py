from typing import Any

from app.components.persistence.database_repository_interface import DatabaseRepositoryInterface
from app.utils.di import Injectable, NamedInjectable
from app.utils.logging import get_logger


class AwsDatabaseRepository(DatabaseRepositoryInterface):
    """Repository providing data in AWS environment."""

    def __init__(
        self,
        dynamodb_repository: Injectable[DatabaseRepositoryInterface, NamedInjectable("dynamodb")],  # noqa: F821
    ):
        self.logger = get_logger()
        self.repository: DatabaseRepositoryInterface = dynamodb_repository

    def get(self, key: str) -> dict[str, Any] | None:
        """Get item from DynamoDB table.

        Args:
            key (str): Resource ID that uniquely identifies the resource.

        Returns:
            dict: Item from DynamoDB table
        """
        return self.repository.get(key)

    def create(self, key: str, item: dict[str, Any]) -> dict[str, Any] | None:
        """Create item in DynamoDB table.

        Args:
            key (str):  In DynamoDB it is a 'resource_id' property in the table.
            item (dict): Item to be created in DynamoDB table.

        Returns:
            dict: Item created in storage. None if already exists.
        """
        return self.repository.create(key, item)

    def put(self, key: str, item: dict[str, Any]) -> dict[str, Any] | None:
        """Put item in DynamoDB table.

        Args:
            key (str): In DynamoDB it is a 'resource_id' property in the table.
            item (dict): Item to be put in DynamoDB table.
        """
        return self.repository.put(key, item)

    def delete(self, key: str) -> bool:
        """Delete item from DynamoDB table.

        Args:
            key (str): Resource ID that uniquely identifies the resource.
        """
        return self.repository.delete(key)
