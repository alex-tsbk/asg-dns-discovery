from abc import ABCMeta, abstractmethod

from app.components.metadata.models.metadata_result_model import MetadataResultModel
from app.components.metadata.models.metadata_value_source_model import MetadataValueSourceModel
from app.domain.entities.instance import Instance


class InstanceMetadataResolverInterface(metaclass=ABCMeta):
    """Interface for resolving value from instance metadata."""

    @abstractmethod
    def resolve(self, instance: Instance, value_source: MetadataValueSourceModel) -> MetadataResultModel:
        """Resolves values from source metadata.

        Args:
            instance (Instance): The instance model.
            value_source (MetadataValueSourceModel): The value source model.

        Returns:
            MetadataResultModel: Model containing the resolved value.
        """
        pass
