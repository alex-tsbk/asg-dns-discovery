from abc import ABCMeta, abstractmethod
from typing import Generic, TypeVar

from app.domain.handlers.handler_context import HandlerContext

T_contra = TypeVar("T_contra", contravariant=True, bound=HandlerContext)


class HandlerInterface(Generic[T_contra], metaclass=ABCMeta):
    """Interface for all handlers"""

    @abstractmethod
    def handle(self, context: T_contra) -> HandlerContext:
        """Method to handle the request

        Args:
            context (T): Context in which the handler is executed. Contravariant type.
        """
        pass
