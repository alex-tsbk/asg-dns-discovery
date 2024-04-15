from app.config.env_configuration_service import EnvironmentConfigurationService
from app.utils.di import DIContainer, DILifetimeScope

from .instance_metadata_interface import InstanceMetadataInterface
from .instance_metadata_resolver_interface import InstanceMetadataResolverInterface
from .internal.instance_metadata_service import InstanceMetadataService
from .internal.resolvers.dns_instance_metadata_resolver import DnsInstanceMetadataResolver
from .internal.resolvers.ip_instance_metadata_resolver import IpInstanceMetadataResolver
from .internal.resolvers.tag_instance_metadata_resolver import TagInstanceMetadataResolver


def register_services(di_container: DIContainer, env_config_service: EnvironmentConfigurationService):
    """Registers services concrete implementations in the DI container.

    Args:
        di_container (DIContainer): DI container
    """
    # Register resolvers
    di_container.register(
        InstanceMetadataResolverInterface, DnsInstanceMetadataResolver, lifetime=DILifetimeScope.SCOPED, name="dns"
    )
    di_container.register(
        InstanceMetadataResolverInterface, IpInstanceMetadataResolver, lifetime=DILifetimeScope.SCOPED, name="ip"
    )
    di_container.register(
        InstanceMetadataResolverInterface, TagInstanceMetadataResolver, lifetime=DILifetimeScope.SCOPED, name="tag"
    )

    # Register metadata service
    di_container.register(InstanceMetadataInterface, InstanceMetadataService, lifetime=DILifetimeScope.SCOPED)
