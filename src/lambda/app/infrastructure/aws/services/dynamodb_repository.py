from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from app.components.persistence.database_repository_interface import DatabaseRepositoryInterface
from app.infrastructure.aws.boto_factory import resolve_resource
from app.utils.exceptions import CloudProviderException
from app.utils.logging import get_logger
from app.utils.serialization import to_json
from botocore.exceptions import ClientError

if TYPE_CHECKING:
    from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table
    from mypy_boto3_dynamodb.type_defs import (
        DeleteItemOutputTableTypeDef,
        GetItemOutputTableTypeDef,
        PutItemOutputTableTypeDef,
    )


class DynamoDbTableRepository(DatabaseRepositoryInterface):
    """Repository for interacting with AWS DynamoDB Table.
    Having this class allows to abstract the interaction with DynamoDB table specifically,
    and allows to mock the DynamoDB table in unit tests.
    """

    dynamodb_resource: Optional[DynamoDBServiceResource] = None

    def __init__(self, table_name: str):
        """Default ctor.

        Args:
            table_name (str): Name of the DynamoDB table to interact with.
        """
        self.logger = get_logger()
        self.table_name: str = table_name
        # Lazy load the DynamoDB resource
        if not self.dynamodb_resource:
            self.dynamodb_resource = resolve_resource("dynamodb")  # type: ignore
        self.table: Table = self.dynamodb_resource.Table(table_name)  # type: ignore

    def get(self, key: str) -> dict[str, Any]:
        """Get item from DynamoDB table.

        Args:
            key (str): Resource ID that uniquely identifies the resource.

        Returns:
            dict: Item from DynamoDB table
        """
        try:
            # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/table/get_item.html
            response: GetItemOutputTableTypeDef = self.table.get_item(Key={"id": key}, ConsistentRead=True)
            self.logger.debug(f"{self.__class__.__name__} get_item response: {to_json(response)}")
            return response.get("Item", {})
        except ClientError as e:
            raise CloudProviderException(e, f"Error getting item from DynamoDB table '{self.table_name}': {str(e)}")

    def create(self, key: str, item: dict[str, Any]) -> dict[str, Any] | None:
        """Create item in DynamoDB table.

        Args:
            key (str):  In DynamoDB it is a rid' property in the table.
            item (dict): Item to be created in DynamoDB table.

        Returns:
            dict: Item created in storage. None if already exists.

        Raises:
            CloudProviderException: When underlying cloud provider operation fails.
        """
        try:
            # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/table/put_item.html
            kwargs: dict[str, Any] = {
                "Item": {"id": key} | item,
                "ConditionExpression": "attribute_not_exists(id)",
            }
            response = self.table.put_item(**kwargs)
            self.logger.debug(f"{self.__class__.__name__} put_item response: {to_json(response)}")
            return item
        except ClientError as e:
            raise CloudProviderException(e, f"Error creating item in DynamoDB table '{self.table_name}': {str(e)}")

    def put(self, key: str, item: dict[str, Any]) -> dict[str, Any] | None:
        """Put item in DynamoDB table.

        Args:
            key (str): In DynamoDB it is a 'rid' property in the table.
            item (dict): Item to be put in DynamoDB table.
        """
        try:
            table_item = {"id": key} | item
            # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/table/put_item.html
            response: PutItemOutputTableTypeDef = self.table.put_item(Item=table_item)
            self.logger.debug(f"{self.__class__.__name__} put_item response: {to_json(response)}")
            return item
        except ClientError as e:
            raise CloudProviderException(e, f"Error putting item in DynamoDB table '{self.table_name}': {str(e)}")

    def delete(self, key: str) -> bool:
        """Delete item from DynamoDB table.

        Args:
            key (str): Resource ID that uniquely identifies the resource.

        Raises:
            CloudProviderException: When underlying cloud provider operation fails.
        """
        try:
            # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/table/delete_item.html
            response: DeleteItemOutputTableTypeDef = self.table.delete_item(Key={"id": key})
            self.logger.debug(f"{self.__class__.__name__} delete_item response: {to_json(response)}")
            return True
        except ClientError as e:
            raise CloudProviderException(
                e, f"Error deleting item '{key}' from DynamoDB table '{self.table_name}': {str(e)}"
            )
