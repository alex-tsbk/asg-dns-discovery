from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping

if TYPE_CHECKING:
    from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table

import boto3
from app.components.persistence.repository_service_interface import RepositoryInterface
from app.config.env_configuration_service import EnvironmentConfigurationService
from app.infrastructure.aws import boto_config
from app.utils.exceptions import CloudProviderException
from app.utils.logging import get_logger
from app.utils.serialization import to_json
from botocore.exceptions import ClientError


class AwsDynamoDBRepository(RepositoryInterface):
    """Repository for accessing items in DynamoDB table."""

    def __init__(self, environment_configuration_service: EnvironmentConfigurationService):
        self.logger = get_logger()
        self.dynamodb: DynamoDBServiceResource = boto3.resource("dynamodb", config=boto_config.CONFIG)  # type: ignore
        dynamodb_table_name = environment_configuration_service.db_config.table_name
        self.table: Table = self.dynamodb.Table(dynamodb_table_name)

    def get(self, key: str) -> Mapping[str, Any]:
        """Get item from DynamoDB table.

        Args:
            key (str): Resource ID that uniquely identifies the resource.

        Returns:
            dict: Item from DynamoDB table
        """
        try:
            # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/table/get_item.html
            response = self.table.get_item(Key={"resource_id": key}, ConsistentRead=True)
            self.logger.debug(f"get_item response: {to_json(response)}")
            return response.get("Item", {})
        except ClientError as e:
            raise CloudProviderException(e, f"Error getting item from DynamoDB table: {str(e)}")

    def create(self, key: str, item: Mapping[str, Any]) -> Mapping[str, Any] | None:
        """Create item in DynamoDB table.

        Args:
            key (str):  In DynamoDB it is a 'resource_id' property in the table.
            item (dict): Item to be created in DynamoDB table.

        Returns:
            dict: Item created in storage. None if already exists.

        Raises:
            CloudProviderException: When underlying cloud provider operation fails.
        """
        try:
            # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/table/put_item.html
            kwargs: Mapping[str, Any] = {
                "Item": {"resource_id": key, **item},
                "ConditionExpression": "attribute_not_exists(resource_id)",
            }
            response = self.table.put_item(**kwargs)
            self.logger.debug(f"put_item response: {to_json(response)}")
            return item
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":  # type: ignore
                return None
            raise CloudProviderException(e, f"Error putting item in DynamoDB table: {str(e)}")

    def put(self, key: str, item: Mapping[str, Any]) -> Mapping[str, Any] | None:
        """Put item in DynamoDB table.

        Args:
            key (str): In DynamoDB it is a 'resource_id' property in the table.
            item (dict): Item to be put in DynamoDB table.
        """
        try:
            table_item = {
                "resource_id": key,
                **item,
            }
            # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/table/put_item.html
            response = self.table.put_item(Item=table_item)
            self.logger.debug(f"put_item response: {to_json(response)}")
            return response
        except ClientError as e:
            raise CloudProviderException(e, f"Error putting item in DynamoDB table: {str(e)}")

    def delete(self, key: str) -> bool:
        """Delete item from DynamoDB table.

        Args:
            key (str): Resource ID that uniquely identifies the resource.
        """
        try:
            # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/table/delete_item.html
            response = self.table.delete_item(Key={"resource_id": key})
            self.logger.debug(f"delete_item response: {to_json(response)}")
            return True
        except ClientError as e:
            raise CloudProviderException(e, f"Error deleting item from DynamoDB table: {str(e)}")
