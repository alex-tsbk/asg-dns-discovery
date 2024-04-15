from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from app.config.models.dns_record_config import DnsRecordConfig


class DnsChangeCommandAction(Enum):
    """Enumeration of DNS change command actions."""

    # Signals to append values to the DNS record.
    APPEND = "APPEND"
    # Signals to remove values from the DNS record.
    REMOVE = "REMOVE"
    # Signals to replace values in the DNS record.
    REPLACE = "REPLACE"


@dataclass(frozen=True)
class DnsChangeCommandValue:
    # DNS value
    dns_value: str
    # Instance launch time
    launch_time: datetime
    # Instance identifier
    instance_id: str

    def __str__(self) -> str:
        return f"${self.__class__.__name__}: {self.dns_value} ({self.instance_id}/{self.launch_time.isoformat()})"


@dataclass(frozen=True)
class DnsChangeCommand:
    """Command to perform a DNS change request."""

    # The action to perform
    action: DnsChangeCommandAction
    # The DNS record configuration.
    dns_config: DnsRecordConfig
    # List of DNS record values to append, remove, or replace.
    values: list[DnsChangeCommandValue] = field(default_factory=list)

    def __str__(self) -> str:
        return f"${self.__class__.__name__}: {self.action} {self.dns_config.record_name} {self.dns_config.record_type} {', '.join([str(v) for v in self.values])} {self.dns_config.to_dict()} "
