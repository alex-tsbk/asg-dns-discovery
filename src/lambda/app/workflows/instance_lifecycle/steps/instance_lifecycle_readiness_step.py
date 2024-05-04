from typing import ClassVar

from app.components.readiness.instance_readiness_interface import InstanceReadinessInterface
from app.components.readiness.models.readiness_result_model import ReadinessResultModel
from app.domain.handlers.handler_context import HandlerContext
from app.utils import instrumentation
from app.utils.logging import get_logger
from app.workflows.instance_lifecycle.instance_lifecycle_context import InstanceLifecycleContext
from app.workflows.instance_lifecycle.instance_lifecycle_step import InstanceLifecycleStep


class InstanceReadinessHandler(InstanceLifecycleStep):
    """Handles determining instance readiness in the instance lifecycle"""

    # Internally tracks readiness checks that have passed,
    # to avoid re-checking readiness for the same readiness check
    # for the same instance.
    checks_passed: ClassVar[set[str]] = set()

    def __init__(self, instance_readiness_service: InstanceReadinessInterface):
        self.logger = get_logger()
        self.instance_readiness_service = instance_readiness_service
        super().__init__()

    def handle(self, context: InstanceLifecycleContext) -> HandlerContext:
        """Handle instance readiness lifecycle

        Args:
            context (InstanceLifecycleContext): Context in which the handler is executed
        """
        context_readiness_key = self.__build_context_readiness_key__(context)

        # If check has already been passed - short circuit
        if context_readiness_key in self.checks_passed:
            self.logger.debug(f"Readiness check {context_readiness_key} already passed")
            context.readiness_result = ReadinessResultModel(
                ready=True,
                instance_id=context.instance_id,
                scaling_group_name=context.scaling_group_config.scaling_group_name,
            )
            return super().handle(context)

        # Perform readiness check
        readiness_result, time_taken_ms = self.perform_check(context)

        # Update model with time taken, used for telemetry
        readiness_result.time_taken_ms = time_taken_ms

        # Record readiness check into internal cache
        if readiness_result.ready:
            self.checks_passed.add(context_readiness_key)
            self.logger.debug(f"Readiness check [{context_readiness_key}] passed")

        # Update context
        context.readiness_result = readiness_result

        # Continue handling
        return super().handle(context)

    @instrumentation.measure_time_taken
    def perform_check(self, context: InstanceLifecycleContext) -> ReadinessResultModel:
        """Perform readiness check on the instance

        Args:
            instance_id (str): Instance ID
            scaling_group_name (str): Scaling Group name
            readiness_config (ReadinessConfig): Readiness configuration

        Returns:
            ReadinessResultModel: Readiness result model
        """
        scaling_group_name = context.scaling_group_config.scaling_group_name

        # If no readiness configuration is provided, return ready
        if not context.readiness_config or not context.readiness_config.enabled:
            self.logger.debug(f"Readiness check disabled for Scaling Group: {scaling_group_name}")
            return ReadinessResultModel(
                ready=True, instance_id=context.instance_id, scaling_group_name=scaling_group_name
            )

        # Perform readiness check
        return self.instance_readiness_service.is_ready(context.instance_id, context.readiness_config)

    @staticmethod
    def __build_context_readiness_key__(context: InstanceLifecycleContext) -> str:
        """On the basis of the context, build a unique key for the readiness check.

        Args:
            context (InstanceLifecycleContext): Context in which the handler is executed

        Returns:
            str: Unique key representing the execution/instance/readiness configuration
        """
        readiness_check_id = context.readiness_config.uid if context.readiness_config else ""
        return f"ctx:{context.context_id}/i:{context.instance_id}/sg:{context.scaling_group_config.scaling_group_name}/rdn_chk_id:{readiness_check_id}"
