from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from app.config.models.dns_record_config import DnsRecordConfig


class DnsChangeCommandAction(Enum):
    """Enumeration of DNS change command actions."""

    # Instructs to append values to the DNS record.
    APPEND = "APPEND"
    # Instructs to remove values from the DNS record.
    REMOVE = "REMOVE"
    # Instructs to replace values in the DNS record.
    REPLACE = "REPLACE"


@dataclass(frozen=True)
class DnsChangeCommandValue:
    # DNS value
    dns_value: str
    # Instance launch time
    launch_time: datetime
    # Instance identifier
    instance_id: str


@dataclass(frozen=True)
class DnsChangeCommand:
    """Command to perform a DNS change request."""

    # The action to perform
    action: DnsChangeCommandAction
    # The DNS record configuration.
    dns_config: DnsRecordConfig
    # List of DNS record values to append, remove, or replace.
    values: list[DnsChangeCommandValue] = field(default_factory=list)
