from time import sleep

from app.components.readiness.instance_readiness_interface import InstanceReadinessInterface
from app.components.readiness.models.readiness_result_model import ReadinessResultModel
from app.config.models.readiness_config import ReadinessConfig
from app.utils.logging import get_logger


class AwaitableInstanceReadinessService(InstanceReadinessInterface):
    """Decorator for InstanceReadinessInterface that waits for the instance to become ready"""

    def __init__(self, underlying_service: InstanceReadinessInterface) -> None:
        self.logger = get_logger()
        self.underlying_service = underlying_service

    def is_ready(self, instance_id: str, readiness_config: ReadinessConfig) -> ReadinessResultModel:
        """Checks whether the instance is ready. The method will wait for the instance
        to become ready in accordance with the readiness_config provided.

        Args:
            instance_id (str): Instance ID
            readiness_config (ReadinessConfig): Readiness configuration

        Returns:
            ReadinessResultModel: Model representing the readiness result
        """
        ready = self.underlying_service.is_ready(instance_id, readiness_config)
        if ready:
            return ReadinessResultModel(
                ready=True,
                instance_id=instance_id,
                readiness_config_hash=readiness_config.hash,
            )

        sleeping_for = 0
        tag_match_timeout = readiness_config.timeout_seconds
        tag_match_interval = readiness_config.interval_seconds

        # Wait for instance to become ready
        while not ready and sleeping_for < tag_match_timeout:
            self.logger.info(
                f"Waiting for instance to become ready: {instance_id} [{sleeping_for}/{tag_match_timeout}]"
            )
            sleep(tag_match_interval)
            ready = self.underlying_service.is_ready(instance_id, readiness_config)
            if ready:
                return ReadinessResultModel(
                    ready=True,
                    instance_id=instance_id,
                    readiness_config_hash=readiness_config.hash,
                )
            sleeping_for += tag_match_interval

        return ReadinessResultModel(
            ready=False,
            instance_id=instance_id,
            readiness_config_hash=readiness_config.hash,
        )
