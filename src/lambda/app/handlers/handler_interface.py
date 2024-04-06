from __future__ import annotations

from abc import ABCMeta, abstractmethod

from .handler_context import HandlerContext


class HandlerInterface(metaclass=ABCMeta):
    """Interface for all handlers"""

    @abstractmethod
    def handle(self, context: HandlerContext) -> HandlerContext:
        """Method to handle the request

        Args:
            context (HandlerContext): Context in which the handler is executed
        """
        pass
