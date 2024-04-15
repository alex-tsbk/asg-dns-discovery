from abc import abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Self

from app.config.models.dns_record_config import DnsRecordConfig
from app.utils.dataclass import DataclassBase


class DnsRecordType(Enum):
    """Enum representing the supported DNS record types"""

    # A: IPv4 address.
    A = "A"
    # AAAA: IPv6 address.
    AAAA = "AAAA"
    # CNAME: Canonical name.
    CNAME = "CNAME"
    # SRV: Service locator.
    SRV = "SRV"
    # TXT: Text.
    TXT = "TXT"


class DnsChangeRequestAction(Enum):
    """Enum representing the DNS change request actions"""

    # CREATE: Create a new record.
    CREATE = "CREATE"
    # DELETE: Delete an existing record.
    DELETE = "DELETE"
    # UPDATE: Update an existing record.
    UPDATE = "UPDATE"
    # IGNORE: Do nothing. Used for cases where no action is required (actual record state matches the desired state)
    IGNORE = "IGNORE"

    def __str__(self) -> str:
        return self.value

    @staticmethod
    def from_str(label: str) -> "DnsChangeRequestAction":
        """Returns the DNS change request action from the label"""
        label = label.upper()
        if hasattr(DnsChangeRequestAction, label):
            return DnsChangeRequestAction[label.upper()]
        raise NotImplementedError(f"Unsupported action: {label}")


@dataclass(kw_only=True)
class DnsChangeRequestModel(DataclassBase):
    """Model representing a DNS change request to reach desired DNS record state."""

    # The action to perform. Example: UPDATE, CREATE, DELETE.
    action: DnsChangeRequestAction
    # Hosted Zone Identifier. Example: Z1234567890ABCDEF.
    hosted_zone_id: str
    # Name of the record to change. Example: myapp.example.com or myapp.
    record_name: str
    # Type of the record. Example: A, CNAME, TXT, etc.
    record_type: DnsRecordType
    # Time to live for the record.
    record_ttl: int = field(default=300)
    # Weight for weighted records. Used only for records with a type of SRV.
    record_weight: int = field(default=0)
    # Priority for records. Used only for records with a type of SRV.
    record_priority: int = field(default=0)
    # Port for records. Used only for records with a type of SRV.
    record_port: int = field(default=0)
    # List of record values. Depending on the record type, it can be a list of IPs, CNAMEs, etc.
    record_values: list[str] = field(default_factory=list)
    # TODO: Implement support passing DNS-provider specific record parameters
    # List of dns-provider specific record parameters with their values.
    # Used for records that require additional data.
    # record_provider_parameters: list[Mapping[str, str]] = field(default_factory=list)

    def __post_init__(self):
        # Record TTL must be between 1 and 604800 seconds
        if self.record_ttl < 1 or self.record_ttl > 604800:
            raise ValueError(f"Invalid record TTL: {self.record_ttl}. Allowed range: 1-604800 seconds.")
        # If record type is SRV ensure priority and weight are set
        if self.record_type == DnsRecordType.SRV:
            if not self.record_priority:
                raise ValueError(f"Record priority is required for DNS record type '{self.record_type}'")
            if not self.record_weight:
                raise ValueError(f"Record weight is required for DNS record type '{self.record_type}'")
        # Ensure required fields are set for non-IGNORE actions
        if self.action != DnsChangeRequestAction.IGNORE:
            if not self.record_name:
                raise ValueError(f"Record name is required for DNS change request action '{self.action}'")
            if not self.record_type:
                raise ValueError(f"Record type is required for DNS change request action '{self.action}'")

    def __str__(self) -> str:
        return f"{self.action}/{self.hosted_zone_id}/{self.record_name}/{self.record_type.value}/{', '.join(self.record_values)}"

    def __eq__(self, value: object) -> bool:
        return str(self) == str(value)

    @abstractmethod
    def build_change(self) -> Self:
        """Builds a change for the underlying DNS provider."""
        pass

    @abstractmethod
    def get_change(self) -> Mapping[str, Any]:
        """Gets platform-specific representation of the change request."""
        pass

    @classmethod
    def from_dns_record_config(cls, dns_record_config: DnsRecordConfig) -> Self:
        """Helper method to prevent writing boilerplate code.
        Creates a DNS change request model from a DNS record configuration.
        """
        return cls(
            action=DnsChangeRequestAction.IGNORE,
            hosted_zone_id=dns_record_config.dns_zone_id,
            record_name=dns_record_config.record_name,
            record_type=DnsRecordType(dns_record_config.record_type),
            record_ttl=dns_record_config.record_ttl,
            record_weight=dns_record_config.srv_weight,
            record_priority=dns_record_config.srv_priority,
        )


IGNORED_DNS_CHANGE_REQUEST = DnsChangeRequestModel(
    action=DnsChangeRequestAction.IGNORE, hosted_zone_id="NaN", record_name="NaN", record_type=DnsRecordType.TXT
)
