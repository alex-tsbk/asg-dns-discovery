from dataclasses import dataclass, field


@dataclass
class ReconciliationConfig:
    """Model representing the reconciliation configuration for the ASG Service Discovery application."""

    # When set to True, the application will only log the actions it would take
    what_if: bool = field(default=False)
    # How many scaling groups to process at the same time
    max_concurrency: int = field(default=1)
    # Valid states for the instance in the Scaling Group to be considered for the reconciliation
    scaling_group_valid_states: list[str] = field(default_factory=list)
