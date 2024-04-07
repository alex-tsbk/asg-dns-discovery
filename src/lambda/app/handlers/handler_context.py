import uuid
from dataclasses import dataclass, field

from app.utils.dataclass import DataclassBase


@dataclass(kw_only=True)
class HandlerContext(DataclassBase):
    """Supertype for all handler contexts"""

    # Unique identifier for the request. Used for logging and tracking.
    context_id: str = field(default="")

    def __post_init__(self):
        if not self.context_id:
            self.context_id = str(uuid.uuid4())
