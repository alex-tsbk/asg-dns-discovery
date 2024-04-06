from abc import ABCMeta, abstractmethod

from app.domain.models.instance_model import InstanceModel

from .models.metadata_result_model import MetadataResultModel


class InstanceMetadataInterface(metaclass=ABCMeta):
    """Interface for resolving value from instance metadata."""

    @abstractmethod
    def resolve_value(self, model: InstanceModel, value_source: str) -> MetadataResultModel:
        """Resolves the value(s) from instance(s) metadata.

        Args:
            model (InstanceModel): The instance model.
            value_source (str): The source of the metadata value.

        Returns:
            MetadataResultModel: The value resolved.
        """
        pass
