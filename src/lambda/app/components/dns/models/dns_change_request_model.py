from abc import abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Self

from app.utils.dataclass import DataclassBase


class DnsRecordType(Enum):
    """Enum representing the DNS record types"""

    # A: IPv4 address.
    A = "A"
    # AAAA: IPv6 address.
    AAAA = "AAAA"
    # CAA: Certification Authority Authorization
    CAA = "CAA"
    # CNAME: Canonical name.
    CNAME = "CNAME"
    # DS: Delegation signer.
    DS = "DS"
    # MX: Mail exchange.
    MX = "MX"
    # NAPTR: Naming authority pointer.
    NAPTR = "NAPTR"
    # NS: Name server.
    NS = "NS"
    # PTR: Pointer.
    PTR = "PTR"
    # SOA: Start of authority.
    SOA = "SOA"
    # SPF: Sender Policy Framework.
    SPF = "SPF"
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
    # IGNORE: Do nothing.
    IGNORE = "IGNORE"

    @staticmethod
    def from_str(label: str):
        """Returns the DNS change request action from the label"""
        if not hasattr(DnsChangeRequestAction, label.upper()):
            raise NotImplementedError(f"Unsupported action: {label}")
        return DnsChangeRequestAction[label.upper()]


@dataclass(kw_only=True)
class DnsChangeRequestModel(DataclassBase):
    """Model representing a DNS change request to reach desired DNS record state."""

    # The action to perform. Example: UPDATE, CREATE, DELETE.
    action: DnsChangeRequestAction
    # Name of the record to change. Example: myapp.example.com or myapp.
    record_name: str
    # Type of the record. Example: A, CNAME, TXT, etc.
    record_type: DnsRecordType
    # Time to live for the record.
    record_ttl: int = field(default=300)
    # Weight for weighted records. Used only for records with a type of SRV or TXT.
    record_weight: int = field(default=0)
    # Priority for records. Used only for records with a type of SRV or MX.
    record_priority: int = field(default=0)
    # List of record values. Depending on the record type, it can be a list of IPs, CNAMEs, etc.
    record_values: list[str] = field(default_factory=list)

    def __post_init__(self):
        # Ensure required fields are set for non-IGNORE actions
        if self.action != DnsChangeRequestAction.IGNORE:
            if not self.record_name:
                raise ValueError(f"Record name is required for DNS change request action '{self.action.value}'")
            if not self.record_type:
                raise ValueError(f"Record type is required for DNS change request action '{self.action.value}'")

    def __str__(self) -> str:
        return f"{self.record_name}/{self.record_type}/{self.action}/{', '.join(self.record_values)}"

    @abstractmethod
    def build_change(self) -> Self:
        """Builds a change for the underlying DNS provider."""
        pass

    @abstractmethod
    def get_change(self) -> Mapping[str, Any]:
        """Gets platform-specific representation of the change request."""
        pass


IGNORED_DNS_CHANGE_REQUEST = DnsChangeRequestModel(
    action=DnsChangeRequestAction.IGNORE, record_name="", record_type=DnsRecordType.A
)
