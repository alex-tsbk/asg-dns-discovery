import threading

from app.components.readiness.instance_readiness_interface import InstanceReadinessInterface
from app.components.readiness.models.readiness_result_model import ReadinessResultModel
from app.domain.handlers.handler_context import HandlerContext
from app.utils import instrumentation
from app.utils.logging import get_logger
from app.workflows.instance_lifecycle.instance_lifecycle_context import InstanceLifecycleContext
from app.workflows.instance_lifecycle.instance_lifecycle_step import InstanceLifecycleStep


class InstanceReadinessStep(InstanceLifecycleStep):
    """Handles determining instance readiness in the instance lifecycle"""

    def __init__(self, instance_readiness_service: InstanceReadinessInterface):
        self.logger = get_logger()
        self.instance_readiness_service = instance_readiness_service
        super().__init__()

    def handle(self, context: InstanceLifecycleContext) -> HandlerContext:
        """Handle instance readiness lifecycle

        Args:
            context (InstanceLifecycleContext): Context in which the handler is executed
        """
        # Perform readiness check
        readiness_result, time_taken_ms = self.perform_check(context)

        # Update model with time taken, used for telemetry
        readiness_result.time_taken_ms = time_taken_ms

        # Record readiness check into internal cache
        self.logger.debug(f"Readiness check [{context.readiness_config.hash}] completed")

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


class CachedInstanceReadinessStep(InstanceLifecycleStep):

    # Internally tracks readiness checks that are in-flight,
    # to avoid re-checking readiness for the same readiness check for the same instance.
    # TODO: Check in AWS Lambda - make sure it's not cached across invocations
    checks_in_flight: dict[str, threading.Lock] = dict()

    # Internally tracks readiness checks that have passed,
    # to avoid re-checking readiness for the same readiness check
    # for the same instance.
    checks_completed: dict[str, bool] = {}

    def __init__(self, underlying_step: InstanceLifecycleStep) -> None:
        self.logger = get_logger()
        self.underlying_step = underlying_step

    def handle(self, context: InstanceLifecycleContext) -> HandlerContext:
        """Handle instance readiness lifecycle

        Args:
            context (InstanceLifecycleContext): Context in which the handler is executed
        """
        context_readiness_hash_key = self.__build_context_readiness_hash_key(context)

        # Declare default readiness result
        context.readiness_result = ReadinessResultModel(
            ready=False,
            instance_id=context.instance_id,
            scaling_group_name=context.scaling_group_config.scaling_group_name,
        )

        # If check has already been passed - short circuit
        if context_readiness_hash_key in self.checks_completed:
            self.logger.debug(f"Readiness check {context_readiness_hash_key} already passed")
            context.readiness_result.ready = self.checks_completed[context_readiness_hash_key]
            return super().handle(context)

        # Don't perform readiness check if it's already in flight, wait for it to complete
        if context_readiness_hash_key in self.checks_in_flight:
            self.logger.debug(
                f"Readiness check {context_readiness_hash_key} already in flight. Waiting on thread {threading.current_thread().name}.."
            )
            with self.checks_in_flight[context_readiness_hash_key]:
                # If lock was released, means the readiness check has completed on another thread
                context.readiness_result.ready = self.checks_completed[context_readiness_hash_key]
            return super().handle(context)

        # Mark readiness check as in-flight
        self.checks_in_flight[context_readiness_hash_key] = threading.Lock()
        with self.checks_in_flight[context_readiness_hash_key]:
            self.logger.debug(
                f"Readiness check [{context_readiness_hash_key}] started on thread {threading.current_thread().name}"
            )

            # Perform readiness check
            self.underlying_step.handle(context)

            # Record readiness check into internal cache
            self.checks_completed[context_readiness_hash_key] = context.readiness_result.ready
            self.logger.debug(f"Readiness check [{context_readiness_hash_key}] completed")

        # Continue handling
        return super().handle(context)

    @staticmethod
    def __build_context_readiness_hash_key(context: InstanceLifecycleContext) -> str:
        """On the basis of the context provided, build a unique key to represent the readiness configuration hash.

        Args:
            context (InstanceLifecycleContext): Context in which the handler is executed

        Returns:
            str: Unique key representing the execution/instance/readiness configuration
        """
        readiness_check_hash = context.readiness_config.hash if context.readiness_config else "none"
        return f"ctx:{context.context_id}/i:{context.instance_id}/rdn_chk_hash:{readiness_check_hash}"
