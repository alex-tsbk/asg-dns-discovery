from dataclasses import dataclass, field

import boto3
from debug.seeders.aws.networking_seeder import NetworkingSeederResponse
from mypy_boto3_autoscaling import AutoScalingClient
from mypy_boto3_ec2 import EC2Client

from . import constants


@dataclass
class Ec2DataSeederState:
    # Dictionary where key is scaling group name and value is list of instance ids
    scaling_groups: dict[str, list[str]] = field(default_factory=dict)


class Ec2DataSeeder:
    def __init__(self):
        self.ec2_client: EC2Client = boto3.client("ec2")  # type: ignore
        self.asg_client: AutoScalingClient = boto3.client("autoscaling")  # type: ignore
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

        # Attach instances to auto-scaling groups
        for asg, instances in seeded_data.scaling_groups.items():
            # Attach instances to auto-scaling group
            self.asg_client.attach_instances(
                AutoScalingGroupName=asg,
                InstanceIds=instances,
            )

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

        shared_state.scaling_groups[asg_name] = []

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
                    ],
                },
            ],
        )
        instance_id = create_result["Instances"][0]["InstanceId"]
        shared_state.scaling_groups[asg_name].append(instance_id)

        return instance_id
