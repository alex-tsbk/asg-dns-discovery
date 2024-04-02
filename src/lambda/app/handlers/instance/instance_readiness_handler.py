from __future__ import annotations

import threading
from threading import Lock
from typing import ClassVar

from app.components.readiness.instance_readiness_interface import InstanceReadinessInterface
from app.components.readiness.models.readiness_result_model import ReadinessResultModel
from app.config.models.readiness_config import ReadinessConfig
from app.handlers.contexts.instance_lifecycle_context import InstanceLifecycleContext
from app.handlers.handler_base import HandlerBase
from app.utils.logging import get_logger


class InstanceReadinessHandler(HandlerBase[InstanceLifecycleContext]):
    """Determines instance readiness based on readiness checks"""

    # Lock to ensure thread safety
    thread_lock: ClassVar[Lock] = threading.Lock()
    # Internally tracks readiness checks that have passed,
    # to avoid re-checking readiness for the same readiness check
    # for the same instance. Considering we're running application in a short-lived
    # container, this should be fine to keep in memory.
    checks_passed: ClassVar[dict[str, set[str]]] = {}

    def __init__(self, instance_readiness_service: InstanceReadinessInterface):
        self.logger = get_logger()
        self.instance_readiness_service = instance_readiness_service
        super().__init__()

    def handle(self, context: InstanceLifecycleContext) -> InstanceLifecycleContext:
        """Handle instance readiness lifecycle

        Args:
            context (InstanceLifecycleContext): Context in which the handler is executed
        """
        readiness_result = self.perform_check(
            instance_id=context.instance_id,
            scaling_group_name=context.scaling_group_config.scaling_group_name,
            readiness_config=context.readiness_config,
        )
        # Record readiness check
        if readiness_result.ready:
            self._record_passed_check(context.instance_id, context.readiness_config.uid)
        # Update context
        context.readiness_result = readiness_result
        # Continue handling
        return super().handle(context)

    def perform_check(
        self, instance_id: str, scaling_group_name: str, readiness_config: ReadinessConfig
    ) -> ReadinessResultModel:
        """Perform readiness check on the instance

        Args:
            instance_id (str): Instance ID
            scaling_group_name (str): Scaling Group name
            readiness_config (ReadinessConfig): Readiness configuration

        Returns:
            ReadinessResultModel: Readiness result model
        """
        # Check if readiness check is enabled and has not been passed
        if (
            not readiness_config  # If readiness config is not provided
            or not readiness_config.enabled  # If readiness check is disabled
            or readiness_config.uid in self.checks_passed.get(instance_id, [])
        ):
            self.logger.debug(f"Readiness check disabled for Scaling Group: {scaling_group_name}")
            # Build result model
            readiness_result = ReadinessResultModel(
                ready=True,
                instance_id=instance_id,
                scaling_group_name=scaling_group_name,
                readiness_config=readiness_config,
            )
            return readiness_result

        self.logger.debug(f"Readiness check enabled for SG: {scaling_group_name}")
        # Perform readiness check
        return self.instance_readiness_service.is_ready(instance_id, readiness_config)

    def _record_passed_check(self, instance_id: str, readiness_config_id: str):
        """Records readiness check as passed.

        Args:
            instance_id (str): Instance ID
            readiness_config_id (str): Readiness configuration ID
        """
        # Obtain thread_lock before updating the shared state
        if instance_id not in self.checks_passed:
            self.thread_lock.acquire()
            self.checks_passed[instance_id] = []
            self.thread_lock.release()
        # We're not mutating state, so no need to thread_lock here
        self.checks_passed[instance_id].add(readiness_config_id)
