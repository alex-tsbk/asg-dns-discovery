from __future__ import annotations

from typing import TYPE_CHECKING

import boto3
from app.infrastructure.aws import boto_config
from app.utils.exceptions import CloudProviderException
from app.utils.logging import get_logger
from app.utils.singleton import Singleton
from botocore.exceptions import ClientError

if TYPE_CHECKING:
    from mypy_boto3_ec2.client import EC2Client
    from mypy_boto3_ec2.type_defs import DescribeInstancesResultTypeDef, InstanceTypeDef
    from mypy_boto3_ec2.service_resource import EC2ServiceResource, Instance


class AwsEc2Service(metaclass=Singleton):
    """Service class for interacting with EC2."""

    def __init__(self):
        self.logger = get_logger()
        self.ec2_client: EC2Client = boto3.client("ec2", config=boto_config.CONFIG)
        self.ec2_resource: EC2ServiceResource = boto3.resource("ec2", config=boto_config.CONFIG)

    def get_instance(self, instance_id: str) -> InstanceTypeDef:
        """Gets EC2 instance by instance ID

        Args:
            instance_id (str): EC2 instance ID

        Raises:
            CloudProviderException: When underlying Boto3 client raises an exception

        Returns:
            InstanceTypeDef: EC2 instance object
        """
        instances = self.get_instances([instance_id])
        return next(filter(lambda i: i["InstanceId"] == instance_id, instances), None)

    def get_instances(self, instance_ids: list[str]) -> list[InstanceTypeDef]:
        """Gets EC2 instances by instance IDs

        Args:
            instance_ids (list[str]): List of EC2 instance IDs

        Raises:
            CloudProviderException: When underlying Boto3 client raises an exception

        Returns:
            list[InstanceTypeDef]: List of EC2 instance objects
        """
        try:
            response: DescribeInstancesResultTypeDef = self.ec2_client.describe_instances(InstanceIds=instance_ids)
        except ClientError as e:
            raise CloudProviderException(e, f"Boto3 error while fetching instances with ids {instance_ids}: {e}")
        instances: list[InstanceTypeDef] = response["Reservations"][0]["Instances"]
        return instances

    def get_instance_resource(self, instance_id: str) -> Instance:
        """Returns EC2 instance resource object by instance ID

        Args:
            instance_id [str]: EC2 instance ID

        Returns:
            EC2Instance: EC2 instance object
        """
        try:
            return self.ec2_resource.Instance(instance_id)
        except ClientError as e:
            if e.response["Error"]["Code"] == "InvalidInstanceID.NotFound":
                raise CloudProviderException(e, f"EC2 instance with ID {instance_id} not found")
            raise CloudProviderException(e, f"Boto3 error while fetching instance with id {instance_id}: {e}")

    def get_instances_resources(self, instance_ids: list[str]) -> list[Instance]:
        """Returns EC2 instance objects by instance IDs

        Args:
            instance_ids [list[str]]: EC2 instance IDs

        Returns:
            list[EC2Instance]: List of EC2 instance resource objects
        """
        return [self.ec2_resource.Instance(instance_id) for instance_id in instance_ids]
