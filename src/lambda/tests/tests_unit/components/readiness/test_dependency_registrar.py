from typing import Callable
from unittest.mock import MagicMock

from app.components.readiness.dependency_registrar import register_services
from app.components.readiness.instance_readiness_interface import InstanceReadinessInterface
from app.components.readiness.internal.aws.aws_instance_readiness_service import AwsInstanceReadinessService
from app.utils.di import DILifetimeScope


def test_register_services_when_running_on_aws(aws_runtime):
    di_container = MagicMock()

    register_services(di_container)

    di_container.register.assert_any_call(InstanceReadinessInterface, AwsInstanceReadinessService)
