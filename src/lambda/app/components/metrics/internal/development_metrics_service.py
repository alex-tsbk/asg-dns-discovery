import datetime
from typing import Any

from app.components.metrics.metrics_interface import MetricsInterface
from app.utils.logging import get_logger


class DevelopmentMetricsService(MetricsInterface):
    """Concrete implementation of metrics service using local development environment (no backend)"""

    def __init__(self):
        self._logger = get_logger()
        # Specify processing date time
        self.processing_date_time = datetime.datetime.now(datetime.UTC)
        # Metric data - records individual metrics for later publishing
        self.metric_data_points: list[dict[str, Any]] = []
        # Metric dimensions - shared across all metrics pushed
        self.metric_dimensions: list[dict[str, Any]] = []

    def reset(self):
        """Resets the metrics service to a clean state"""
        self.metric_data_points = []
        self.metric_dimensions = []
        self.processing_date_time = datetime.datetime.now(datetime.UTC)
        return

    def record_data_point(
        self,
        metric_name: str,
        metric_value: int,
        description: str = "",
        metric_unit: str = "Count",
    ):
        """Record a metric data point for later publishing

        Args:
            metric_name (str): name of metric
            metric_value (int): value of metric
            metric_unit (str, optional): unit of metric. Defaults to "Count".
        """
        existing_metric = next((x for x in self.metric_data_points if x["MetricName"] == metric_name), None)
        if existing_metric:
            existing_metric["Value"] += metric_value
        else:
            self.metric_data_points.append(
                {
                    "MetricName": metric_name,
                    "Timestamp": self.processing_date_time,
                    "Unit": metric_unit,
                    "Value": metric_value,
                }
            )
        if description:
            self._logger.debug(f"{description}: {metric_value}")

    def record_dimension(self, metric_name: str, metric_value: str, description: str = ""):
        """Record a metric dimension for later use in metric publishing

        Args:
            metric_name (str): name of metric dimension
            metric_value (str): value of metric dimension
        """
        # Only add dimension if it doesn't exist
        if not next((x for x in self.metric_dimensions if x["Name"] == metric_name), None):
            self.metric_dimensions.append({"Name": metric_name, "Value": str(metric_value)})
        if description:
            self._logger.info(f"{description}: {metric_value}")

    def publish_metrics(self) -> bool:
        """Publish all recorded metrics to the metrics service

        Returns:
            bool: True if metrics were successfully published, False otherwise
        """
        # Merge shared dimensions into metric data points
        for metric in self.metric_data_points:
            metric["Dimensions"] = self.metric_dimensions

        # Log metrics to console
        self._logger.info(f"Metrics: {self.metric_data_points}")
        return True
