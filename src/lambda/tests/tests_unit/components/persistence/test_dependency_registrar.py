from typing import Callable
from unittest.mock import MagicMock

from app.components.persistence.database_repository_interface import DatabaseRepositoryInterface
from app.components.persistence.dependency_registrar import register_services
from app.components.persistence.internal.aws.aws_database_repository import AwsDatabaseRepository
from app.config.env_configuration_service import EnvironmentConfigurationService


def test_register_services_when_running_on_aws(aws_runtime):
    di_container = MagicMock()

    register_services(di_container)

    di_container.register.assert_any_call(DatabaseRepositoryInterface, AwsDatabaseRepository)
