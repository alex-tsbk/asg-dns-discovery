import abc


class MetricsInterface(metaclass=abc.ABCMeta):
    """Defines interface for metrics service implementations"""

    @abc.abstractmethod
    def reset(self):
        """Resets the metrics service to a clean state"""
        pass

    @abc.abstractmethod
    def record_data_point(self, metric_name: str, metric_value: int, description: str = "", metric_unit: str = "Count"):
        """Record a metric data point for later publishing

        Args:
            metric_name (str): name of metric
            metric_value (int): value of metric
            description (str, optional): description of metric. Defaults to "".
            metric_unit (str, optional): unit of metric. Defaults to "Count".
        """
        pass

    @abc.abstractmethod
    def record_dimension(self, metric_name: str, metric_value: str, description: str = ""):
        """Record a metric dimension for later use in metric publishing

        Args:
            metric_name (str): name of metric dimension
            metric_value (str): value of metric dimension
            description (str, optional): description of metric. Defaults to "".
        """
        pass

    @abc.abstractmethod
    def publish_metrics(self) -> bool:
        """Publish all recorded metrics to the metrics service

        Returns:
            bool: True if metrics were successfully published, False otherwise
        """
        pass
