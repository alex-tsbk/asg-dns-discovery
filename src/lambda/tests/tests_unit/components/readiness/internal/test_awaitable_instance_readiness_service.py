from unittest.mock import MagicMock, patch

import pytest
from app.components.readiness.internal.awaitable_instance_readiness_service import AwaitableInstanceReadinessService
from app.components.readiness.models.readiness_result_model import ReadinessResultModel
from app.config.models.readiness_config import ReadinessConfig


@pytest.fixture
def underlying_service():
    return MagicMock()


def test_is_ready_when_underlying_service_ready(underlying_service):
    underlying_service.is_ready.return_value = ReadinessResultModel(True)
    readiness_service = AwaitableInstanceReadinessService(underlying_service)
    readiness_config = ReadinessConfig(
        enabled=True, tag_key="tag_key", tag_value="tag_value", timeout_seconds=3, interval_seconds=1
    )

    assert readiness_service.is_ready("instance_id", readiness_config) is True


@patch("app.components.readiness.internal.awaitable_instance_readiness_service.sleep", return_value=None)
def test_is_ready_waits_when_tag_not_match(patched_time_sleep, underlying_service):
    underlying_service.is_ready.return_value = ReadinessResultModel(False)
    readiness_service = AwaitableInstanceReadinessService(underlying_service)
    readiness_config = ReadinessConfig(
        enabled=True, tag_key="tag_key", tag_value="tag_value", timeout_seconds=3, interval_seconds=1
    )

    readiness_service.is_ready("instance_id", readiness_config)

    # Ensure time.sleep was called 3 times
    assert patched_time_sleep.call_count == 3
