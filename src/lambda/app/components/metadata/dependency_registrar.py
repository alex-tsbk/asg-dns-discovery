from app.utils.di import DIContainer

from .instance_metadata_interface import InstanceMetadataInterface
from .instance_metadata_resolver_interface import InstanceMetadataResolverInterface
from .internal.instance_metadata_service import InstanceMetadataService
from .internal.resolvers.dns_instance_metadata_resolver import DnsInstanceMetadataResolver
from .internal.resolvers.ip_instance_metadata_resolver import IpInstanceMetadataResolver
from .internal.resolvers.tag_instance_metadata_resolver import TagInstanceMetadataResolver


def register_services(di_container: DIContainer):
    """Registers services concrete implementations in the DI container.

    Args:
        di_container (DIContainer): DI container
    """
    # Register resolvers
    di_container.register(InstanceMetadataResolverInterface, DnsInstanceMetadataResolver, name="dns")
    di_container.register(InstanceMetadataResolverInterface, IpInstanceMetadataResolver, name="ip")
    di_container.register(InstanceMetadataResolverInterface, TagInstanceMetadataResolver, name="tag")

    # Register metadata service
    di_container.register(InstanceMetadataInterface, InstanceMetadataService)
