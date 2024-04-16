from app.components.lifecycle.instance_lifecycle_interface import InstanceLifecycleInterface
from app.components.lifecycle.models.lifecycle_event_model import LifecycleAction, LifecycleEventModel
from app.infrastructure.aws.services.ec2_asg_service import AwsEc2AutoScalingService
from app.utils.logging import get_logger


class AwsInstanceLifecycleService(InstanceLifecycleInterface):
    """Service for managing the lifecycle of an instance."""

    def __init__(self, autoscaling_service: AwsEc2AutoScalingService):
        self.logger = get_logger()
        self.autoscaling_service = autoscaling_service

    def complete_lifecycle_action(self, event: LifecycleEventModel, action: LifecycleAction) -> bool:
        """Completes the lifecycle action for the instance with the provided result.

        Args:
            event (AwsLifecycleEventModel): Aws event object
            action (LifecycleAction): Action to proceed with

        Returns:
            bool: True if lifecycle action was completed (acknowledged) without error, False otherwise
        """
        ec2_instance_id = event.instance_id

        self.autoscaling_service.complete_lifecycle_action(
            lifecycle_action_result=action.value,
            **event.get_lifecycle_action_args(),
        )

        self.logger.debug(
            f"Lifecycle action completed for instance: {ec2_instance_id}. Action: {action.value}, LifecycleHook: {event.lifecycle_hook_name}"
        )
        return True
