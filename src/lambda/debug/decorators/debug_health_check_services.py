from time import sleep

from app.components.healthcheck.health_check_interface import HealthCheckInterface
from app.components.healthcheck.models.health_check_result_model import HealthCheckResultModel
from app.config.models.health_check_config import HealthCheckConfig
from app.utils.logging import get_logger


class PassingHealthCheckDebugService(HealthCheckInterface):
    """Decorator for HealthCheckInterface that always returns a passing health check result."""

    def __init__(self, underlying_service: HealthCheckInterface) -> None:
        self.logger = get_logger()
        self.underlying_service = underlying_service

    def check(self, destination: str, health_check_config: HealthCheckConfig) -> HealthCheckResultModel:
        self.logger.info("Sleeping for 1 second before returning a passing health check result.")
        sleep(1)
        return HealthCheckResultModel(
            True, message="Passing health check service.", health_check_config_hash=health_check_config.hash
        )


class FailingHealthCheckDebugService(HealthCheckInterface):
    """Decorator for HealthCheckInterface that always returns a failing health check result."""

    def __init__(self, underlying_service: HealthCheckInterface) -> None:
        self.logger = get_logger()
        self.underlying_service = underlying_service

    def check(self, destination: str, health_check_config: HealthCheckConfig) -> HealthCheckResultModel:
        self.logger.info("Sleeping for 1 second before returning a failing health check result.")
        sleep(1)
        return HealthCheckResultModel(
            False, message="Failing health check service.", health_check_config_hash=health_check_config.hash
        )
