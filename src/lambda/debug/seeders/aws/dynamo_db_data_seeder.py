import base64
import json
import os
from typing import Any

import boto3
from mypy_boto3_dynamodb import DynamoDBServiceResource
from mypy_boto3_dynamodb.service_resource import Table

from . import constants


class DynamoDBDataSeeder:

    def __init__(
        self,
        table_name: str = "test-table",
        db_config_iac_item_key_id: str = "sg-dns-discovery-iac-config",
        db_config_external_item_key_id: str = "sg-dns-discovery-external-config ",
    ):
        self.table_name = table_name
        self.db_config_iac_item_key_id = db_config_iac_item_key_id
        self.db_config_external_item_key_id = db_config_external_item_key_id
        self.dynamodb: DynamoDBServiceResource = boto3.resource("dynamodb")  # type: ignore
        # Check whether the table exists, and if not - create it
        if table_name not in [table.name for table in self.dynamodb.tables.all()]:
            self.dynamodb.create_table(
                TableName=table_name,
                BillingMode="PAY_PER_REQUEST",
                KeySchema=[
                    {"AttributeName": "id", "KeyType": "HASH"},
                ],
                AttributeDefinitions=[
                    {"AttributeName": "id", "AttributeType": "S"},
                ],
            )
        self.table: Table = self.dynamodb.Table(table_name)

    def patch_environment(self) -> None:
        """Patches the environment to allow for the data to be seeded."""
        # Mocks the environment variables to use DynamoDB (see ~/lambda-shared.tf -> lambda_envrionment_variables)
        os.environ["db_provider"] = "dynamodb"
        os.environ["db_table_name"] = self.table_name
        os.environ["db_config_iac_item_key_id"] = self.db_config_iac_item_key_id
        os.environ["db_config_external_item_key_id"] = self.db_config_external_item_key_id

    def seed_default_data(self) -> Any:
        # Records to insert

        # Pretty much all-default record for Auto-scaling group, as defined in variables.tf
        records = [
            {
                "scaling_group_name": "test-asg",
                "multiple_config_proceed_mode": "ALL_OPERATIONAL",
                "dns_config": {
                    "provider": "route53",
                    "mode": "MULTIVALUE",
                    "empty_mode": "KEEP",
                    "value_source": "ip:v4:private",
                    "dns_zone_id": "Z1234567890",
                    "record_name": "test-asg",
                    "record_ttl": 60,
                    "record_type": "A",
                    "srv_priority": 0,
                    "srv_weight": 0,
                    "srv_port": 0,
                },
                "readiness": {
                    "enabled": True,
                    "tag_key": constants.EC2_INSTANCE_READY_TAG_KEY,
                    "tag_value": constants.EC2_INSTANCE_READY_TAG_VALUE,
                    "timeout_seconds": 300,
                    "interval_seconds": 5,
                },
                "health_check": {
                    "enabled": True,
                    "endpoint_source": "ip:private",
                    "port": 80,
                    "protocol": "HTTP",
                    "path": "/index.html",
                    "timeout_seconds": 5,
                },
            },
        ]

        # Base64 encode
        records_json = json.dumps(records)
        records_base64 = base64.b64encode(records_json.encode("utf-8"))
        self.table.put_item(Item={"id": self.db_config_iac_item_key_id, "config": records_base64})

        return records
