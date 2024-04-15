from abc import ABCMeta, abstractmethod

from app.entities.instance_entity import Instance
from app.entities.scaling_group_entity import ScalingGroup


class InstanceDiscoveryInterface(metaclass=ABCMeta):
    """Interface for discovering information about instances."""

    @abstractmethod
    def describe_instances(self, *instances_ids: str) -> list[Instance]:
        """Describe the instances with the given IDs.

        Args:
            *instances_ids (str): The IDs of the instances to describe.

        Returns:
            list[Instance]: Models describing the instances.
        """
        pass

    @abstractmethod
    def describe_scaling_groups(self, *scaling_groups_names: str) -> list[ScalingGroup]:
        """Get the instances in the scaling group.

        Args:
            *scaling_groups_names (str): The names of the scaling groups to describe.

        Returns:
            list[ScalingGroup]: Models describing scaling groups and related instances.
        """
        pass
