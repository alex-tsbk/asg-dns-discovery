from dataclasses import dataclass, field

from app.components.healthcheck.models.health_check_result_model import HealthCheckResultModel
from app.components.readiness.models.readiness_result_model import ReadinessResultModel
from app.config.models.dns_record_config import DnsRecordProvider
from app.config.models.health_check_config import HealthCheckConfig
from app.config.models.readiness_config import ReadinessConfig
from app.config.models.scaling_group_config import ScalingGroupProceedMode
from app.workflows.instance_lifecycle.instance_lifecycle_context import InstanceLifecycleContext


@dataclass(kw_only=True)
class InstanceLifecycleContextManager:
    """
    Manager for aggregating and simplifying access to instance lifecycle contexts.
    """

    # Scaling group may have multiple configurations declared,
    # which themselves may have different readiness and health check configurations.
    # Thus, same instance may be passing readiness and health checks for one DNS configuration,
    # but not for another. This is why it is necessary to track unique combinations of readiness
    # and health checks for each DNS configuration separately. This also allows to prevent
    # duplicate processing of the same instance when the readiness and health check configurations are the same.
    instances_contexts: list[InstanceLifecycleContext] = field(init=False, default_factory=list)

    def register_instance_context(self, instance_context: InstanceLifecycleContext):
        """Register an instance context that is part of the current scaling group lifecycle.

        Args:
            instance_context (InstanceLifecycleContext): Instance lifecycle context to be registered
        """
        # Validate readiness configuration, and if not require checking, mark as 'ready'
        self._assess_readiness_configuration(instance_context)
        # Validate health check configuration, and if not require checking, mark as 'healthy'
        self._assess_health_check_configuration(instance_context)
        # Register instance context
        self.instances_contexts.append(instance_context)

    def get_all_contexts(self) -> list[InstanceLifecycleContext]:
        """Returns all instance lifecycle contexts.

        Returns:
            list[InstanceLifecycleContext]: List of instance lifecycle contexts
        """
        return self.instances_contexts

    def get_operational_contexts(self) -> list[InstanceLifecycleContext]:
        """Returns operational instance lifecycle contexts.

        Returns:
            list[InstanceLifecycleContext]: List of operational instance lifecycle contexts
        """
        all_instances_contexts_operational = self.check_all_instances_operational()
        return [
            instance_context
            for instance_context in self.instances_contexts
            if instance_context.operational
            and instance_context.scaling_group_config.multiple_config_proceed_mode
            == ScalingGroupProceedMode.SELF_OPERATIONAL
            or instance_context.scaling_group_config.multiple_config_proceed_mode
            == ScalingGroupProceedMode.ALL_OPERATIONAL
            and all_instances_contexts_operational
        ]

    def get_non_operational_contexts(self) -> list[InstanceLifecycleContext]:
        """Returns non-operational instance lifecycle contexts.

        Returns:
            list[InstanceLifecycleContext]: List of non-operational instance lifecycle contexts
        """
        all_instances_contexts_operational = self.check_all_instances_operational()
        return [
            instance_context
            for instance_context in self.instances_contexts
            if not instance_context.operational
            or instance_context.operational
            and instance_context.scaling_group_config.multiple_config_proceed_mode
            == ScalingGroupProceedMode.ALL_OPERATIONAL
            and all_instances_contexts_operational
        ]

    def check_all_instances_operational(self) -> bool:
        """Returns True if all instances are considered operational.

        Returns:
            bool: True if all instances are considered operational
        """
        operational_instances = [
            instance_context
            for instance_context in self.instances_contexts
            if instance_context.instance_model and instance_context.operational
        ]
        return len(operational_instances) == len(self.instances_contexts)

    def get_dns_providers(self) -> set[DnsRecordProvider]:
        """Returns distinct DNS providers from all instances contexts.

        Returns:
            set[DnsRecordProvider]: Set of DNS providers
        """
        return {
            instance_context.scaling_group_config.dns_config.provider for instance_context in self.instances_contexts
        }

    def get_readiness_configs_require_checking(
        self,
    ) -> dict[str, tuple[ReadinessConfig, list[InstanceLifecycleContext]]]:
        """Returns readiness configurations that require checking.

        Returns:
            dict[str, tuple[ReadinessConfig, list[InstanceLifecycleContext]]]: Readiness configurations that require checking,
                where key is readiness config hash and value is tuple of readiness config and list of instance contexts that
                have the same readiness config
        """
        readiness_configs_require_checking: dict[str, tuple[ReadinessConfig, list[InstanceLifecycleContext]]] = {
            instance_context.readiness_config.hash: (instance_context.readiness_config, [])
            for instance_context in self.instances_contexts
            if instance_context.readiness_check_required
        }  # type: ignore - mypy doesn't understand that `readiness_check_required` ensures `readiness_config` is not None
        for instance_context in self.instances_contexts:
            if (
                instance_context.readiness_check_required
                and instance_context.readiness_config.hash in readiness_configs_require_checking
            ):
                readiness_configs_require_checking[instance_context.readiness_config.hash][1].append(instance_context)

        return readiness_configs_require_checking

    def get_health_check_configs_require_checking(
        self,
    ) -> dict[str, tuple[HealthCheckConfig, list[InstanceLifecycleContext]]]:
        """Returns health check configurations that require checking.

        Returns:
            dict[str, tuple[HealthCheckConfig, list[InstanceLifecycleContext]]]: Health check configurations that require checking,
                where key is health check config hash and value is tuple of health check config and list of instance contexts that
                have the same health check config
        """
        health_check_configs_require_checking: dict[str, tuple[HealthCheckConfig, list[InstanceLifecycleContext]]] = {
            instance_context.health_check_config.hash: (instance_context.health_check_config, [])
            for instance_context in self.instances_contexts
            if instance_context.readiness_check_passed and instance_context.health_check_required
        }  # type: ignore - mypy doesn't understand that `health_check_required` ensures `health_check_config` is not None
        for instance_context in self.instances_contexts:
            if (
                instance_context.readiness_check_passed
                and instance_context.health_check_required
                and instance_context.health_check_config.hash in health_check_configs_require_checking
            ):
                health_check_configs_require_checking[instance_context.health_check_config.hash][1].append(
                    instance_context
                )
        return health_check_configs_require_checking

    @staticmethod
    def _assess_readiness_configuration(instance_context: InstanceLifecycleContext):
        """Assess readiness configuration and mark as ready if not required to check.

        Args:
            instance_context (InstanceLifecycleContext): Instance lifecycle context
        """
        if not instance_context.readiness_check_required:
            instance_context.readiness_result = ReadinessResultModel(
                ready=True,
                instance_id=instance_context.instance_id,
            )
            # Assign hash only if readiness config is present
            if instance_context.readiness_config is not None:
                instance_context.readiness_result.readiness_config_hash = instance_context.readiness_config.hash

    @staticmethod
    def _assess_health_check_configuration(instance_context: InstanceLifecycleContext):
        """Assess health check configuration and mark as healthy if not required to check.

        Args:
            instance_context (InstanceLifecycleContext): Instance lifecycle context
        """
        if not instance_context.health_check_required:
            instance_context.health_check_result = HealthCheckResultModel(
                healthy=True,
                instance_id=instance_context.instance_id,
            )
            if instance_context.health_check_config is not None:
                instance_context.health_check_result.health_check_config_hash = (
                    instance_context.health_check_config.hash
                )
