from typing import Any, Iterable, Mapping

from app.components.readiness.instance_readiness_interface import InstanceReadinessInterface
from app.components.readiness.models.readiness_result_model import ReadinessResultModel
from app.config.models.readiness_config import ReadinessConfig
from app.infrastructure.aws.services.ec2_service import Ec2Service
from app.utils.logging import get_logger


class AwsInstanceReadinessService(InstanceReadinessInterface):
    """AWS EC2 Instance Readiness service implementation."""

    def __init__(self, aws_ec2_service: Ec2Service) -> None:
        self.logger = get_logger()
        self.aws_ec2_service = aws_ec2_service

    def is_ready(self, instance_id: str, readiness_config: ReadinessConfig) -> ReadinessResultModel:
        """Checks whether the instance is ready
        Args:
            instance_id (str): Instance ID
            readiness_config (ReadinessConfig): Readiness configuration

        Returns:
            ReadinessResultModel: Model representing the readiness result
        """
        readiness_model = ReadinessResultModel(
            instance_id=instance_id,
        )

        if not readiness_config.enabled:
            readiness_model.ready = True
            return readiness_model

        instance = self.aws_ec2_service.get_instance(instance_id)
        if instance is None:
            readiness_model.ready = False
            return readiness_model

        tag_key = readiness_config.tag_key
        tag_value = readiness_config.tag_value
        tag_match = self._match_tag(tag_key, tag_value, instance.get("Tags", []))

        # Update readiness model based on whether tag match was found
        readiness_model.ready = tag_match is not None
        return readiness_model

    @staticmethod
    def _match_tag(tag_key: str, tag_value: str, tags: Iterable[Mapping[str, Any]]) -> Mapping[str, Any] | None:
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
            filter(lambda t: t.get("Key", "") == tag_key and t.get("Value", "") == tag_value, tags),
            None,
        )
