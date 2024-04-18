from app.components.metadata.instance_metadata_resolver_interface import InstanceMetadataResolverInterface
from app.components.metadata.models.metadata_result_model import MetadataResultModel
from app.components.metadata.models.metadata_value_source_model import MetadataValueSourceModel
from app.entities.instance import Instance
from app.utils import strings
from app.utils.exceptions import BusinessException
from app.utils.logging import get_logger


class DnsInstanceMetadataResolver(InstanceMetadataResolverInterface):
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
        if not strings.alike(value_source.type, "dns"):
            raise BusinessException(
                f"Resolver {self.__class__.__name__} does not support value source type {value_source.type}"
            )
        # Prepare the result model
        result = MetadataResultModel(instance.instance_id, "", str(value_source))
        # Resolve DNS value based on the attribute
        if strings.alike(value_source.attribute, "private"):
            result.value = instance.metadata.private_dns
        if strings.alike(value_source.attribute, "public"):
            result.value = instance.metadata.public_dns
        self.logger.debug(f"For value source {value_source}, resolved value: {result.value}")
        return result
