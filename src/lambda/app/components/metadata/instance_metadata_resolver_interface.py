from abc import ABCMeta, abstractmethod
from typing import Literal

from app.components.metadata.models.metadata_result_model import MetadataResultModel


class InstanceMetadataResolverInterface(metaclass=ABCMeta):
    """Interface for resolving value from instance metadata."""

    @abstractmethod
    def resolve_ip_values(
        source: str,
        ip_type: Literal["public", "private"],
        ip_version: Literal["v4", "v6"],
    ) -> list[MetadataResultModel]:
        """Resolves IP values from source metadata.

        Args:
            source: Source of the metadata. This could be instance-id, name of scaling group, etc.
                Whatever implements this interface should know how to interpret this value.
            ip_type (str): IP value to use - public or private.
            ip_version (str): IP version to use - IP v4 or IP v6.

        Returns:
            list[MetadataResultModel]: The list containing information about values resolved.
        """
        pass

    @abstractmethod
    def resolve_tag_values(
        self,
        source: str,
        tag_name: str,
    ) -> list[MetadataResultModel]:
        """Resolves tag values from source metadata.

        Args:
            source: Source of the metadata. This could be instance-id, name of scaling group, etc.
                Whatever implements this interface should know how to interpret this value.
            tag_name (str): Name of the tag to resolve value from.

        Returns:
            list[MetadataResultModel]: The list containing information about values resolved.
        """
        pass

    @abstractmethod
    def resolve_dns_values(
        self,
        source: str,
        dns_type: Literal["public", "private"],
    ) -> list[MetadataResultModel]:
        """Resolves DNS values from source metadata.

        Args:
            source: Source of the metadata. This could be instance-id, name of scaling group, etc.
                Whatever implements this interface should know how to interpret this value.
            dns_type (str): DNS value to use - public or private.

        Returns:
            list[MetadataResultModel]: The list containing information about values resolved.
        """
        pass
