from __future__ import annotations

from typing import TYPE_CHECKING

from app.components.discovery.instance_discovery_interface import InstanceDiscoveryInterface
from app.domain.models.instance_model import InstanceMetadataModel, InstanceModel, InstanceTagModel
from app.domain.models.scaling_group_model import ScalingGroupModel
from app.infrastructure.aws.ec2_asg_service import AwsEc2AutoScalingService
from app.infrastructure.aws.ec2_service import AwsEc2Service
from app.utils.logging import get_logger

if TYPE_CHECKING:
    from mypy_boto3_ec2.type_defs import InstanceTypeDef as InstanceTypeDef


class AwsInstanceDiscoveryService(InstanceDiscoveryInterface):
    """Service for discovering and collecting required information on
    EC2 instances in AWS together with their metadata."""

    def __init__(self, aws_ec2_service: AwsEc2Service, aws_asg_service: AwsEc2AutoScalingService):
        self.logger = get_logger()
        self.aws_ec2_service = aws_ec2_service
        self.aws_asg_service = aws_asg_service

    def describe_instances(self, *instances_ids: str) -> list[InstanceModel]:
        """Describe the instances with the given IDs.

        Args:
            *instances_ids (str): The IDs of the instances to describe.

        Returns:
            list[InstanceModel]: Models describing the instances.
        """
        # We'll store the instances models in a dictionary for fast lookup
        instances_models: dict[str, InstanceModel] = {}
        # Pencil down the scaling group names to describe them later
        auto_scaling_group_names: set[str] = set()
        # Collect EC2 instances information
        aws_instances = self.aws_ec2_service.get_instances(instances_ids)
        for aws_instance in aws_instances:
            instance_model = self._build_instance_model(aws_instance)
            if not instance_model.scaling_group_name:  # Ensure instance belongs to a scaling group
                self.logger.warning(f"Instance {instance_model.instance_id} does not belong to any scaling group.")
                continue
            # Add the scaling group name to the set so we can describe them later in single call
            auto_scaling_group_names.add(instance_model.scaling_group_name)
            instances_models[instance_model.instance_id] = instance_model

        # Collect Auto Scaling Group instances information
        scaling_groups = self.aws_asg_service.describe_instances(
            auto_scaling_group_names=list(auto_scaling_group_names)
        )
        for _, scaling_group_instances in scaling_groups.items():
            for aws_asg_instance in scaling_group_instances:
                instance_model = instances_models.get(aws_asg_instance["InstanceId"])
                if not instance_model:
                    continue
                # Backfill missing data only
                instance_model.lifecycle_state = aws_asg_instance["LifecycleState"]

        # Build result list
        result = list(instances_models.values())
        return result

    def describe_scaling_groups(self, *scaling_groups_names: str) -> list[ScalingGroupModel]:
        """Get the instances in the scaling group.

        Args:
            *scaling_groups_names (str): The names of the scaling groups to describe.

        Returns:
            list[ScalingGroupModel]: Models describing the instances.
        """
        # We'll store the instances models in a dictionary for fast lookup
        instances_models: dict[str, InstanceModel] = {}
        # Collect Auto Scaling Group instances information
        scaling_groups = self.aws_asg_service.describe_instances(
            auto_scaling_group_names=list(scaling_groups_names),
        )
        for scaling_group_name, scaling_group_instances in scaling_groups.items():
            for aws_asg_instance in scaling_group_instances:
                instance_model = InstanceModel(
                    instance_id=aws_asg_instance["InstanceId"],
                    scaling_group_name=scaling_group_name,
                    lifecycle_state=aws_asg_instance["LifecycleState"],
                )
                instances_models[instance_model.instance_id] = instance_model

        # Collect EC2 instances information
        ec2_instances_ids = list(set(instances_models.keys()))
        aws_instances: list[InstanceTypeDef] = self.aws_ec2_service.get_instances(ec2_instances_ids)
        for aws_instance in aws_instances:
            instance_model = instances_models.get(aws_instance["InstanceId"])
            if not instance_model:
                continue
            # Backfill missing data only
            instance_model.instance_state = aws_instance.get("State", {}).get("Name", "")
            instance_model.instance_launch_timestamp = int(aws_instance["LaunchTime"].timestamp())
            self._fill_instance_metadata(instance_model, aws_instance)
            self._fill_instance_tags(instance_model, aws_instance)

        # Build result
        result: dict[str, ScalingGroupModel] = {}
        for instance in instances_models.values():
            if instance.scaling_group_name not in result:
                result[instance.scaling_group_name] = ScalingGroupModel(scaling_group_name=instance.scaling_group_name)
            result[instance.scaling_group_name].instances.append(instance)
        return list(result.values())

    @classmethod
    def _build_instance_model(cls, aws_instance_info: InstanceTypeDef) -> InstanceModel:
        """Builds an Instance Model from AWS Instance information.

        Args:
            aws_instance_info (InstanceTypeDef): AWS instance information.

        Returns:
            InstanceModel: Model containing the instance information.
        """
        instance_id = aws_instance_info.get("InstanceId", "")
        auto_scaling_group_name = next(
            (tag["Value"] for tag in aws_instance_info["Tags"] if tag["Key"] == "aws:autoscaling:groupName"), ""
        )
        instance = InstanceModel(
            instance_id=instance_id,
            scaling_group_name=auto_scaling_group_name,
            instance_state=aws_instance_info["State"]["Name"],
            instance_launch_timestamp=int(aws_instance_info["LaunchTime"].timestamp()),
        )
        cls._fill_instance_metadata(instance, aws_instance_info)
        cls._fill_instance_tags(instance, aws_instance_info)
        return instance

    @staticmethod
    def _fill_instance_metadata(instance: InstanceModel, aws_instance_info: InstanceTypeDef):
        """Fetches instance metadata from AWS instance information and updates the instance model.

        Args:
            instance (InstanceModel): Instance model to update.
            aws_instance_info (InstanceTypeDef): AWS instance information.
        """
        instance.metadata = InstanceMetadataModel(
            public_ip_v4=aws_instance_info.get("PublicIpAddress", ""),
            private_ip_v4=aws_instance_info.get("PrivateIpAddress", ""),
            public_dns=aws_instance_info.get("PublicDnsName", ""),
            private_dns=aws_instance_info.get("PrivateDnsName", ""),
            # In AWS IPv6 already is global unique address,
            # so we don't need to check if it's public or private.
            # Might not be the case for other cloud providers though.
            public_ip_v6=aws_instance_info.get("Ipv6Address", ""),
            private_ip_v6=aws_instance_info.get("Ipv6Address", ""),
        )

    @staticmethod
    def _fill_instance_tags(instance: InstanceModel, aws_instance_info: InstanceTypeDef):
        """Fetches instance tags from AWS instance information and updates the instance model.

        Args:
            instance (InstanceModel): Instance model to update.
            aws_instance_info (InstanceTypeDef): AWS instance information.
        """
        instance.tags = [InstanceTagModel(key=tag["Key"], value=tag["Value"]) for tag in aws_instance_info["Tags"]]
