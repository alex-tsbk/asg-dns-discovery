from dataclasses import dataclass, field
from uuid import uuid4

from app.utils.dataclass import DataclassBase


@dataclass
class Envelope(DataclassBase):
    """Entity representing the envelope of the message."""

    # Message id
    message_id: str = field(init=False, default=uuid4().hex)
    # Message type
    message_type: str = field(init=False, default="")
    # Message schema version
    schema_version: str = field(default="v1")
