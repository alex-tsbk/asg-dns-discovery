from abc import ABCMeta, abstractmethod

from app.domain.models.instance_model import InstanceModel


class InstanceDiscoveryInterface(metaclass=ABCMeta):
    """Interface for discovering information about instances."""

    @abstractmethod
    def describe_instances(self, *instances_ids: str) -> list[InstanceModel]:
        """Describe the instances with the given IDs.

        Args:
            *instances_ids (str): The IDs of the instances to describe.

        Returns:
            list[InstanceModel]: Models describing the instances.
        """
        pass

    @abstractmethod
    def describe_scaling_groups(self, *scaling_groups_names: str) -> list[InstanceModel]:
        """Get the instances in the scaling group.

        Args:
            *scaling_groups_names (str): The names of the scaling groups to describe.

        Returns:
            list[InstanceModel]: Models describing the instances.
        """
        pass
