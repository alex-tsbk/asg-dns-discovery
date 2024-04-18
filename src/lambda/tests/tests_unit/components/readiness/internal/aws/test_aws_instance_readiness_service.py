from unittest.mock import MagicMock, patch

import pytest
from app.components.readiness.internal.aws.aws_instance_readiness_service import AwsInstanceReadinessService
from app.config.models.readiness_config import ReadinessConfig


@pytest.fixture
def ec2_service():
    return MagicMock()


def test_is_ready_when_readiness_disabled(ec2_service):
    readiness_service = AwsInstanceReadinessService(ec2_service)
    readiness_config = ReadinessConfig(enabled=False)

    assert readiness_service.is_ready("instance_id", readiness_config).ready is True


def test_is_ready_when_instance_not_found(ec2_service):
    ec2_service.get_instance.return_value = None
    readiness_service = AwsInstanceReadinessService(ec2_service)
    readiness_config = ReadinessConfig(enabled=True, tag_key="tag_key", tag_value="tag_value")

    assert readiness_service.is_ready("instance_id", readiness_config).ready is False


def test_is_ready_when_tag_match(ec2_service):
    instance = {"Tags": [{"Key": "tag_key", "Value": "tag_value"}]}
    ec2_service.get_instance.return_value = instance
    readiness_service = AwsInstanceReadinessService(ec2_service)
    readiness_config = ReadinessConfig(enabled=True, tag_key="tag_key", tag_value="tag_value")

    assert readiness_service.is_ready("instance_id", readiness_config).ready is True


def test_is_ready_when_tag_not_match(ec2_service):
    instance = MagicMock()
    instance.tags = [{"Key": "tag_key", "Value": "other_value"}]
    ec2_service.get_instance.return_value = instance
    readiness_service = AwsInstanceReadinessService(ec2_service)
    readiness_config = ReadinessConfig(enabled=True, tag_key="tag_key", tag_value="tag_value")

    assert readiness_service.is_ready("instance_id", readiness_config).ready is False
