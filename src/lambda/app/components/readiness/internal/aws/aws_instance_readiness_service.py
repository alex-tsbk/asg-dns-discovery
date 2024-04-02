from typing import TYPE_CHECKING

from app.components.readiness.instance_readiness_interface import InstanceReadinessInterface
from app.components.readiness.models.readiness_result_model import ReadinessResultModel
from app.config.models.readiness_config import ReadinessConfig
from app.infrastructure.aws.ec2_service import AwsEc2Service
from app.utils.logging import get_logger

if TYPE_CHECKING:
    from mypy_boto3_ec2.service_resource import Instance


class AwsInstanceReadinessService(InstanceReadinessInterface):
    """AWS EC2 Instance Readiness service implementation."""

    def __init__(self, ec2_service: AwsEc2Service) -> None:
        self.logger = get_logger()
        self.ec2_service = ec2_service

    def is_ready(self, instance_id: str, readiness_config: ReadinessConfig) -> ReadinessResultModel:
        """Checks whether the instance is ready
        Args:
            instance_id (str): Instance ID
            readiness_config (ReadinessConfig): Readiness configuration

        Returns:
            ReadinessResultModel: Model representing the readiness result
        """
        if not readiness_config.enabled:
            return True

        instance: Instance = self.ec2_service.get_instance(instance_id)
        if not instance:
            return False

        tag_key = readiness_config.tag_key
        tag_value = readiness_config.tag_value
        tag_match = self._match_tag(tag_key, tag_value, instance.tags)

        return tag_match is not None

    @staticmethod
    def _match_tag(tag_key: str, tag_value: str, tags: list[dict]) -> dict | None:
        """Finds tag by key and ensures value match in list of tags.

        Args:
            tag_key (str): Tag key
            tag_value (str): Tag value
            tags (list[dict]): List of tags
                [
                    {
                        "Key": "Name",
                        "Value": "my-instance"
                    },
                    ...
                ]

        Returns:
            dict: Tag object if found, None otherwise
        """
        return next(
            filter(lambda t: t["Key"] == tag_key and t["Value"] == tag_value, tags),
            None,
        )
