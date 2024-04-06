from dataclasses import dataclass, field

from app.utils.dataclass import DataclassBase


@dataclass
class MetadataResultModel(DataclassBase):
    """Model containing instance metadata resolved values."""

    # Instance id
    instance_id: str
    # Value resolved
    value: str
    # Source of the value
    value_source: str = field(default="")
