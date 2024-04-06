from abc import ABCMeta, abstractmethod

from app.components.metadata.models.metadata_result_model import MetadataResultModel
from app.components.metadata.models.metadata_value_source_model import MetadataValueSourceModel
from app.domain.models.instance_model import InstanceModel


class InstanceMetadataResolverInterface(metaclass=ABCMeta):
    """Interface for resolving value from instance metadata."""

    @abstractmethod
    def resolve(self, instance: InstanceModel, value_source: MetadataValueSourceModel) -> MetadataResultModel:
        """Resolves values from source metadata.

        Args:
            instance (InstanceModel): The instance model.
            value_source (MetadataValueSourceModel): The value source model.

        Returns:
            MetadataResultModel: Model containing the resolved value.
        """
        pass
