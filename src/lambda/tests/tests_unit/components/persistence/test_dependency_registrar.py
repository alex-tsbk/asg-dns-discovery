from typing import Callable
from unittest.mock import MagicMock

from app.components.persistence.dependency_registrar import register_services
from app.components.persistence.internal.aws.aws_dynamodb_repository import AwsDynamoDBRepository
from app.components.persistence.repository_service_interface import RepositoryInterface
from app.config.env_configuration_service import EnvironmentConfigurationService
from app.utils.di import DILifetimeScope


def test_register_services_when_running_on_aws(aws_runtime):
    di_container = MagicMock()
    env_config_service = MagicMock(spec=EnvironmentConfigurationService)
    env_config_service.db_config.provider = "dynamodb"

    register_services(di_container, env_config_service)

    di_container.register.assert_any_call(RepositoryInterface, AwsDynamoDBRepository, lifetime=DILifetimeScope.SCOPED)
