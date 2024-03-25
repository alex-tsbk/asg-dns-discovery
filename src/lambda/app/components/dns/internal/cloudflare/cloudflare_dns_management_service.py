from app.components.dns.dns_management_interface import DnsManagementInterface
from app.components.dns.internal.cloudflare.cloudflare_dns_change_request_model import CloudflareDnsChangeRequestModel
from app.components.dns.models.dns_change_request_model import DnsChangeRequestAction, DnsChangeRequestModel
from app.components.dns.models.dns_change_response_model import DnsChangeResponseModel
from app.components.lifecycle.models.lifecycle_event_model import LifecycleEventModel, LifecycleTransition
from app.components.metadata.instance_metadata_interface import InstanceMetadataInterface
from app.config.models.scaling_group_dns_config import DnsRecordMappingMode, ScalingGroupConfiguration
from app.infrastructure.cloudflare.cloudflare_service import CloudflareService
from app.utils.logging import get_logger
from app.utils.serialization import to_json


class CloudflareDnsManagementService(DnsManagementInterface):
    """Service for managing DNS records in AWS environment."""

    def __init__(self, dns_service: CloudflareService, instance_metadata_service: InstanceMetadataInterface) -> None:
        self.logger = get_logger()
        self.dns_service = dns_service
        self.instance_metadata_service = instance_metadata_service

    def generate_change_request(
        self, sg_config_item: ScalingGroupConfiguration, lifecycle_event: LifecycleEventModel
    ) -> DnsChangeRequestModel:
        """For a given set of input parameters, generate a change set to update the values for DNS record.

        Args:
            sg_config_item [str]: The Scaling Group DNS configuration item.
            lifecycle_event [LifecycleEventModel]: The lifecycle event.

        Returns:
            DnsChangeRequestModel: The model that represents the change set to update the value of the DNS record.

        Raises:
            NotImplementedError: If the lifecycle event transition is not supported.
        """
        # record_name = sg_config_item.dns_config.record_name
        # hosted_zone_id = sg_config_item.dns_config.dns_zone_id
        # record_type = sg_config_item.dns_config.record_type

        # record_name = self._normalize_record_name(record_name, hosted_zone_id)
        # record = self.dns_service.read_record(hosted_zone_id, record_name, record_type)
        # resolved_values = self.instance_metadata_service.resolve_value(sg_config_item, lifecycle_event)

        # if lifecycle_event.transition == LifecycleTransition.DRAINING:
        #     return self._handle_draining(sg_config_item, record, resolved_values)

        # if lifecycle_event.transition == LifecycleTransition.LAUNCHING:
        #     return self._handle_launching(sg_config_item, record, resolved_values)

        # if lifecycle_event.transition == LifecycleTransition.RECONCILING:
        #     return self._handle_reconciliation(sg_config_item, record, resolved_values)

        # # If the lifecycle event transition is not supported, ignore the change
        # return AwsDnsChangeRequestModel(
        #     action=DnsChangeRequestAction.IGNORE, record_name=record_name, record_type=record_type
        # )
        pass

    def apply_change_request(
        self, sg_config_item: ScalingGroupConfiguration, change_request: DnsChangeRequestModel
    ) -> DnsChangeResponseModel:
        """Apply the change request to the DNS record.

        Args:
            sg_config_item [ScalingGroupConfiguration]: The Scaling Group DNS configuration item.
            change_request [DnsChangeRequestModel]: The change request to apply.
        """
        # hosted_zone_id = sg_config_item.dns_config.dns_zone_id
        # # Build and convert change request to AWS Route53 format
        # change = change_request.build_change().get_change()
        # self.logger.debug(f"Applying change request for hosted zone: {hosted_zone_id} -> {to_json(change)}")
        # self.dns_service.change_resource_record_sets(hosted_zone_id, change)
        pass

    def _normalize_record_name(self, record_name: str, hosted_zone_id: str) -> str:
        """Normalize record name by appending hosted zone name if not present.

        Args:
            record_name [str]: Record name to be normalized.
            hosted_zone_id [str]: Hosted zone ID.

        Returns:
            str: Normalized record name
        """
        # hosted_zone_name = self.dns_service.get_hosted_zone_name(hosted_zone_id)
        # record_name = record_name.rstrip(".")
        # if not record_name.endswith(hosted_zone_name):
        #     record_name = f"{record_name}.{hosted_zone_name}"
        # return record_name
        pass

    def _handle_draining(
        self, sg_config_item: ScalingGroupConfiguration, record: dict, resolved_values: list[str]
    ) -> DnsChangeRequestModel:
        """
        Handle the draining lifecycle event.

        Args:
            sg_config_item [ScalingGroupConfiguration]: The Scaling Group DNS configuration item.
            record [dict]: The Route53 record.
            resolved_values [list[str]]: The resolved values for the current lifecycle.

        Returns:
            DnsChangeRequestModel: The change request model.
        """
        record_name = sg_config_item.dns_config.record_name
        record_type = sg_config_item.dns_config.record_type

        if not record:
            return CloudflareDnsChangeRequestModel(
                action=DnsChangeRequestAction.IGNORE,
                record_name=record_name,
                record_type=record_type,
            )
        # Extract the current values from the record
        current_record_values_original = self._extract_values_from_route53_record(sg_config_item, record)
        if not current_record_values_original:
            return CloudflareDnsChangeRequestModel(
                action=DnsChangeRequestAction.IGNORE,
                record_name=record_name,
                record_type=record_type,
            )
        # Create duplicate of the current values, to preserve the original values in case we need to remove the record
        # Also, since we're draining, we want to remove the resolved value from the record set
        current_record_values_altered = [
            value for value in current_record_values_original if value not in resolved_values
        ]
        # Check if any values are left
        has_values = bool(current_record_values_altered)
        # If no values are left, and DNS record is managed - we can't remove it,
        # only update it to the mock IP. Otherwise, Terraform will not be happy.
        if not has_values and sg_config_item.dns_config.managed_dns_record:
            has_values = True  # We need to update the record to the mock IP
            current_record_values_altered = [sg_config_item.dns_config.dns_mock_value]
        # Build common kwargs for change request
        change_request_kwargs = {
            "record_name": record_name,
            "record_type": record_type,
            "record_ttl": record["TTL"],
            "record_weight": sg_config_item.dns_config.record_weight,
            "record_priority": sg_config_item.dns_config.record_priority,
        }
        # If no values are left, delete the record.
        if not has_values:
            return CloudflareDnsChangeRequestModel(
                action=DnsChangeRequestAction.DELETE,
                record_values=current_record_values_original,  # Pass the original values to the change request for removal
                **change_request_kwargs,
            )
        # If any values are left, update the record
        return CloudflareDnsChangeRequestModel(
            action=DnsChangeRequestAction.UPDATE,
            record_values=current_record_values_altered,
            **change_request_kwargs,
        )

    def _handle_launching(
        self, sg_config_item: ScalingGroupConfiguration, record: dict, resolved_values: list[str]
    ) -> DnsChangeRequestModel:
        """Handle the launching lifecycle event.

        Args:
            sg_config_item [ScalingGroupConfiguration]: The Scaling Group DNS configuration item.
            record [dict]: The Route53 record.
            resolved_values [list[str]]: The resolved values for the current lifecycle.

        Returns:
            DnsChangeRequestModel: The change request model.
        """
        IGNORE_CHANGE_REQUEST = CloudflareDnsChangeRequestModel(
            action=DnsChangeRequestAction.IGNORE,
            record_name=sg_config_item.dns_config.record_name,
            record_type=sg_config_item.dns_config.record_type,
        )
        if not resolved_values:
            # If no resolved values, ignore the change
            return IGNORE_CHANGE_REQUEST

        current_record_values = self._extract_values_from_route53_record(sg_config_item, record)
        # If resolved_values a subset of current_record_values, ignore the change
        if set(resolved_values).issubset(set(current_record_values)):
            return IGNORE_CHANGE_REQUEST

        # Augment current record values with resolved values
        current_record_values.extend(resolved_values)
        # Remove duplicates
        current_record_values = list(set(current_record_values))
        # Create a change request
        action = DnsChangeRequestAction.CREATE if not record else DnsChangeRequestAction.UPDATE
        record_values = (
            current_record_values if sg_config_item.mode == DnsRecordMappingMode.MULTIVALUE else [resolved_values[0]]
        )
        return CloudflareDnsChangeRequestModel(
            action=action,
            record_values=record_values,
            record_name=sg_config_item.dns_config.record_name,
            record_type=sg_config_item.dns_config.record_type,
            record_ttl=sg_config_item.dns_config.record_ttl,
        )

    def _handle_reconciliation(
        self, sg_config_item: ScalingGroupConfiguration, record: dict, resolved_values: list[str]
    ) -> DnsChangeRequestModel:
        """Handle the reconciliation lifecycle event.

        Args:
            sg_config_item [ScalingGroupConfiguration]: The Scaling Group DNS configuration item.
            record [dict]: The Route53 record.
            resolved_values [list[str]]: The resolved values for the current lifecycle.

        Returns:
            DnsChangeRequestModel: The change request model.
        """
        IGNORE_CHANGE_REQUEST = CloudflareDnsChangeRequestModel(
            action=DnsChangeRequestAction.IGNORE,
            record_name=sg_config_item.dns_config.record_name,
            record_type=sg_config_item.dns_config.record_type,
        )
        current_record_values = self._extract_values_from_route53_record(sg_config_item, record)
        # If current values are the same as resolved values, ignore the change
        if current_record_values == resolved_values:
            return IGNORE_CHANGE_REQUEST
        # If resolved values are different from current values, create a change request
        action = DnsChangeRequestAction.UPDATE if record else DnsChangeRequestAction.CREATE
        record_values = (
            resolved_values if sg_config_item.mode == DnsRecordMappingMode.MULTIVALUE else [resolved_values[0]]
        )
        return CloudflareDnsChangeRequestModel(
            action=action,
            record_values=record_values,
            record_name=sg_config_item.dns_config.record_name,
            record_type=sg_config_item.dns_config.record_type,
            record_ttl=sg_config_item.dns_config.record_ttl,
        )

    def _extract_values_from_route53_record(self, sg_config_item: ScalingGroupConfiguration, record: dict) -> list[str]:
        """Extract values from Route53 record DNS record."""
        if not record or "ResourceRecords" not in record:
            return []
        values = [value["Value"] for value in record["ResourceRecords"]]
        # If managed DNS record and mock IP is in the values, remove it
        if sg_config_item.dns_config.managed_dns_record and sg_config_item.dns_config.dns_mock_value in values:
            values.remove(sg_config_item.dns_config.dns_mock_value)
        return values

    def remove_ip_from_record(
        self,
        hosted_zone_id: str,
        record_name: str,
        record_type: str,
        # If DNS record is managed - we can't remove it, only update
        managed_dns_record: bool,
        dns_mock_value: str,
        ip: str,
    ) -> bool:
        """Remove an IP from a record.

        Args:
            hosted_zone_id [str]: The ID of the hosted zone that contains the resource record sets that you want to change.
            record_name [str]: The name of the resource record set that you want to change.
            record_type [str]: The DNS record type.
            dns_mock_value [str]: The mock value used for DNS address to be removed from the record.
            ip [str]: The IP address to be removed from the record.

        Returns:
            bool: True if IP is removed from record, False otherwise
        """
        record_name = self._normalize_record_name(record_name, hosted_zone_id)
        record = self.dns_service.read_record(hosted_zone_id, record_name, record_type)
        if not record:
            return False
        # Preserve the original values in case we need to remove the record
        values_original = [value["Value"] for value in record["ResourceRecords"]]
        # Duplicate IPs stripping the IP to be removed and the mock IP
        values = [v for v in values_original if v != ip and v != dns_mock_value]
        should_update = values and values != values_original
        # Ensure we don't nuke the record if it's managed,'
        # otherwise Terraform will not be happy
        if not should_update and managed_dns_record:
            should_update = True
            values = [dns_mock_value]

        # If any values are left, update the record, otherwise delete it
        change_batch = DnsChangeRequestModel(
            action="UPSERT" if should_update else "DELETE",
            record_name=record_name,
            record_type=record_type,
            record_ttl=record["TTL"],
            ips=values if should_update else values_original,
        )
        self.logger.debug(f"change_batch: {to_json(change_batch)}")
        # self.dns_service.change_resource_record_sets(hosted_zone_id, change_batch)
        return True

    def add_ip_to_record(
        self,
        hosted_zone_id: str,
        record_name: str,
        record_type: str,
        record_ttl: int,
        dns_mock_value: str,
        ip: str,
    ) -> bool:
        """Add an IP to a record.

        Args:
            hosted_zone_id [str]: The ID of the hosted zone that contains the resource record sets that you want to change.
            record_name [str]: The name of the resource record set that you want to change.
            record_type [str]: The DNS record type.
            record_ttl [int]: The resource record cache time to live (TTL) in seconds.
            dns_mock_value [str]: The mock value used for DNS address to be added to the record.
            ip [str]: The IP address to be added to the record.

        Returns:
            bool: True if IP is added to record, False otherwise
        """
        record_name = self._normalize_record_name(record_name, hosted_zone_id)
        record = self.dns_service.read_record(hosted_zone_id, record_name, record_type)
        if record:
            values = [value["Value"] for value in record["ResourceRecords"] if value["Value"] != dns_mock_value]
            if ip not in values:
                values.append(ip)
                change_batch = DnsChangeRequestModel(
                    action="UPSERT",
                    record_name=record_name,
                    record_type=record_type,
                    record_ttl=record_ttl,
                    ips=values,
                )
        else:
            change_batch = DnsChangeRequestModel(
                action="CREATE",
                record_name=record_name,
                record_type=record_type,
                record_ttl=record_ttl,
                ips=[ip],
            )
        self.logger.debug(f"change_batch: {to_json(change_batch)}")
        # self.dns_service.change_resource_record_sets(hosted_zone_id, change_batch)
        return True
