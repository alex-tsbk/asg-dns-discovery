from typing import ClassVar

from app.components.healthcheck.health_check_interface import HealthCheckInterface
from app.components.healthcheck.models.health_check_result_model import HealthCheckResultModel
from app.components.metadata.instance_metadata_interface import InstanceMetadataInterface
from app.components.metadata.models.metadata_result_model import MetadataResultModel
from app.domain.handlers.handler_context import HandlerContext
from app.utils import instrumentation
from app.utils.exceptions import BusinessException
from app.utils.logging import get_logger
from app.workflows.instance_lifecycle.instance_lifecycle_context import InstanceLifecycleContext
from app.workflows.instance_lifecycle.instance_lifecycle_step import InstanceLifecycleStep


class InstanceHealthCheckStep(InstanceLifecycleStep):
    """Handles determining instance health check in the instance lifecycle"""

    # Internally tracks checks that have passed,
    # to avoid re-checking health for the same health check for the same instance.
    checks_passed: ClassVar[set[str]] = set()

    def __init__(
        self,
        instance_metadata_service: InstanceMetadataInterface,
        instance_health_check_service: HealthCheckInterface,
    ):
        self.logger = get_logger()
        self.instance_metadata_service = instance_metadata_service
        self.instance_health_check_service = instance_health_check_service
        super().__init__()

    def handle(self, context: InstanceLifecycleContext) -> HandlerContext:
        """Handle instance health check lifecycle

        Args:
            context (InstanceLifecycleContext): Context in which the handler is executed
        """
        context_healthcheck_key = self.__build_context_healthcheck_key__(context)

        # If check has already been passed - short circuit
        if context_healthcheck_key in self.checks_passed:
            self.logger.debug(f"Health check {context_healthcheck_key} already passed")
            context.health_check_result = HealthCheckResultModel(
                healthy=True,
                instance_id=context.instance_id,
            )
            return super().handle(context)

        # Perform health check
        health_check_result, time_taken_ms = self.perform_check(context)

        # Update time taken, used for telemetry
        health_check_result.time_taken_ms = time_taken_ms

        # Record health check into internal cache
        if health_check_result.healthy:
            self.checks_passed.add(context_healthcheck_key)
            self.logger.debug(f"Health check [{context_healthcheck_key}] passed")

        # Update context
        context.health_check_result = health_check_result

        # Continue handling
        return super().handle(context)

    @instrumentation.measure_time_taken
    def perform_check(self, context: InstanceLifecycleContext) -> HealthCheckResultModel:
        """Perform health check on the instance

        Args:
            context (InstanceLifecycleContext): Context in which the handler is executed

        Returns:
            HealthCheckResultModel: Model containing information about health check result
        """
        scaling_group_name = context.scaling_group_config.scaling_group_name
        dns_config_hash = context.scaling_group_config.dns_config.hash

        # If no health check present, or health check is disabled, consider instance healthy
        if context.health_check_config is None or not context.health_check_config.enabled:
            self.logger.debug(
                f"Health check disabled for Scaling Group: {scaling_group_name} tracking DNS configuration '{dns_config_hash}'"
            )
            # Build result model
            return HealthCheckResultModel(healthy=True, instance_id=context.instance_id)

        # Ensure instance model is loaded prior to performing health check
        if context.instance_model is None:
            raise BusinessException(
                "Instance model is missing in the context. Must be loaded before performing health check."
            )

        # Resolve the destination address for health check
        self.logger.debug(f"Readiness check enabled for SG: {scaling_group_name}")
        destination: MetadataResultModel = self.instance_metadata_service.resolve_value(
            context.instance_model, context.health_check_config.endpoint_source
        )

        # Perform health check
        return self.instance_health_check_service.check(destination.value, context.health_check_config)

    @staticmethod
    def __build_context_healthcheck_key__(context: InstanceLifecycleContext) -> str:
        """On the basis of the context, build a unique key for the health check.

        Args:
            context (InstanceLifecycleContext): Context in which the handler is executed

        Returns:
            str: Unique key representing the execution/instance/health check configuration
        """
        health_check_id = context.health_check_config.hash if context.health_check_config else ""
        return f"ctx:{context.context_id}/i:{context.instance_id}/sg:{context.scaling_group_config.scaling_group_name}/hth_hck_id:{health_check_id}"
