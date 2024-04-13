from typing import TYPE_CHECKING

from app.components.dns.dns_management_interface import DnsManagementInterface
from app.components.dns.internal.aws.aws_dns_change_request_model import AwsDnsChangeRequestModel
from app.components.dns.models.dns_change_request_model import (
    IGNORED_DNS_CHANGE_REQUEST,
    DnsChangeRequestAction,
    DnsChangeRequestModel,
    DnsRecordType,
)
from app.components.dns.models.dns_change_response_model import DnsChangeResponseModel
from app.components.discovery.instance_discovery_interface import InstanceDiscoveryInterface
from app.config.models.dns_record_config import DnsRecordEmptyValueMode, DnsRecordMappingMode
from app.infrastructure.aws.route53_service import Route53Service
from app.utils.logging import get_logger
from app.utils.serialization import to_json

from app.components.dns.models.dns_change_command import DnsChangeCommand, DnsChangeCommandAction

if TYPE_CHECKING:
    from mypy_boto3_route53.type_defs import ResourceRecordSetTypeDef


class AwsDnsManagementService(DnsManagementInterface):
    """Service for managing DNS records in AWS environment."""

    def __init__(
        self,
        route_53_service: Route53Service,
        instance_discovery_service: InstanceDiscoveryInterface,
    ) -> None:
        self.logger = get_logger()
        self.route_53_service = route_53_service
        self.instance_discovery_service = instance_discovery_service

    def generate_change_request(self, dns_change_command: DnsChangeCommand) -> DnsChangeRequestModel:
        """Generate a change request to update the DNS record based on the command.

        Args:
            dns_change_command [DnsChangeRequestCommand]: The command describing to perform the DNS change request.

        Returns:
            DnsChangeRequestModel: The model that represents the change set to update the value of the DNS record.
        """
        dns_config = dns_change_command.dns_config
        record_name = dns_config.record_name
        hosted_zone_id = dns_config.dns_zone_id
        record_type = DnsRecordType(dns_config.record_type)

        record_name = self._normalize_record_name(record_name, hosted_zone_id)
        record = self.route_53_service.read_record(hosted_zone_id, record_name, record_type.value)
        if not record:
            return IGNORED_DNS_CHANGE_REQUEST

        if dns_change_command.action == DnsChangeCommandAction.APPEND:
            return self._handle_launching(dns_change_command, record)

        if dns_change_command.action == DnsChangeCommandAction.REMOVE:
            return self._handle_draining(dns_change_command, record)

        if dns_change_command.action == DnsChangeCommandAction.REPLACE:
            return self._handle_reconciliation(dns_change_command, record)

        # If the lifecycle event transition is not supported, ignore the change
        return IGNORED_DNS_CHANGE_REQUEST

    def apply_change_request(self, change_request: DnsChangeRequestModel) -> DnsChangeResponseModel:
        """Apply the change request to the DNS record.

        Args:
            change_request [DnsChangeRequestModel]: The change request to apply.
        """
        hosted_zone_id = change_request.hosted_zone_id
        # Build and convert change request to AWS Route53 format
        change = change_request.build_change().get_change()
        self.logger.debug(f"Applying change request for hosted zone: {hosted_zone_id} -> {to_json(change)}")
        try:
            successful = self.route_53_service.change_resource_record_sets(
                hosted_zone_id,
                change,  # type: ignore -- underlying boto3 type not available at runtime
            )
            return DnsChangeResponseModel(success=successful)
        except Exception as e:
            self.logger.error(f"Error applying change request: {str(e)}")
            return DnsChangeResponseModel(success=False)

    def _normalize_record_name(self, record_name: str, hosted_zone_id: str) -> str:
        """Normalize record name by appending hosted zone name if not present.

        Args:
            record_name [str]: Record name to be normalized.
            hosted_zone_id [str]: Hosted zone ID.

        Returns:
            str: Normalized record name
        """
        hosted_zone_name = self.route_53_service.get_hosted_zone_name(hosted_zone_id)
        record_name = record_name.rstrip(".")
        if not record_name.endswith(hosted_zone_name):
            record_name = f"{record_name}.{hosted_zone_name}"
        return record_name

    def _handle_draining(
        self, dns_change_command: DnsChangeCommand, record: ResourceRecordSetTypeDef
    ) -> DnsChangeRequestModel:
        """
        Handle the draining lifecycle event.

        Args:
            dns_change_command [DnsChangeCommand]: The DNS change command.
            record [dict]: The Route53 record.

        Returns:
            DnsChangeRequestModel: The change request model.
        """
        if not record:
            return IGNORED_DNS_CHANGE_REQUEST

        # Extract the current values from the record
        current_record_values: list[str] = self._extract_values_from_route53_record(record)
        removable_dns_record_values: list[str] = self._extract_dns_record_values(dns_change_command)
        if not current_record_values:
            return IGNORED_DNS_CHANGE_REQUEST

        # Compute values that should be left in the record
        desired_dns_record_values = [
            value for value in current_record_values if value not in removable_dns_record_values
        ]
        # Check if any values are left
        has_values = bool(desired_dns_record_values)
        # Create a base change request model response
        dns_change_request_model_response = AwsDnsChangeRequestModel.from_dns_record_config(
            dns_change_command.dns_config
        )
        # Decide how to handle thi
        if not has_values:
            # Basically, do nothing if no values are left
            if dns_change_command.dns_config.empty_mode == DnsRecordEmptyValueMode.KEEP:
                return IGNORED_DNS_CHANGE_REQUEST
            # Delete the record if no values are left
            if dns_change_command.dns_config.empty_mode == DnsRecordEmptyValueMode.DELETE:
                dns_change_request_model_response.action = DnsChangeRequestAction.DELETE
                dns_change_request_model_response.record_values = current_record_values
                return dns_change_request_model_response
            # Use a fixed value if no values are left
            if dns_change_command.dns_config.empty_mode == DnsRecordEmptyValueMode.FIXED:
                dns_change_request_model_response.action = DnsChangeRequestAction.UPDATE
                dns_change_request_model_response.record_values = [dns_change_command.dns_config.empty_mode_value]
                return dns_change_request_model_response

        # If any values are left, update the record
        dns_change_request_model_response.action = DnsChangeRequestAction.UPDATE
        dns_change_request_model_response.record_values = desired_dns_record_values
        return dns_change_request_model_response

    def _handle_launching(
        self, dns_change_command: DnsChangeCommand, record: ResourceRecordSetTypeDef
    ) -> DnsChangeRequestModel:
        """Handle the launching lifecycle event.

        Args:
            dns_change_command [DnsChangeCommand]: The DNS change command.
            record [dict]: The Route53 record.

        Returns:
            DnsChangeRequestModel: The change request model.
        """
        if not dns_change_command.values:
            # If no resolved values, ignore the change
            return IGNORED_DNS_CHANGE_REQUEST

        dns_config = dns_change_command.dns_config

        current_dns_record_values: list[str] = self._extract_values_from_route53_record(record)
        additional_dns_record_values: list[str] = self._extract_dns_record_values(dns_change_command)

        # If resolved_values a subset of current_record_values, ignore the change
        # (or both sets are empty, which is also an edge case)
        if set(additional_dns_record_values).issubset(set(current_dns_record_values)):
            return IGNORED_DNS_CHANGE_REQUEST

        # Augment current record values with resolved values
        desired_dns_record_values: list[str] = []
        if dns_config.mode == DnsRecordMappingMode.SINGLE_LATEST:
            desired_dns_record_values = additional_dns_record_values

        if dns_config.mode == DnsRecordMappingMode.MULTIVALUE:
            desired_dns_record_values = current_dns_record_values.copy()
            desired_dns_record_values.extend(additional_dns_record_values)

        if not desired_dns_record_values:
            return IGNORED_DNS_CHANGE_REQUEST

        # Create a change request
        action = DnsChangeRequestAction.CREATE if not record else DnsChangeRequestAction.UPDATE

        return AwsDnsChangeRequestModel(
            action=action,
            hosted_zone_id=dns_config.dns_zone_id,
            record_name=dns_config.record_name,
            record_type=DnsRecordType(dns_config.record_type),
            record_ttl=dns_config.record_ttl,
            record_weight=dns_config.srv_weight,
            record_priority=dns_config.srv_priority,
            record_port=dns_config.srv_port,
            record_values=desired_dns_record_values,
        )

    def _handle_reconciliation(
        self, dns_change_command: DnsChangeCommand, record: ResourceRecordSetTypeDef
    ) -> DnsChangeRequestModel:
        """Handle the reconciliation lifecycle event.

        Args:
            dns_change_command [DnsChangeCommand]: The DNS change command.
            record [dict]: The Route53 record.

        Returns:
            DnsChangeRequestModel: The change request model.
        """
        dns_config = dns_change_command.dns_config

        current_dns_record_values: list[str] = self._extract_values_from_route53_record(record)
        desired_dns_record_values: list[str] = self._extract_dns_record_values(dns_change_command)

        # If current values are the same as desired values, ignore the change
        if set(current_dns_record_values) == set(desired_dns_record_values):
            return IGNORED_DNS_CHANGE_REQUEST

        # If resolved values are different from current values, create a change request
        action = DnsChangeRequestAction.UPDATE if record else DnsChangeRequestAction.CREATE

        if not desired_dns_record_values:
            # Basically, we can't have DNS record without values.
            # TODO: Revisit this edge case
            return IGNORED_DNS_CHANGE_REQUEST

        return AwsDnsChangeRequestModel(
            action=action,
            hosted_zone_id=dns_config.dns_zone_id,
            record_name=dns_config.record_name,
            record_type=DnsRecordType(dns_config.record_type),
            record_ttl=dns_config.record_ttl,
            record_weight=dns_config.srv_weight,
            record_priority=dns_config.srv_priority,
            record_port=dns_config.srv_port,
            record_values=desired_dns_record_values,
        )

    def _extract_values_from_route53_record(self, record: ResourceRecordSetTypeDef) -> list[str]:
        """Extract values from Route53 record DNS record.

        Returns:
            list[str]: The DNS record values sorted in ascending order.
        """
        if not record or "ResourceRecords" not in record:
            return []
        values = [value["Value"] for value in record["ResourceRecords"]]
        return sorted(values)

    @staticmethod
    def _extract_dns_record_values(dns_change_command: DnsChangeCommand) -> list[str]:
        """Extracts the desired DNS record values from the DNS change command.

        Args:
            dns_change_command (DnsChangeCommand): The DNS change command.

        Returns:
            list[str]: The desired DNS record values sorted in ascending order.
        """
        dns_config = dns_change_command.dns_config
        desired_record_values: list[str] = []
        if dns_config.mode == DnsRecordMappingMode.MULTIVALUE:
            desired_record_values = sorted([value_item.dns_value for value_item in dns_change_command.values])

        if dns_config.mode == DnsRecordMappingMode.SINGLE_LATEST:
            # Get the most recent operational instance
            most_recent_operational_instance = sorted(
                dns_change_command.values,
                key=lambda x: x.launch_time,
                reverse=True,
            )[0]
            desired_record_values = [most_recent_operational_instance.dns_value]

        return desired_record_values
