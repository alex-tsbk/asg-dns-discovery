from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Self, override

if TYPE_CHECKING:
    from mypy_boto3_route53.type_defs import ChangeBatchTypeDef, ChangeTypeDef
    from mypy_boto3_route53.literals import ChangeActionType

from app.components.dns.models.dns_change_request_model import (
    DnsChangeRequestAction,
    DnsChangeRequestModel,
    DnsRecordType,
)


@dataclass(kw_only=True)
class AwsDnsChangeRequestModel(DnsChangeRequestModel):
    """Model for AWS Route53 change request."""

    # Private attributes
    _change: ChangeTypeDef = field(init=False, repr=False)

    def __post_init__(self):
        """Need to call the parent's post-init method explicitly."""
        return super().__post_init__()

    @override
    def get_change(self) -> ChangeBatchTypeDef:
        """Returns a fully-constructed change batch to update the IPs in the DNS record set for Route53.

        Args:
            hosted_zone_id [str]: The ID of the hosted zone that contains the resource record sets that you want to change.

        Returns:
            dict: The change batch to update the IPs.
                Example of A record change batch:
                {
                    'Changes': [{
                        'Action': 'UPSERT' | 'CREATE' | 'DELETE',
                        'ResourceRecordSet': {
                            'Name': record_name,
                            'Type': record_type,
                            'TTL': record_ttl,
                            'ResourceRecords': [{'Value': ip} for ip in ips]
                        }
                    }]
                }
        """
        return {"Changes": [self._change]}

    @override
    def build_change(self) -> Self:
        """Generate a change request for a record based on record type.

        Returns:
            AwsDnsChangeRequestModel: The change request.
        """
        match self.record_type:
            case DnsRecordType.A:
                self._change = self._build_A_record_change()
            case _:
                raise NotImplementedError(
                    f"No change implementation found in 'AwsDnsChangeRequestModel' for record type: {self.record_type}"
                )
        return self

    def _build_A_record_change(self) -> ChangeTypeDef:
        """Build an A record change.

        Returns:
            dict: The A record change.
        """
        return {
            "Action": self._get_route53_change_action_name(self.action),
            "ResourceRecordSet": {
                "Name": self.record_name,
                "Type": self.record_type.value,
                "TTL": self.record_ttl,
                "ResourceRecords": [{"Value": value} for value in sorted(list(set(self.record_values)))],
            },
        }

    @staticmethod
    def _get_route53_change_action_name(action: DnsChangeRequestAction) -> ChangeActionType:
        """Get Route53 change action.

        Args:
            action [DnsChangeRequestAction]: The action to perform.

        Returns:
            str: The Route53 change action.
        """
        if action in [DnsChangeRequestAction.CREATE, DnsChangeRequestAction.UPDATE]:
            return "UPSERT"
        elif action == DnsChangeRequestAction.DELETE:
            return "DELETE"

        raise ValueError(f"Unsupported action in 'AwsDnsChangeRequestModel': {action}")
