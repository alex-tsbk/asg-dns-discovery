from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, ClassVar, Sequence

import boto3
from app.infrastructure.aws import boto_config
from app.utils.exceptions import CloudProviderException
from app.utils.logging import get_logger
from app.utils.serialization import to_json
from app.utils.singleton import Singleton
from botocore.exceptions import ClientError

if TYPE_CHECKING:
    from mypy_boto3_autoscaling.client import AutoScalingClient
    from mypy_boto3_autoscaling.type_defs import FilterTypeDef, InstanceTypeDef


class Ec2AutoScalingService(metaclass=Singleton):
    """Service class for interacting with AWS EC2 Auto-Scaling Groups."""

    autoscaling_client: ClassVar[AutoScalingClient] = boto3.client("autoscaling", config=boto_config.CONFIG)  # type: ignore

    def __init__(self):
        self.logger = get_logger()

    def describe_instances(
        self,
        *,
        auto_scaling_group_names: list[str],
        tag_filters: Sequence[FilterTypeDef] | None = None,
    ) -> dict[Annotated[str, "ASG Name"], Sequence[InstanceTypeDef]]:
        """Lists the running EC2 instances in the Auto-Scaling Groups.

        For more information please visit:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/autoscaling.html#AutoScaling.Client.describe_auto_scaling_groups

        Args:
            auto_scaling_group_names [list[str]]: The names of the Auto Scaling groups.
            tag_filters [list[dict]]: A list of tag filters to apply to the query.

        Returns:
            dict[Annotated[str, "ASG Name"], Sequence[InstanceTypeDef]]: A dictionary with the ASG name as the key and a list of EC2 instances containing metadata values.
                Example:
                ```python
                {
                    "ASG-1": [
                        {
                            "InstanceId": str,
                            "AvailabilityZone": str,
                            "LifecycleState": LifecycleStateType,
                            "HealthStatus": str,
                            "ProtectedFromScaleIn": bool,
                            "InstanceType": NotRequired[str],
                            "LaunchConfigurationName": NotRequired[str],
                            "LaunchTemplate": NotRequired[LaunchTemplateSpecificationTypeDef],
                            "WeightedCapacity": NotRequired[str],
                        },
                        ...
                    ],
                    "ASG-2": [
                        ...
                    ],
                    ...
                }
                ```

        Raises:
            CloudProviderException: When call fails to underlying boto3 function
        """
        kwargs: dict[str, Any] = {"AutoScalingGroupNames": auto_scaling_group_names}
        if tag_filters:
            kwargs["Filters"] = list(tag_filters)

        asg_ec2_instances: dict[Annotated[str, "ASG Name"], Sequence[InstanceTypeDef]] = {}

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
                    asg_ec2_instances[asg["AutoScalingGroupName"]] = asg["Instances"]
        except ClientError as e:
            raise CloudProviderException(e, f"Error listing ASG running EC2 instances: {str(e)}")

        return asg_ec2_instances

    def complete_lifecycle_action(
        self,
        *,  # Enforce keyword-only arguments
        lifecycle_hook_name: str,
        autoscaling_group_name: str,
        lifecycle_action_token: str,
        lifecycle_action_result: str,
        instance_id: str,
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

            instance_id [str]: EC2 instance ID.

        Raises:
            CloudProviderException: When call fails to underlying boto3 function
        """
        try:
            response = self.autoscaling_client.complete_lifecycle_action(
                LifecycleHookName=lifecycle_hook_name,
                AutoScalingGroupName=autoscaling_group_name,
                LifecycleActionToken=lifecycle_action_token,
                LifecycleActionResult=lifecycle_action_result,
                InstanceId=instance_id,
            )
            self.logger.debug(f"complete_lifecycle_action response: {to_json(response)}")
        except ClientError as e:
            raise CloudProviderException(e, f"Error completing lifecycle action: {str(e)}")
