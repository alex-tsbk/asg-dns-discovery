from app.components.metadata.instance_metadata_resolver_interface import InstanceMetadataResolverInterface
from app.components.metadata.models.metadata_result_model import MetadataResultModel
from app.components.metadata.models.metadata_value_source_model import MetadataValueSourceModel
from app.entities.instance import Instance
from app.utils import strings
from app.utils.exceptions import BusinessException
from app.utils.logging import get_logger


class TagInstanceMetadataResolver(InstanceMetadataResolverInterface):
    def __init__(self) -> None:
        self.logger = get_logger()

    def resolve(self, instance: Instance, value_source: MetadataValueSourceModel) -> MetadataResultModel:
        """Resolves values from source metadata.

        Args:
            instance (Instance): The instance model.
            value_source (MetadataValueSourceModel): The value source model.

        Returns:
            MetadataResultModel: Model containing the resolved value.
        """
        if not strings.alike(value_source.type, "tag"):
            raise BusinessException(
                f"Resolver {self.__class__.__name__} does not support value source type {value_source.type}"
            )
        # Resolve tag value based on the attribute and sub-type
        value = instance.get_tag_value(value_source.attribute, not strings.alike(value_source.sub_type, "ci"))
        result = MetadataResultModel(instance.instance_id, value, str(value_source))
        self.logger.debug(f"For value source {value_source}, resolved value: {result.value}")
        return result
