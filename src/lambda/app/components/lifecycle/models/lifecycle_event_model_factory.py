from typing import Any

from app.runtime_context import RUNTIME_CONTEXT
from app.utils.singleton import Singleton

from .lifecycle_event_model import LifecycleEventModel


class LifecycleEventModelFactory(metaclass=Singleton):
    """Lifecycle event model factory. Creates lifecycle event models based on the runtime context."""

    def create(self, event: dict[str, Any]) -> LifecycleEventModel:
        """Creates a lifecycle event model based on the runtime context.

        Args:
            event (dict): Event data

        Returns:
            LifecycleEventModel: Model containing the event data
        """
        if RUNTIME_CONTEXT.is_aws:
            from .aws.aws_lifecycle_event_model import AwsLifecycleEventModel

            return AwsLifecycleEventModel.from_dict(event)

        raise NotImplementedError("Unsupported runtime context")
