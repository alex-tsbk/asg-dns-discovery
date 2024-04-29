from app.components.metadata.instance_metadata_interface import InstanceMetadataInterface
from app.components.metadata.instance_metadata_resolver_interface import InstanceMetadataResolverInterface
from app.components.metadata.models.metadata_result_model import MetadataResultModel
from app.components.metadata.models.metadata_value_source_model import MetadataValueSourceModel
from app.domain.entities.instance import Instance
from app.utils.di import DIContainer
from app.utils.exceptions import BusinessException


class InstanceMetadataService(InstanceMetadataInterface):
    """Base class for concrete implementations of services resolving values from instance metadata."""

    def __init__(self, di_container: DIContainer):
        self.di_container = di_container

    def resolve_value(self, model: Instance, value_source: str) -> MetadataResultModel:
        """Resolves the value(s) from instance(s) metadata.

        Args:
            model (Instance): The instance model.
            value_source (str): The source of the metadata value.

        Returns:
            MetadataResultModel: The value resolved.
        """
        value_source_model = MetadataValueSourceModel.from_string(value_source)

        # Resolve metadata resolver based on the value_source_model type
        try:
            metadata_resolver = self.di_container.resolve(InstanceMetadataResolverInterface, value_source_model.type)
            return metadata_resolver.resolve(model, value_source_model)
        except Exception as e:
            raise BusinessException(f"No resolver for {value_source_model.type} value source type") from e
