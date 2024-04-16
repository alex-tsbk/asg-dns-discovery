from __future__ import annotations

from typing import TYPE_CHECKING, Any, Sequence

import boto3
from app.infrastructure.aws import boto_config
from app.utils.exceptions import CloudProviderException
from app.utils.logging import get_logger
from app.utils.singleton import Singleton
from botocore.exceptions import ClientError

if TYPE_CHECKING:
    from mypy_boto3_ec2 import DescribeInstancesPaginator
    from mypy_boto3_ec2.client import EC2Client
    from mypy_boto3_ec2.type_defs import InstanceTypeDef


class AwsEc2Service(metaclass=Singleton):
    """Service class for interacting with EC2."""

    def __init__(self):
        self.logger = get_logger()
        self.ec2_client: EC2Client = boto3.client("ec2", config=boto_config.CONFIG)  # type: ignore
        self.ec2_describe_instances_paginator: DescribeInstancesPaginator = self.ec2_client.get_paginator(
            "describe_instances"
        )

    def get_instance(self, instance_id: str) -> InstanceTypeDef | None:
        """Gets EC2 instance by instance ID

        Args:
            instance_id (str): EC2 instance ID

        Raises:
            CloudProviderException: When underlying Boto3 client raises an exception

        Returns:
            InstanceTypeDef: EC2 instance object
        """
        instances: list[InstanceTypeDef] = self.get_instances([instance_id])
        return next(filter(lambda i: i.get("InstanceId", "") == instance_id, instances), None)

    def get_instances(self, instance_ids: Sequence[str]) -> list[InstanceTypeDef]:
        """Gets EC2 instances by instance IDs

        Args:
            instance_ids (list[str]): List of EC2 instance IDs

        Raises:
            CloudProviderException: When underlying Boto3 client raises an exception

        Returns:
            list[InstanceTypeDef]: List of EC2 instance objects
        """
        instances: list[InstanceTypeDef] = []
        kwargs: dict[str, Any] = {"InstanceIds": instance_ids}

        try:
            for page in self.ec2_describe_instances_paginator.paginate(**kwargs):
                for resource in page["Reservations"]:
                    instances.extend(resource["Instances"])
        except ClientError as e:
            raise CloudProviderException(e, f"Boto3 error while fetching instances with ids {instance_ids}: {e}")
        return instances
