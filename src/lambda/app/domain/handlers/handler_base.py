from typing import Self

from app.domain.handlers.handler_context import HandlerContext

from .handler_interface import HandlerInterface, T_contra


class HandlerBase(HandlerInterface[T_contra]):
    """Base class for all handlers"""

    def __init__(self):
        self._predecessor: Self | None = None
        self._successor: Self | None = None

    def chain(self, successor: Self) -> Self:
        """Chains the handlers into Chain of Responsibility.

        Args:
            successor (HandlerInterface[T_contra]): Next handler in the pipeline.
                Enforces to have the same context type.

        Returns:
            HandlerInterface[T_contra]: Returns the successor handler.
        """
        self._successor = successor
        successor._predecessor = self
        return successor

    def head(self) -> Self:
        """Returns the first handler in the pipeline.

        Returns:
            HandlerInterface[T_contra]: Returns the first handler in the pipeline.
        """
        return self._predecessor.head() if self._predecessor else self

    def handle(self, context: T_contra) -> HandlerContext:
        """Passes the request to the next handler in the pipeline.

        Args:
            context (T): Context in which the handler is executed
        """
        if self._successor:
            return self._successor.handle(context)
        # Return end state context
        return context

    def __rshift__(self, other: Self) -> Self:
        """Overloads the >> operator to chain the handlers.

        Args:
            other (HandlerInterface[T_contra]): Next handler in the pipeline.

        Returns:
            HandlerInterface[T_contra]: Returns the successor handler, so that the chaining can continue.
        """
        return self.chain(other)
