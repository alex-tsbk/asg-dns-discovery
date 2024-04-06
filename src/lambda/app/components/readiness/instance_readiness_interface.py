from abc import ABCMeta, abstractmethod

from app.config.models.readiness_config import ReadinessConfig

from .models.readiness_result_model import ReadinessResultModel


class InstanceReadinessInterface(metaclass=ABCMeta):
    """Interface for instance readiness service"""

    @abstractmethod
    def is_ready(self, instance_id: str, readiness_config: ReadinessConfig) -> ReadinessResultModel:
        """Checks if the instance is ready.

        Args:
            instance_id (str): Instance ID
            readiness_config (ReadinessConfig): Readiness configuration
            wait (bool): When set to True, the method will wait for the instance
                to become ready in accordance with the readiness_config provided

        Returns:
            ReadinessResultModel: Model representing the readiness result
        """
        pass
