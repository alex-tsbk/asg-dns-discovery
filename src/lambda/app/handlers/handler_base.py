from .handler_context import HandlerContext
from .handler_interface import HandlerInterface


class HandlerBase[T: HandlerContext](HandlerInterface):
    """Base class for all handlers"""

    def __init__(self):
        self._successor = None

    def chain(self, successor: HandlerInterface):
        """Method to chain the handlers together into a pipeline.

        Args:
            successor (HandlerInterface): Successor handler in the pipeline

        Returns:
            HandlerInterface: Next handler in the pipeline
        """
        self._successor = successor
        return successor

    def handle(self, context: T) -> T:
        """Passes the request to the next handler in the pipeline.

        Args:
            context (T): Context in which the handler is executed
        """
        if self._successor:
            return self._successor.handle(context)
        # Return end state context
        return context
