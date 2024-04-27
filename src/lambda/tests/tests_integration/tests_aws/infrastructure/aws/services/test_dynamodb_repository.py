import os
from unittest.mock import patch

import boto3
import pytest
from app.infrastructure.aws.services.dynamodb_repository import DynamoDbTableRepository
from app.utils.exceptions import CloudProviderException
from botocore.exceptions import ClientError
from moto import mock_aws


@pytest.fixture(scope="function")
def create_dynamodb_table(aws):
    boto3.client("dynamodb").create_table(
        TableName="test_table",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
    )


@pytest.fixture(scope="function")
def dynamodb_repository(aws):
    yield DynamoDbTableRepository("test_table")


@pytest.fixture(scope="function")
def dynamodb_repository_with_error(dynamodb_repository):

    def raise_throttling_exception(*args, **kwargs):
        error_response = {"Error": {"Code": "ProvisionedThroughputExceededException", "Message": "Rate exceeded"}}
        raise ClientError(error_response, "GetItem")

    with patch.object(dynamodb_repository.table, "get_item", side_effect=raise_throttling_exception), \
         patch.object(dynamodb_repository.table, "put_item", side_effect=raise_throttling_exception), \
         patch.object(dynamodb_repository.table, "delete_item", side_effect=raise_throttling_exception):  # fmt: skip
        yield dynamodb_repository


def test_dynamodb_repository_should_create_item(create_dynamodb_table, dynamodb_repository):
    dynamodb_repository.create("key", {"name": "test"})

    item = boto3.client("dynamodb").get_item(TableName="test_table", Key={"id": {"S": "key"}})

    assert item is not None, "Item not found in DynamoDB table"
    assert item["Item"]["name"]["S"] == "test", "Item name does not match"


def test_dynamodb_repository_should_get_item(create_dynamodb_table, dynamodb_repository):
    boto3.client("dynamodb").put_item(TableName="test_table", Item={"id": {"S": "key"}, "name": {"S": "test"}})

    item = dynamodb_repository.get("key")

    assert item is not None, "Item not found in DynamoDB table"
    assert item["name"] == "test", "Item name does not match"


def test_dynamodb_repository_should_return_empty_dict_when_item_not_found(create_dynamodb_table, dynamodb_repository):
    item = dynamodb_repository.get("key")

    assert item == {}, "Item should be empty dict when not found in DynamoDB table"


def test_dynamodb_repository_should_put_item(create_dynamodb_table, dynamodb_repository):
    dynamodb_repository.put("key", {"name": "test"})

    item = boto3.client("dynamodb").get_item(TableName="test_table", Key={"id": {"S": "key"}})

    assert item is not None, "Item not found in DynamoDB table"
    assert item["Item"]["name"]["S"] == "test", "Item name does not match"


def test_dynamic_repository_should_delete_item(create_dynamodb_table, dynamodb_repository):
    boto3.client("dynamodb").put_item(TableName="test_table", Item={"id": {"S": "key"}, "name": {"S": "test"}})

    dynamodb_repository.delete("key")

    item = boto3.client("dynamodb").get_item(TableName="test_table", Key={"id": {"S": "key"}})

    assert item.get("Item", None) is None, "Item should be deleted from DynamoDB table"


def test_dynamodb_repository_get_item_should_raise_exception_when_error_occurs(
    create_dynamodb_table, dynamodb_repository_with_error
):
    with pytest.raises(CloudProviderException):
        dynamodb_repository_with_error.get("key")  # This should raise an exception because item does not exist


def test_dynamodb_repository_put_item_should_raise_exception_when_error_occurs(
    create_dynamodb_table, dynamodb_repository_with_error
):
    with pytest.raises(CloudProviderException):
        dynamodb_repository_with_error.put(
            "key", {"name": "test"}
        )  # This should raise an exception because of throttling


def test_dynamodb_repository_delete_item_should_raise_exception_when_error_occurs(
    create_dynamodb_table, dynamodb_repository_with_error
):
    with pytest.raises(CloudProviderException):
        dynamodb_repository_with_error.delete("key")  # This should raise an exception because item does not exist


def test_dynamodb_repository_create_item_should_raise_exception_when_error_occurs(
    create_dynamodb_table, dynamodb_repository_with_error
):
    with pytest.raises(CloudProviderException):
        dynamodb_repository_with_error.create(
            "key", {"name": "test"}
        )  # This should raise an exception because of throttling
