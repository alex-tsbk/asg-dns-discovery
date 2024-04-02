import uuid
from dataclasses import dataclass, field

from app.utils.dataclass import DataclassBase


@dataclass
class HandlerContext(DataclassBase):
    """Base class for all handler contexts"""

    # Unique identifier for the request. Used for logging and tracking.
    request_id: str = field(init=False)

    def __post_init__(self):
        self.request_id = str(uuid.uuid4())
