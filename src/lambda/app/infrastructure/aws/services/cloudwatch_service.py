from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

import boto3
from app.infrastructure.aws import boto_config
from app.utils.exceptions import CloudProviderException
from app.utils.logging import get_logger
from app.utils.singleton import Singleton
from botocore.exceptions import ClientError

if TYPE_CHECKING:
    from mypy_boto3_cloudwatch import CloudWatchClient
    from mypy_boto3_cloudwatch.type_defs import MetricDatumTypeDef


class AwsCloudWatchService(metaclass=Singleton):
    """Service class for interacting with AWS CloudWatch."""

    def __init__(self):
        self.logger = get_logger()
        self.cloudwatch_client: CloudWatchClient = boto3.client("cloudwatch", config=boto_config.CONFIG)  # type: ignore

    def publish_metric_data(self, namespace: str, metric_data: Sequence[MetricDatumTypeDef]):
        """Publishes metric data to CloudWatch.

        Args:
            namespace (str): Namespace for the metric data to publish to.
            metric_data (list[dict]): List of metric data to publish.

        Raises:
            CloudProviderException: When call fails to underlying boto3 function, or any other error occurs.
        """
        try:
            self.cloudwatch_client.put_metric_data(Namespace=namespace, MetricData=metric_data)
        except ClientError as e:
            message = f"Error publishing metric data: {e}"
            raise CloudProviderException(e, message)
