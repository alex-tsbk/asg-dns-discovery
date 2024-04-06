from app.components.metadata.instance_metadata_resolver_interface import InstanceMetadataResolverInterface
from app.components.metadata.models.metadata_result_model import MetadataResultModel
from app.components.metadata.models.metadata_value_source_model import MetadataValueSourceModel
from app.domain.models.instance_model import InstanceModel
from app.utils import strings
from app.utils.exceptions import BusinessException
from app.utils.logging import get_logger


class IpInstanceMetadataResolver(InstanceMetadataResolverInterface):
    def __init__(self) -> None:
        self.logger = get_logger()

    def resolve(self, instance: InstanceModel, value_source: MetadataValueSourceModel) -> MetadataResultModel:
        """Resolves values from source metadata.

        Args:
            instance (InstanceModel): The instance model.
            value_source (MetadataValueSourceModel): The value source model.

        Returns:
            MetadataResultModel: Model containing the resolved value.
        """
        if not strings.alike(value_source.type, "ip"):
            raise BusinessException(
                f"Resolver {self.__class__.__name__} does not support value source type {value_source.type}"
            )
        # Prepare the result model
        result = MetadataResultModel(instance.instance_id, "", str(value_source))
        # Resolve IP value based on the type and sub-type
        if strings.alike(value_source.sub_type, "v4") or value_source.sub_type == "":  # Default to v4 if not specified
            if strings.alike(value_source.attribute, "private"):
                result.value = instance.metadata.private_ip_v4
            if strings.alike(value_source.attribute, "public"):
                result.value = instance.metadata.public_ip_v4
        if strings.alike(value_source.sub_type, "v6"):
            if strings.alike(value_source.attribute, "private"):
                result.value = instance.metadata.private_ip_v6
            if strings.alike(value_source.attribute, "public"):
                result.value = instance.metadata.public_ip_v6
        self.logger.debug(f"For value source {value_source}, resolved value: {result.value}")
        return result
