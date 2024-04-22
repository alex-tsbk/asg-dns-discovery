from dataclasses import dataclass, field

from app.entities.envelope import Envelope


@dataclass
class ScalingGroupReconciliationRequestEvent(Envelope):
    """Event for reconciling the scaling group."""

    scaling_group_name: str = field(default="")

    def __post_init__(self):
        self.message_type = self.__class__.__name__
