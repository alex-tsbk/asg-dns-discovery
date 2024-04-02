import abc

from app.config.models.health_check_config import HealthCheckConfig

from .models.health_check_result_model import HealthCheckResultModel


class HealthCheckInterface(metaclass=abc.ABCMeta):
    """Interface for performing healthcheck on the specified destination."""

    @abc.abstractmethod
    def check(self, destination: str, health_check_config: HealthCheckConfig) -> HealthCheckResultModel:
        """
        Performs a health check on a destination in accordance with the given health check configuration.

        Args:
            destination (str): The address of the resource to run health check against. Can be IP, DNS name, etc.
            health_check_config (HealthCheckConfig): The health check configuration to use.

        Returns:
            HealthCheckResultModel: The model that represents the result of the health check.
        """
