from dataclasses import dataclass, field
from typing import Iterable, Sequence

import boto3
from app.components.concurrency.internal.concurrent_task_scheduler import ConcurrentTaskScheduler
from debug.aws.seeders import constants
from debug.aws.seeders.networking_seeder import NetworkingSeederResponse
from debug.utils import with_delay
from mypy_boto3_autoscaling import AutoScalingClient
from mypy_boto3_ec2 import EC2Client


@dataclass
class Ec2InfoModel:
    """Model representing EC2 instance information."""

    instance_id: str
    instance_ipv4_private: str = field(default="")


@dataclass
class AsgInfoModel:
    """Model representing ASG information."""

    asg_name: str
    instances: list[Ec2InfoModel] = field(default_factory=list)

    @property
    def instance_ids(self) -> Sequence[str]:
        return [instance.instance_id for instance in self.instances]


@dataclass
class Ec2DataSeederState:
    # Dictionary where key is scaling group name and value is AsgInfoModel
    scaling_groups: dict[str, AsgInfoModel] = field(default_factory=dict)


class Ec2DataSeeder:
    def __init__(self):
        self.ec2_client: EC2Client = boto3.client("ec2")  # type: ignore
        self.asg_client: AutoScalingClient = boto3.client("autoscaling")  # type: ignore
        # We'll use this internally to schedule updating ec2 tags in 5 seconds in the future
        self.task_scheduler = ConcurrentTaskScheduler()
        # Set some default that we don't explicitly use,
        # thus care very little about
        self.launch_configuration_name = "test-lc"

    def seed_data_for_sg_lch(self, networking_info: NetworkingSeederResponse) -> Ec2DataSeederState:
        """Seeds data for ASG lifecycle hook.

        Returns:
            Ec2DataSeederState: The response containing the seeded data.
        """
        seeded_data = Ec2DataSeederState()

        self.__create_launch_configuration(networking_info)

        # Provision data for Primary ASG
        self.__create_auto_scaling_group(constants.ASG_PRIMARY, networking_info, seeded_data)
        # Seed 2 instances in the auto-scaling group
        self.__create_instance_in_auto_scaling_group(constants.ASG_PRIMARY, networking_info, seeded_data)
        self.__create_instance_in_auto_scaling_group(constants.ASG_PRIMARY, networking_info, seeded_data)

        # Provision data for Secondary ASG
        self.__create_auto_scaling_group(constants.ASG_SECONDARY, networking_info, seeded_data)
        # Seed 2 instances in the auto-scaling group
        self.__create_instance_in_auto_scaling_group(constants.ASG_SECONDARY, networking_info, seeded_data)
        self.__create_instance_in_auto_scaling_group(constants.ASG_SECONDARY, networking_info, seeded_data)

        # Schedule updating ec2 instances tags in 10 seconds in the future, so code can progress to handling 'readiness'
        self.task_scheduler.place(
            self.__mark_instance_ready, seeded_data.scaling_groups[constants.ASG_PRIMARY].instance_ids
        )

        # Attach instances to auto-scaling groups
        for asg_info in seeded_data.scaling_groups.values():
            # Attach instances to auto-scaling group
            self.asg_client.attach_instances(
                AutoScalingGroupName=asg_info.asg_name,
                InstanceIds=asg_info.instance_ids,
            )

        self.task_scheduler

        return seeded_data

    def __create_launch_configuration(self, networking_info: NetworkingSeederResponse):
        self.asg_client.create_launch_configuration(
            LaunchConfigurationName=self.launch_configuration_name,
            ImageId="ami-0c55b159cbfafe1f0",
            InstanceType="t2.micro",
            KeyName=networking_info.ec2_key_name,
            SecurityGroups=[networking_info.security_group_id],
        )

    def __create_auto_scaling_group(
        self, asg_name: str, networking_info: NetworkingSeederResponse, shared_state: Ec2DataSeederState
    ):
        """Creates an auto-scaling group with a single instance in it."""
        self.asg_client.create_auto_scaling_group(
            AutoScalingGroupName=asg_name,
            LaunchConfigurationName=self.launch_configuration_name,
            MinSize=0,
            MaxSize=2,
            VPCZoneIdentifier=networking_info.subnet_id,
        )

        shared_state.scaling_groups[asg_name] = AsgInfoModel(asg_name=asg_name)

    def __create_instance_in_auto_scaling_group(
        self, asg_name: str, networking_info: NetworkingSeederResponse, shared_state: Ec2DataSeederState
    ) -> str:
        """Creates an instance in the auto-scaling group.

        Returns:
            str: The instance ID of the created instance.
        """

        # Create EC2 instance in the auto-scaling group
        create_result = self.ec2_client.run_instances(
            ImageId="ami-0c55b159cbfafe1f0",
            MinCount=1,
            MaxCount=1,
            InstanceType="t2.micro",
            KeyName=networking_info.ec2_key_name,
            SecurityGroupIds=[networking_info.security_group_id],
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": [
                        {"Key": "Name", "Value": "test-instance"},
                        {"Key": "dns_cname", "Value": "www.python.org"},
                    ],
                },
            ],
        )
        instance_id: str = create_result["Instances"][0]["InstanceId"]
        instace_ipv4 = create_result["Instances"][0]["PrivateIpAddress"]
        shared_state.scaling_groups[asg_name].instances.append(
            Ec2InfoModel(
                instance_id=instance_id,
                instance_ipv4_private=instace_ipv4,
            )
        )

        return instance_id

    @with_delay(10)
    def __mark_instance_ready(self, instance_ids: Iterable[str]):
        """Updates the instance tags to mark them as ready. To simulate real environment, we'll delay this by 10 seconds.

        Args:
            instance_ids (Iterable[str]): The instance IDs to mark as ready.
        """
        self.ec2_client.create_tags(
            Resources=list(instance_ids),
            Tags=[
                {
                    "Key": constants.EC2_INSTANCE_READY_TAG_KEY,
                    "Value": constants.EC2_INSTANCE_READY_TAG_VALUE,
                },
            ],
        )
