from app.workflows.scaling_group_lifecycle.sgl_context import ScalingGroupLifecycleContext
from app.workflows.workflow_step_base import StepBase


class ScalingGroupLifecycleStep(StepBase[ScalingGroupLifecycleContext]):
    """Base class for scaling group lifecycle step.
    This allows for a common interface for all scaling group lifecycle steps,
    while reducing writing boilerplate code when resolving and registering steps in workflows.
    """

    pass
