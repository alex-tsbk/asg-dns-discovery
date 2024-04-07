import abc
from concurrent.futures import Future
from typing import Any, Callable, NoReturn, Iterable


class TaskSchedulerInterface(metaclass=abc.ABCMeta):
    """Interface for task scheduler implementations"""

    @abc.abstractmethod
    def place(self, task: Callable[..., NoReturn], *args: Any, **kwargs: Any):
        """Places a task in the scheduler queue and schedules it for execution"""
        pass

    @abc.abstractmethod
    def retrieve(self) -> Iterable[Future[NoReturn] | Exception]:
        """Retrieves the next completed task from the scheduler queue"""
        pass

    @abc.abstractmethod
    def shutdown(self, wait: bool = True):
        """Shuts down the execution, optionally waiting for tasks to complete."""
        pass
