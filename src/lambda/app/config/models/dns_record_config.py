from dataclasses import dataclass, field
from enum import Enum
from typing import Any, override

from app.utils.dataclass import DataclassBase


class DnsRecordMappingMode(Enum):
    """Enum representing the DNS record mapping modes"""

    # MULTIVALUE: Multiple records are created for the same record name.
    #   Example: domain.com resolves to multiple IP addresses, thus having multiple A records,
    #   single A record with multiple IP addresses, etc.
    # This is the default mode.
    MULTIVALUE = "MULTIVALUE"
    # SINGLE: Single record is created for the same record name.
    # Value is resolved to the most-recent Instance in Scaling Group that matches readiness/health check.
    #   Example: domain.com resolves to a single IP address, thus having a single A record with single value.
    SINGLE = "SINGLE"

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


@dataclass
class DnsRecordConfig(DataclassBase):
    """Model representing the DNS record configuration"""

    # DNS configuration
    provider: DnsRecordProvider = field(default=DnsRecordProvider.ROUTE53)
    value_source: str = field(default="ip:private")
    # Specifies mode of how DNS records should be mapped
    mode: DnsRecordMappingMode = field(default=DnsRecordMappingMode.MULTIVALUE)
    dns_zone_id: str = field(default="")
    record_name: str = field(default="")
    record_ttl: int = field(default=60)
    record_type: str = field(default="A")
    # DNS record priority and weight for SRV records
    record_priority: int = field(default=0)
    record_weight: int = field(default=0)

    def __post_init__(self):
        """Validate the DNS record configuration"""
        self.record_type = self.record_type.upper()

        if self.record_ttl < 1 or self.record_ttl > 604800:
            raise ValueError(f"Invalid record TTL: {self.record_ttl}")

        RECORDS_SUPPORTING_MULTIVALUE = [
            "A",
            "AAAA",
            "MX",
            "TXT",
            "PTR",
            "SRV",
            "SPF",
            "NAPTR",
            "CAA",
        ]

        if self.mode == DnsRecordMappingMode.MULTIVALUE and self.record_type not in RECORDS_SUPPORTING_MULTIVALUE:
            raise ValueError(
                f"Invalid record type: {self.record_type} - for mode {self.mode.value}: only {RECORDS_SUPPORTING_MULTIVALUE} are supported"
            )

    @override
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DnsRecordConfig":
        """Create a DNS record configuration from a dictionary"""
        return DnsRecordConfig(
            provider=DnsRecordProvider(str(data.get("provider", DnsRecordProvider.ROUTE53.value)).upper()),
            value_source=str(data.get("value_source", "ip:private")).lower(),
            mode=DnsRecordMappingMode(str(data.get("mode", DnsRecordMappingMode.MULTIVALUE.value)).upper()),
            dns_zone_id=data.get("dns_zone_id", ""),
            record_name=data.get("record_name", ""),
            record_ttl=data.get("record_ttl", 60),
            record_type=data.get("record_type", "A"),
            record_priority=data.get("record_priority", 0),
            record_weight=data.get("record_weight", 0),
        )
