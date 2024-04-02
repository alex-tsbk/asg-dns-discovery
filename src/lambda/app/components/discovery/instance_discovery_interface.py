from abc import ABCMeta, abstractmethod
from typing import Literal

from app.components.metadata.models.metadata_result_model import MetadataResultModel


class InstanceDiscoveryInterface(metaclass=ABCMeta):
    """Interface for discovering instances."""

    @abstractmethod
    def get_instance(instance_id: str) -> MetadataResultModel:
        """Get the instance by its ID.

        Args:
            instance_id (str): The ID of the instance.

        Returns:
            MetadataResultModel: The instance metadata.
        """
        pass

    @abstractmethod
    def get_scaling_group_instances(scaling_group_name: str) -> list[MetadataResultModel]:
        """Get the instances in the scaling group.

        Args:
            scaling_group_name (str): The name of the scaling group.

        Returns:
            list[MetadataResultModel]: The instances metadata.
        """
        pass
