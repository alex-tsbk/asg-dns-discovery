from app.domain.handlers.handler_context import HandlerContext

from .handler_interface import HandlerInterface, T_contra


class HandlerBase(HandlerInterface[T_contra]):
    """Base class for all handlers"""

    def __init__(self):
        self._successor: HandlerInterface[T_contra] | None = None

    def chain(self, successor: HandlerInterface[T_contra]) -> HandlerInterface[T_contra]:
        """Chains the handlers into Chain of Responsibility.

        Args:
            successor (HandlerInterface[T_contra]): Next handler in the pipeline.
                Enforces to have the same context type.

        Returns:
            HandlerInterface[T_contra]: Returns the successor handler.
        """
        self._successor = successor
        return successor

    def handle(self, context: T_contra) -> HandlerContext:
        """Passes the request to the next handler in the pipeline.

        Args:
            context (T): Context in which the handler is executed
        """
        if self._successor:
            return self._successor.handle(context)
        # Return end state context
        return context
