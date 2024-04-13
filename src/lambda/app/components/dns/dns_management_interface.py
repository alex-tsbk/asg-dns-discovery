import abc

from app.components.dns.models.dns_change_command import DnsChangeCommand

from .models.dns_change_request_model import DnsChangeRequestModel
from .models.dns_change_response_model import DnsChangeResponseModel


class DnsManagementInterface(metaclass=abc.ABCMeta):
    """Interface for managing DNS records."""

    @abc.abstractmethod
    def generate_change_request(self, dns_change_command: DnsChangeCommand) -> DnsChangeRequestModel:
        """Generate a change request to update the DNS record based on the command.

        Args:
            dns_change_command [DnsChangeRequestCommand]: The command describing to perform the DNS change request.

        Returns:
            DnsChangeRequestModel: The model that represents the change set to update the value of the DNS record.
        """
        pass

    @abc.abstractmethod
    def apply_change_request(self, change_request: DnsChangeRequestModel) -> DnsChangeResponseModel:
        """Applies the change request to the DNS record.

        Args:
            change_request [DnsChangeRequestModel]: The change request model.

        Returns:
            DnsChangeResponseModel: The model that represents the response of the change request.
        """
        pass
