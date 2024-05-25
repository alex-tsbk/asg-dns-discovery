from dataclasses import dataclass, field
from enum import Enum

from app.contexts.runtime_context import RUNTIME_CONTEXT


class MessageBrokerProvider(Enum):
    """DNS record provider"""

    # Instructs the application to use AWS SQS as a message broker provider.
    SQS = "SQS"
    # Instructs the application to use an internal message broker provider.
    # Used for local development and testing.
    INTERNAL = "INTERNAL"


@dataclass
class ReconciliationConfig:
    """Model representing the reconciliation configuration for the SG Service Discovery application."""

    # How many scaling groups to process at the same time
    max_concurrency: int = field(default=1)
    # Valid states for the instance in the Scaling Group to be considered for the reconciliation
    scaling_group_valid_states: list[str] = field(default_factory=list)
    # Message broker provider where to place messages for the per-scaling group reconciliation
    message_broker: MessageBrokerProvider = field(default=MessageBrokerProvider.INTERNAL)
    # Message broker endpoint
    message_broker_url: str = field(default="")

    def __post_init__(self):
        if self.message_broker != MessageBrokerProvider.INTERNAL and not self.message_broker_url:
            raise ValueError("'message_broker_url' is '': Non-internal message broker requires a url to be defined.")
        # Assign default valid states if not provided
        if not self.scaling_group_valid_states:
            # Assign well-known valid states based on the runtime context
            if RUNTIME_CONTEXT.is_aws:
                self.scaling_group_valid_states = ["InService"]
