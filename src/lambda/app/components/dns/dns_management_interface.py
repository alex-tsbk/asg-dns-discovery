import abc

from app.components.lifecycle.models.lifecycle_event_model import LifecycleEventModel
from app.config.models.scaling_group_dns_config import ScalingGroupConfiguration

from .models.dns_change_request_model import DnsChangeRequestModel
from .models.dns_change_response_model import DnsChangeResponseModel


class DnsManagementInterface(metaclass=abc.ABCMeta):
    """Interface for managing DNS records."""

    @abc.abstractmethod
    def generate_change_request(
        self, sg_config_item: ScalingGroupConfiguration, lifecycle_event: LifecycleEventModel
    ) -> DnsChangeRequestModel:
        """For a given set of input parameters, generate a change set to update the values for DNS record.

        Args:
            sg_config_item [str]: The Scaling Group DNS configuration item.
            lifecycle_event [LifecycleEventModel]: The lifecycle event.

        Returns:
            DnsChangeRequestModel: The model that represents the change set to update the value of the DNS record.
        """
        pass

    @abc.abstractmethod
    def apply_change_request(
        self, sg_config_item: ScalingGroupConfiguration, change_request: DnsChangeRequestModel
    ) -> DnsChangeResponseModel:
        """Apply the change request to the DNS record.

        Args:
            sg_config_item [ScalingGroupConfiguration]: The Scaling Group DNS configuration item.
            change_request [DnsChangeRequestModel]: The change request model.

        Returns:
            DnsChangeResponseModel: The model that represents the response of the change request.
        """
        pass
