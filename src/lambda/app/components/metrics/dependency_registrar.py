from app.config.env_configuration_service import EnvironmentConfigurationService
from app.context import RUNTIME_CONTEXT
from app.utils.di import DIContainer, DILifetimeScope

from .internal.development_metrics_service import DevelopmentMetricsService
from .metrics_interface import MetricsInterface


def register_services(di_container: DIContainer, env_config_service: EnvironmentConfigurationService):
    """Registers services concrete implementations in the DI container.

    Args:
        di_container (DIContainer): DI container
    """
    if RUNTIME_CONTEXT.is_local_development:
        di_container.register(MetricsInterface, DevelopmentMetricsService, lifetime=DILifetimeScope.SCOPED)
        return

    metrics_provider = env_config_service.metrics_config.metrics_provider
    if RUNTIME_CONTEXT.is_aws and metrics_provider == "cloudwatch":
        from app.components.metrics.internal.aws.aws_cloudwatch_metrics_service import AwsCloudwatchMetricsService

        di_container.register(MetricsInterface, AwsCloudwatchMetricsService, lifetime=DILifetimeScope.SCOPED)
