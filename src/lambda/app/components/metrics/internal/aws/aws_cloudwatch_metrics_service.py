from __future__ import annotations

import datetime
from typing import Any

from app.components.metrics.metrics_interface import MetricsInterface
from app.config.env_configuration_service import EnvironmentConfigurationService
from app.infrastructure.aws.services.cloudwatch_service import CloudWatchService
from app.utils.exceptions import CloudProviderException
from app.utils.logging import get_logger
from app.utils.serialization import to_json
from botocore.exceptions import ClientError


class AwsCloudwatchMetricsService(MetricsInterface):
    """Concrete implementation of metrics service using AWS Cloudwatch"""

    def __init__(
        self, aws_cloudwatch_service: CloudWatchService, env_configuration_service: EnvironmentConfigurationService
    ):
        self.logger = get_logger()
        # Specify processing date time
        self.processing_date_time = datetime.datetime.now(datetime.UTC)
        self.cloudwatch_metrics_namespace = env_configuration_service.metrics_config.metrics_namespace
        # Metric data - records individual metrics for later publishing
        self.metric_data_points: list[dict[str, Any]] = []
        # Metric dimensions - shared across all metrics pushed
        self.metric_dimensions: list[dict[str, Any]] = []
        self.aws_cloudwatch_service = aws_cloudwatch_service

    def reset(self):
        """Resets the metrics service to a clean state"""
        self.metric_data_points = []
        self.metric_dimensions = []
        self.processing_date_time = datetime.datetime.now(datetime.UTC)

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
            self.logger.debug(f"{description}: {metric_value}")

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
            self.logger.info(f"{description}: {metric_value}")

    def publish_metrics(self) -> bool:
        """Publish all recorded metrics to the metrics service

        Returns:
            bool: True if metrics were successfully published, False otherwise
        """

        # Merge shared dimensions into metric data points
        for metric in self.metric_data_points:
            metric["Dimensions"] = self.metric_dimensions

        try:
            # Put metric data
            self.aws_cloudwatch_service.publish_metric_data(
                namespace=self.cloudwatch_metrics_namespace,
                metric_data=self.metric_data_points,  # type: ignore -- underlying boto3 type now available at runtime
            )
            self.logger.debug(f"Pushing metrics to cloudwatch: {self.metric_data_points}")
            self.logger.info(
                f"Metric pushed successfully: {self.cloudwatch_metrics_namespace} / {len(self.metric_data_points)} data points."
            )
            return True
        except ClientError as e:
            message = f"Error pushing metrics to cloudwatch: {str(e)}"
            self.logger.error(to_json(self.metric_data_points))
            raise CloudProviderException(e, message)
        except Exception as e:
            raise e
