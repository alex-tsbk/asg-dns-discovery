from abc import ABCMeta, abstractmethod

from app.domain.handlers.handler_context import HandlerContext
from app.domain.handlers.handler_interface import HandlerInterface, T_contra


class WorkflowInterface(HandlerInterface[T_contra], metaclass=ABCMeta):
    """
    Interface for all workflows. This is a specialization of the HandlerInterface.
    Opposed to HandlerInterface direct descendants responsible for performing a single task,
    workflows are responsible for orchestrating multiple tasks. This is achieved by chaining
    multiple handlers into a pipeline. The pipeline is a Chain of Responsibility pattern.
    """

    @abstractmethod
    def handle(self, context: T_contra) -> HandlerContext:
        """Handles the request by invoking chained handlers in workflow pipeline.

        Args:
            context (T): Context in which the handler is executed
        """
        pass
