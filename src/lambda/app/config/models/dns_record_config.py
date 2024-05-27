from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Self, override

from app.utils import enums
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
    # SINGLE:
    #   Single value for the DNS name.
    # Value is resolved to the most-recently-launched Instance in Scaling Group
    # that is considered 'ready' and 'healthy'. Great for blue/green deployments.
    # Example:
    #   * domain.com resolves to a single IP address, thus having a single A record with single value:
    #     ;; subdomain.example.com A 12.82.13.83
    SINGLE = "SINGLE"


class DnsRecordProvider(Enum):
    """DNS record provider"""

    ROUTE53 = "route53"
    CLOUDFLARE = "cloudflare"
    MOCK = "mock"


class DnsRecordEmptyValueMode(Enum):
    """Enum representing the DNS no value actions"""

    # KEEP: Keep the existing record if no value is available.
    KEEP = "KEEP"
    # DELETE: Delete the record if no value is available.
    DELETE = "DELETE"
    # FIXED: Use a fixed value if no value is available.
    FIXED = "FIXED"


@dataclass
class DnsRecordConfig(DataclassBase):
    """Model representing the DNS record configuration"""

    # Provider of the DNS record
    provider: DnsRecordProvider = field(default=DnsRecordProvider.ROUTE53)
    # Specifies mode of how DNS records should be mapped
    mode: DnsRecordMappingMode = field(default=DnsRecordMappingMode.MULTIVALUE)
    # Specifies action to take when no value is available to update record with
    empty_mode: DnsRecordEmptyValueMode = field(default=DnsRecordEmptyValueMode.KEEP)
    empty_mode_fixed_value: str = field(default="")
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

    @property
    def hash(self) -> str:
        """Generate a unique identifier for the DNS record configuration"""
        return f"{self.provider.value}-{self.dns_zone_id}-{self.record_name}-{self.record_type}"

    @property
    def garbage_collection_id(self) -> str:
        """Returns ID that's used for tracking values requiring garbage collection.

        Garbage collection is the process of removing leftover records from Repository (DynamoDB in AWS)
        which were used to track outdated DNS record value(s) if DNS config has `empty_mode` set to `KEEP`.

        Example:
            When SG scales to 0 instances, the DNS record keeps it's last value in place in such configuration.
            For this - entry is created in the Repository to remember to remove this value on next scale-out event.
            When SG scales out to 1+ instance(s), the DNS record is updated only with the new value(s)
            resolved from Instance(s), instead of appending to it. The record from the Repository needs to be removed.
        """
        return f"garbage_collection_{self.hash}"

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
            # Fix mode to single if record type does not support multivalue
            self.mode = DnsRecordMappingMode.SINGLE

        if self.empty_mode == DnsRecordEmptyValueMode.FIXED and not self.empty_mode_fixed_value:
            raise ValueError(
                f"Invalid empty mode value: {self.empty_mode_fixed_value} for mode {self.empty_mode.value}. Value is required."
            )

    @override
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create a DNS record configuration from a dictionary"""
        # Determine no value action
        empty_mode_raw: str = data.get("empty_mode", DnsRecordEmptyValueMode.KEEP.value)
        empty_mode_arr = empty_mode_raw.split(":", 1)
        try:
            empty_mode = enums.to_enum(empty_mode_arr[0], DnsRecordEmptyValueMode)
        except Exception as e:
            raise ValueError(f"Invalid empty mode: {empty_mode_raw}") from e

        empty_mode_fixed_value = ""
        if empty_mode == DnsRecordEmptyValueMode.FIXED:
            empty_mode_fixed_value = empty_mode_arr[1]

        return cls(
            provider=enums.to_enum(data.get("provider"), default=DnsRecordProvider.ROUTE53),
            mode=enums.to_enum(data.get("mode"), default=DnsRecordMappingMode.MULTIVALUE),
            empty_mode=empty_mode,
            empty_mode_fixed_value=empty_mode_fixed_value,
            value_source=str(data.get("value_source", "ip:private")).lower(),
            dns_zone_id=data.get("dns_zone_id", ""),
            record_name=data.get("record_name", ""),
            record_ttl=data.get("record_ttl", 60),
            record_type=data.get("record_type", "A"),
            srv_priority=data.get("record_priority", 0),
            srv_weight=data.get("record_weight", 0),
            srv_port=data.get("record_port", 0),
        )
