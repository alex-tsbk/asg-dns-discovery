from .handler_context import HandlerContext
from .handler_interface import HandlerInterface
from typing import TypeVar

T = TypeVar("T", bound=HandlerContext, covariant=True)


class HandlerBase[T](HandlerInterface):
    """Base class for all handlers"""

    def __init__(self):
        self._successor = None

    def chain(self, successor: HandlerInterface) -> HandlerInterface:
        """Method to chain the handlers.

        Args:
            successor (HandlerInterface): Successor handler in the pipeline

        Returns:
            HandlerInterface: Next handler in the pipeline
        """
        self._successor = successor
        return successor

    def handle(self, context: HandlerContext) -> T:
        """Passes the request to the next handler in the pipeline.

        Args:
            context (T): Context in which the handler is executed
        """
        if self._successor:
            return self._successor.handle(context)
        # Return end state context
        return context
