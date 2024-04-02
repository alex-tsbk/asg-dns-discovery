import abc
from concurrent.futures import Future
from typing import Callable, NoReturn, Sequence


class TaskSchedulerInterface(metaclass=abc.ABCMeta):
    """Interface for task scheduler implementations"""

    @abc.abstractmethod
    def place(self, task: Callable, *args, **kwargs) -> NoReturn:
        """Places a task in the scheduler queue and schedules it for execution"""
        pass

    @abc.abstractmethod
    def retrieve(self) -> Sequence[Future]:
        """Retrieves the next completed task from the scheduler queue"""
        pass

    @abc.abstractmethod
    def shutdown(self, wait: bool = True):
        """Shuts down the execution, optionally waiting for tasks to complete."""
        pass
