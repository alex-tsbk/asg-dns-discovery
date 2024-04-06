from __future__ import annotations

import threading
from threading import Lock
from typing import Annotated, ClassVar

from app.components.healthcheck.health_check_interface import HealthCheckInterface
from app.components.healthcheck.models.health_check_result_model import HealthCheckResultModel
from app.components.metadata.instance_metadata_interface import InstanceMetadataInterface
from app.config.models.health_check_config import HealthCheckConfig
from app.handlers.contexts.instance_lifecycle_context import InstanceLifecycleContext
from app.handlers.handler_base import HandlerBase
from app.utils.logging import get_logger


class InstanceHealthCheckHandler(HandlerBase[InstanceLifecycleContext]):
    """Handles instance readiness lifecycle"""

    # Lock to ensure thread safety
    thread_lock: ClassVar[Lock] = threading.Lock()
    # Internally tracks checks that have passed,
    # to avoid re-checking health for the same health check for the same instance.
    # Considering we're running application in a short-lived
    # container, this should be fine to keep in memory.
    checks_passed: ClassVar[dict[Annotated[str, "instance-id"], set[str]]] = {}

    def __init__(
        self,
        instance_metadata_service: InstanceMetadataInterface,
        instance_health_check_service: HealthCheckInterface,
    ):
        self.logger = get_logger()
        self.instance_metadata_service = instance_metadata_service
        self.instance_health_check_service = instance_health_check_service
        super().__init__()

    def handle(self, context: InstanceLifecycleContext) -> InstanceLifecycleContext:
        """Handle instance readiness lifecycle

        Args:
            context (InstanceLifecycleContext): Context in which the handler is executed
        """
        health_check_result = self.perform_check(
            instance_id=context.instance_id,
            scaling_group_name=context.scaling_group_config.scaling_group_name,
            health_check_config=context.health_check_config,
        )
        # Record readiness check
        if health_check_result.healthy:
            self._record_passed_check(context.instance_id, context.health_check_config.uid)
        # Update context
        context.health_check_result = health_check_result
        # Continue handling
        return super().handle(context)

    def perform_check(
        self, instance_id: str, scaling_group_name: str, health_check_config: HealthCheckConfig
    ) -> HealthCheckResultModel:
        """Perform readiness check on the instance

        Args:
            instance_id (str): Instance ID
            scaling_group_name (str): Scaling Group name
            health_check_config (HealthCheckConfig): Readiness configuration

        Returns:
            HealthCheckResultModel: Model containing information about health check result
        """
        destination = self.instance_metadata_service.resolve_value()
        health_check_key = f"/{health_check_config.uid}"
        # Check if readiness check is enabled and has not been passed
        if (
            not health_check_config  # If readiness config is not provided
            or not health_check_config.enabled  # If readiness check is disabled
            or health_check_config.uid in self.checks_passed.get(instance_id, [])
        ):
            self.logger.debug(f"Readiness check disabled for Scaling Group: {scaling_group_name}")
            # Build result model
            health_check_result = HealthCheckResultModel(
                healthy=True,
                instance_id=instance_id,
                scaling_group_name=scaling_group_name,
                health_check_config=health_check_config,
            )
            return health_check_result

        self.logger.debug(f"Readiness check enabled for SG: {scaling_group_name}")
        # Perform readiness check
        return self.instance_health_check_service.is_ready(instance_id, health_check_config)

    def _record_passed_check(self, instance_id: str, readiness_config_id: str):
        """Records readiness check as passed.

        Args:
            instance_id (str): Instance ID
            readiness_config_id (str): Readiness configuration ID
        """
        # Obtain thread_lock before updating the shared state
        if instance_id not in self.readiness_checks_passed:
            self.thread_lock.acquire()
            self.readiness_checks_passed[instance_id] = []
            self.thread_lock.release()
        # We're not mutating state, so no need to thread_lock here
        self.readiness_checks_passed[instance_id].add(readiness_config_id)
