from dataclasses import dataclass, field
from typing import Union

from app.utils.dataclass import DataclassBase


@dataclass
class Envelope(DataclassBase):
    """Entity representing the envelope of the message."""

    # Message id
    message_id: str
    # Message type
    message_type: str
    # Message schema version
    schema_version: str = field(default="v1")
    # Message payload
    payload: dict[str, Union[str, int, bool]] = field(init=False, default_factory=dict)
