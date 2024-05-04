from app.workflows.instance_lifecycle.instance_lifecycle_context import InstanceLifecycleContext
from app.workflows.workflow_step_base import StepBase


class InstanceLifecycleStep(StepBase[InstanceLifecycleContext]):
    """Base class for instance lifecycle step.
    This allows for a common interface for all instance lifecycle steps,
    while reducing writing boilerplate code when resolving and registering steps in workflows.
    """

    pass
