from typing import Any, Callable

from app.config.models.db_config import DbConfig
from app.config.models.metrics_config import MetricsConfig
from app.config.models.readiness_config import ReadinessConfig
from app.config.models.reconciliation_config import ReconciliationConfig
from app.utils import environment


class EnvironmentConfigurationService:
    """Service class for resolving application configuration from environment variables"""

    def __init__(self):
        # Cache placeholders
        self._cache: dict[str, Any] = {}

    @property
    def readiness_config(self) -> ReadinessConfig:
        """Returns readiness settings. These are used to determine if an instance is ready to serve traffic."""

        def resolver() -> ReadinessConfig:
            enabled = environment.try_get_value("ec2_readiness_enabled", "true").lower() == "true"
            interval = environment.try_get_value("ec2_readiness_interval_seconds", 5)
            timeout = environment.try_get_value("ec2_readiness_timeout_seconds", 300)
            tag_key = environment.try_get_value("ec2_readiness_tag_key", "app:code-deploy:status")
            tag_value = environment.try_get_value("ec2_readiness_tag_value", "success")
            return ReadinessConfig(
                enabled=enabled,
                interval_seconds=interval,
                timeout_seconds=timeout,
                tag_key=tag_key,
                tag_value=tag_value,
            )

        return self._cached("readiness_config", resolver)

    @property
    def db_config(self) -> DbConfig:
        """Returns DynamoDB settings. These are used to determine if an instance is ready to serve traffic."""

        def resolver() -> DbConfig:
            provider = environment.try_get_value("db_provider", "dynamodb")
            table_name = environment.try_get_value("db_table_name", "")
            config_item_key_id = environment.try_get_value("db_config_item_key_id", "")
            return DbConfig(
                provider=provider,
                table_name=table_name,
                config_item_key_id=config_item_key_id,
            )

        return self._cached("dynamo_config", resolver)

    @property
    def reconciliation_config(self) -> ReconciliationConfig:
        """Returns reconciliation settings. These are used to determine if an instance is ready to serve traffic."""

        def resolver() -> ReconciliationConfig:
            what_if = environment.try_get_value("reconciliation_what_if", "false").lower() == "true"
            max_concurrency = environment.try_get_value("reconciliation_max_concurrency", 1)
            scaling_group_valid_states = environment.try_get_value(
                "reconciliation_scaling_group_valid_states", ""
            ).split(",")
            return ReconciliationConfig(what_if, max_concurrency, scaling_group_valid_states)

        return self._cached("reconciliation_config", resolver)

    @property
    def metrics_config(self) -> MetricsConfig:
        """Returns metrics settings. These are used to determine if an instance is ready to serve traffic."""

        def resolver() -> MetricsConfig:
            metrics_enabled = environment.try_get_value("monitoring_metrics_enabled", "false").lower() == "true"
            metrics_provider = environment.try_get_value("monitoring_metrics_provider", "cloudwatch")
            metrics_namespace = environment.try_get_value("monitoring_metrics_namespace", "")
            alarms_enabled = environment.try_get_value("monitoring_alarms_enabled", "false").lower() == "true"
            alarms_notification_destination = environment.try_get_value(
                "monitoring_alarms_notification_destination", ""
            )
            return MetricsConfig(
                metrics_enabled=metrics_enabled,
                metrics_provider=metrics_provider,
                metrics_namespace=metrics_namespace,
                alarms_enabled=alarms_enabled,
                alarms_notification_destination=alarms_notification_destination,
            )

        return self._cached("metrics_config", resolver)

    def _cached[T](self, key: str, resolver: Callable[[], T]) -> T:
        """Returns a cached value or resolves it using the provided resolver function

        Args:
            key (str): Cache key
            resolver (Callable[[], any]): Resolver function

        Returns:
            any: Cached value
        """
        if key not in self._cache:
            self._cache[key] = resolver()
        return self._cache[key]
