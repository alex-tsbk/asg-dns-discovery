from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

import boto3
from app.infrastructure.aws import boto_config
from app.utils.exceptions import CloudProviderException
from app.utils.logging import get_logger
from app.utils.serialization import to_json
from app.utils.singleton import Singleton
from botocore.exceptions import ClientError

if TYPE_CHECKING:
    from mypy_boto3_autoscaling.client import AutoScalingClient
    from mypy_boto3_autoscaling.type_defs import FilterTypeDef


class AwsEc2AutoScalingService(metaclass=Singleton):
    """Service class for interacting with AWS EC2 Auto-Scaling Groups."""

    def __init__(self):
        self.logger = get_logger()
        self.autoscaling_client: AutoScalingClient = boto3.client("autoscaling", config=boto_config.CONFIG)

    def list_ec2_instances(
        self,
        autoscaling_group_names: list[str],
        scaling_group_valid_states: list[str] = None,
        tag_filters: Sequence[FilterTypeDef] = None,
    ) -> dict[str, list[dict]]:
        """Lists the running EC2 instances in the Auto-Scaling Groups.

        For more information please visit:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/autoscaling.html#AutoScaling.Client.describe_auto_scaling_groups

        Args:
            autoscaling_group_names [list[str]]: The names of the Auto Scaling groups.
            scaling_group_valid_states [list[str]]: A list of lifecycle states to filter the results.
                Example: for instance launching valid states could be:
                    ['Pending', 'Pending:Wait', 'Pending:Proceed', 'InService', ]
            tag_filters [list[dict]]: A list of tag filters to apply to the query.

        Returns:
            dict[str, list[dict]]: A dictionary with the ASG name as the key and a list of EC2 instances containing metadata values.

                Example: {
                    "ASG-1": [
                        {
                            "instance_id": "i-1234567890abcdef0",
                            "lifecycle_state": "InService",
                            "launch_time": "2021-10-01T12:00:00Z"
                        }
                    ],
                    "ASG-2": [
                        {
                            "instance_id": "i-1234567890abcdef1",
                            "lifecycle_state": "InService",
                            "launch_time": "2021-10-01T12:00:00Z"
                        }
                    ],
                    ...
                }

        Raises:
            CloudProviderException: When call fails to underlying boto3 function
        """
        kwargs = {"AutoScalingGroupNames": autoscaling_group_names}
        if tag_filters:
            kwargs["Filters"] = list(tag_filters)

        asg_ec2_instances: dict[str, list[dict]] = {}

        # Get paginator and iterate through the results
        try:
            # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/autoscaling/client/describe_auto_scaling_groups.html
            paginator = self.autoscaling_client.get_paginator("describe_auto_scaling_groups")
            iterable = paginator.paginate(**kwargs)
            for page in iterable:
                self.logger.debug(f"list_running_ec2_instances page: {to_json(page)}")
                if not page.get("AutoScalingGroups", None):
                    break
                for asg in page["AutoScalingGroups"]:
                    asg_name = asg["AutoScalingGroupName"]
                    asg_ec2_instances[asg_name] = []
                    # Collect instances
                    for instance in asg["Instances"]:
                        if scaling_group_valid_states and instance["LifecycleState"] not in scaling_group_valid_states:
                            continue
                        asg_ec2_instances[asg_name].append(
                            dict(
                                instance_id=instance["InstanceId"],
                                # 'Pending'|'Pending:Wait'|'Pending:Proceed'|'Quarantined'|'InService'|
                                # 'Terminating'|'Terminating:Wait'|'Terminating:Proceed'|'Terminated'|
                                # 'Detaching'|'Detached'|'EnteringStandby'|'Standby'|
                                # 'Warmed:Pending'|'Warmed:Pending:Wait'|'Warmed:Pending:Proceed'|
                                # 'Warmed:Terminating'|'Warmed:Terminating:Wait'|'Warmed:Terminating:Proceed'|
                                # 'Warmed:Terminated'|'Warmed:Stopped'|'Warmed:Running'|'Warmed:Hibernated'
                                lifecycle_state=instance["LifecycleState"],
                                launch_time=instance["LaunchTime"],
                            )
                        )
        except ClientError as e:
            raise CloudProviderException(e, f"Error listing ASG running EC2 instances: {str(e)}")

        return asg_ec2_instances

    def complete_lifecycle_action(
        self,
        lifecycle_hook_name: str,
        autoscaling_group_name: str,
        lifecycle_action_token: str,
        lifecycle_action_result: str,
        ec2_instance_id: str,
    ) -> None:
        """Completes the lifecycle action for the ASG.

        For more information please visit:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/autoscaling.html#AutoScaling.Client.complete_lifecycle_action

        Args:
            lifecycle_hook_name [str]: The name of the lifecycle hook.

            autoscaling_group_name [str]: The name of the Auto Scaling group.

            lifecycle_action_token [str]: UUID identifying a specific lifecycle action associated with an instance.
                ASG sends this token to the SNS specified when LCH is created.

            lifecycle_action_result [str]: The action for the group to take. This parameter can be either CONTINUE or ABANDON .

            ec2_instance_id [str]: EC2 instance ID.

        Raises:
            CloudProviderException: When call fails to underlying boto3 function
        """
        try:
            response = self.autoscaling_client.complete_lifecycle_action(
                LifecycleHookName=lifecycle_hook_name,
                AutoScalingGroupName=autoscaling_group_name,
                LifecycleActionToken=lifecycle_action_token,
                LifecycleActionResult=lifecycle_action_result,
                InstanceId=ec2_instance_id,
            )
            self.logger.debug(f"complete_lifecycle_action response: {to_json(response)}")
        except ClientError as e:
            raise CloudProviderException(e, f"Error completing lifecycle action: {str(e)}")
