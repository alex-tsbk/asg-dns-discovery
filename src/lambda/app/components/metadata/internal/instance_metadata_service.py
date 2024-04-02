from abc import ABC, abstractmethod
from typing import NoReturn

from app.components.lifecycle.models.lifecycle_event_model import LifecycleEventModel, LifecycleTransition
from app.components.metadata.instance_metadata_interface import InstanceMetadataInterface
from app.components.metadata.models.metadata_result_model import MetadataResultModel
from app.config.models.scaling_group_dns_config import ScalingGroupConfiguration
from app.components.metadata.instance_metadata_resolver_interface import InstanceMetadataResolverInterface
from app.utils.di import Injectable, NamedInjectable


class InstanceMetadataService(InstanceMetadataInterface):
    """Base class for concrete implementations of services resolving values from instance metadata."""

    def __init__(
        self,
        instance_metadata_resolver: Injectable[
            InstanceMetadataResolverInterface, NamedInjectable("instance-resolver")  # noqa: F821
        ],
        scaling_group_metadata_resolver: Injectable[
            InstanceMetadataResolverInterface, NamedInjectable("scaling-group-resolver")  # noqa: F821
        ],
    ) -> NoReturn:
        self.instance_metadata_resolver = instance_metadata_resolver
        self.scaling_group_metadata_resolver = scaling_group_metadata_resolver

    def resolve_value(
        self,
        lifecycle_event: LifecycleEventModel,
        value_source: str,
    ) -> list[MetadataResultModel]:
        """Resolves the value(s) from instance(s) metadata.

        Args:
            sg_config_item (ScalingGroupConfiguration): The scaling group configuration item.
            lifecycle_event (LifecycleEventModel): The lifecycle event for which to resolve the value.

        Returns:
            list[MetadataResultModel]: The values resolved.

        Remarks:
            There are few supported sources for the metadata value:
            - 'ip-v4:public|private' - will use public/private IP v4 of the instance.
            - 'ip-v6:public|private' - will use public/private IP v6 of the instance.
            - 'dns:public|private' - will use public/private DNS name of the instance
            - 'tag:<tag_name>' - where <tag_name> is the name of the tag to use as the source for the DNS record value.
        """
        # Don't resolve instances for unsupported transitions
        if lifecycle_event.transition not in self.supported_transitions:
            return []

        # Resolve metadata resolver based on the lifecycle transition
        metadata_resolver: InstanceMetadataResolverInterface = None
        # Source of the metadata value.
        # When lifecycle transition is LAUNCHING or DRAINING, this will hold the instance ID.
        # When lifecycle transition is RECONCILING, this will hold the name of the scaling group.
        source: str = None

        # Based on the lifecycle transition, resolve the metadata resolver and source
        if lifecycle_event.transition in [LifecycleTransition.LAUNCHING, LifecycleTransition.DRAINING]:
            metadata_resolver = self.instance_metadata_resolver
            source = lifecycle_event.instance_id

        if lifecycle_event.transition in [LifecycleTransition.RECONCILING]:
            metadata_resolver = self.scaling_group_metadata_resolver
            source = sg_config_item.scaling_group_name

        match sg_config_item.dns_config.value_source.split(":"):
            case [source, value] if source in ["ip", "ip-v4", "ip-v6"]:
                ip_version = "v4"
                if "-" in source:
                    source, ip_version = source.split("-")
                return metadata_resolver.resolve_ip_values(source, value, ip_version)
            case [source, value] if source == "tag":
                return metadata_resolver.resolve_tag_values(source, value)
            case [source, value] if source == "dns":
                return metadata_resolver.resolve_dns_values(source, value)
            case _:
                return None

    @property
    @staticmethod
    def supported_transitions():
        """Lifecycle transitions supported by the service."""
        return [
            LifecycleTransition.LAUNCHING,
            LifecycleTransition.DRAINING,
            LifecycleTransition.RECONCILING,
        ]
