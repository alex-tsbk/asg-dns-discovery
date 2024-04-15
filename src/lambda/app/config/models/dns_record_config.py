from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Self, override

from app.utils.dataclass import DataclassBase


class DnsRecordMappingMode(Enum):
    """Enum representing the DNS record mapping modes"""

    # MULTIVALUE:
    #   Multiple records are created for the same record name.
    # Example:
    #   * domain.com resolves to multiple IP addresses, thus having multiple A records,
    #     (or single A record with multiple IP addresses):
    #     ;; subdomain.example.com A 12.82.13.83, 12.82.13.84, 12.82.14.80
    MULTIVALUE = "MULTIVALUE"
    # SINGLE_LATEST:
    #   Single value for the DNS name.
    # Value is resolved to the most-recently-launched Instance in Scaling Group
    # that is considered 'ready' and 'healthy'. Great for blue/green deployments.
    # Example:
    #   * domain.com resolves to a single IP address, thus having a single A record with single value:
    #     ;; subdomain.example.com A 12.82.13.83
    SINGLE_LATEST = "SINGLE_LATEST"

    @staticmethod
    def from_str(label: str):
        """Returns the DNS record mapping mode from the label"""
        if not hasattr(DnsRecordMappingMode, label.upper()):
            raise NotImplementedError(f"Unsupported mode: {label}")
        return DnsRecordMappingMode[label.upper()]


class DnsRecordProvider(Enum):
    """DNS record provider"""

    ROUTE53 = "route53"
    CLOUDFLARE = "cloudflare"
    MOCK = "mock"

    @staticmethod
    def from_str(label: str):
        """Returns the DNS record provider from the label"""
        if not hasattr(DnsRecordProvider, label.upper()):
            raise NotImplementedError(f"Unsupported provider: {label}")
        return DnsRecordProvider[label.upper()]


class DnsRecordEmptyValueMode(Enum):
    """Enum representing the DNS no value actions"""

    # KEEP: Keep the existing record if no value is available.
    KEEP = "KEEP"
    # DELETE: Delete the record if no value is available.
    DELETE = "DELETE"
    # FIXED: Use a fixed value if no value is available.
    FIXED = "FIXED"

    @staticmethod
    def from_str(label: str):
        """Returns the DNS no value action from the label"""
        if not hasattr(DnsRecordEmptyValueMode, label.upper()):
            raise NotImplementedError(f"Unsupported no value action: {label}")
        return DnsRecordEmptyValueMode[label.upper()]


@dataclass
class DnsRecordConfig(DataclassBase):
    """Model representing the DNS record configuration"""

    # Provider of the DNS record
    provider: DnsRecordProvider = field(default=DnsRecordProvider.ROUTE53)
    # Specifies mode of how DNS records should be mapped
    mode: DnsRecordMappingMode = field(default=DnsRecordMappingMode.MULTIVALUE)
    # Specifies action to take when no value is available to update record with
    empty_mode: DnsRecordEmptyValueMode = field(default=DnsRecordEmptyValueMode.KEEP)
    empty_mode_value: str = field(default="")
    # Specifies the source of the value to update the record with
    value_source: str = field(default="ip:private")
    # DNS zone ID (e.g. Z1234567890ABCDEF for AWS, etc.)
    dns_zone_id: str = field(default="")
    # DNS Record Parameters
    record_name: str = field(default="")
    record_ttl: int = field(default=60)
    record_type: str = field(default="A")
    # SRV Record Type specific parameters
    srv_priority: int = field(default=0)
    srv_weight: int = field(default=0)
    srv_port: int = field(default=0)

    def uid(self) -> str:
        """Generate a unique identifier for the DNS record configuration"""
        return f"{self.provider.value}-{self.dns_zone_id}-{self.record_name}-{self.record_type}"

    def __post_init__(self):
        """Validate the DNS record configuration"""
        # Ensure record type is uppercase
        self.record_type = self.record_type.upper()
        # Guard clauses against invalid values for TTL
        if self.record_ttl < 1 or self.record_ttl > 604800:
            raise ValueError(f"Invalid record TTL: {self.record_ttl}")

        RECORDS_SUPPORTING_MULTIVALUE = [
            "A",
            "AAAA",
            "TXT",
            "SRV",
        ]

        if self.mode == DnsRecordMappingMode.MULTIVALUE and self.record_type not in RECORDS_SUPPORTING_MULTIVALUE:
            raise ValueError(
                f"Invalid record type: {self.record_type} - for mode {self.mode.value}: only {RECORDS_SUPPORTING_MULTIVALUE} are supported"
            )

        if self.empty_mode == DnsRecordEmptyValueMode.FIXED and not self.empty_mode_value:
            raise ValueError(
                f"Invalid empty mode value: {self.empty_mode_value} for mode {self.empty_mode.value}. Value is required."
            )

    @override
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create a DNS record configuration from a dictionary"""
        # Determine no value action
        empty_mode_raw: str = data.get("empty_mode", DnsRecordEmptyValueMode.KEEP.value)
        empty_mode_arr = empty_mode_raw.split(":", 1)
        try:
            empty_mode = DnsRecordEmptyValueMode.from_str(empty_mode_arr[0])
        except Exception as e:
            raise ValueError(f"Invalid empty mode: {empty_mode_raw}") from e

        empty_mode_value = ""
        if empty_mode == DnsRecordEmptyValueMode.FIXED:
            empty_mode_value = empty_mode_arr[1]

        return cls(
            provider=DnsRecordProvider.from_str(data.get("provider", DnsRecordProvider.ROUTE53.value)),
            mode=DnsRecordMappingMode.from_str(data.get("mode", DnsRecordMappingMode.MULTIVALUE.value)),
            empty_mode=empty_mode,
            empty_mode_value=empty_mode_value,
            value_source=str(data.get("value_source", "ip:private")).lower(),
            dns_zone_id=data.get("dns_zone_id", ""),
            record_name=data.get("record_name", ""),
            record_ttl=data.get("record_ttl", 60),
            record_type=data.get("record_type", "A"),
            srv_priority=data.get("record_priority", 0),
            srv_weight=data.get("record_weight", 0),
            srv_port=data.get("record_port", 0),
        )
