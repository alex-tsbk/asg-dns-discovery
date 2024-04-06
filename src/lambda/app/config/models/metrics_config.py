from dataclasses import dataclass


@dataclass
class MetricsConfig:
    """Model representing the metrics configuration for the Scaling Group DNS discovery application."""

    metrics_enabled: bool
    metrics_provider: str
    metrics_namespace: str
    alarms_enabled: bool
    alarms_notification_destination: str

    def __post_init__(self):
        self.metrics_provider = self.metrics_provider.lower()
