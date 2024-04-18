from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from typing import Any, Callable, ClassVar, Generator, NoReturn

from app.components.concurrency.task_scheduler_interface import TaskSchedulerInterface

# from app.context import RUNTIME_CONTEXT
from app.utils import environment
from app.utils.logging import get_logger

# Maximum number of concurrent threads to run in the thread pool
CONCURRENT_THREADS_HARD_LIMIT = 1000


class ConcurrentTaskScheduler(TaskSchedulerInterface):
    """Concrete implementation of TaskSchedulerInterface that schedules tasks concurrently.
    Best suitable for I/O-bound tasks. All tasks are executed in a thread pool.
    """

    # Remarks:
    #  AWS supports up to 1024 concurrent threads in a Lambda function
    #    https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html#function-configuration-deployment-and-execution
    #  Azure Functions can resolve this from PYTHON_THREADPOOL_THREAD_COUNT environment variable
    #    https://learn.microsoft.com/en-us/answers/questions/1193349/how-to-increase-parallelism-in-azure-functions-wit
    max_workers: ClassVar[int] = min(
        environment.try_get_value("PYTHON_THREADPOOL_THREAD_COUNT", CONCURRENT_THREADS_HARD_LIMIT),
        CONCURRENT_THREADS_HARD_LIMIT,
    )

    def __init__(self):
        """Initializes the task scheduler with a thread pool executor."""
        self.logger = get_logger()
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.futures: list[Future[NoReturn]] = []

    def place(self, task: Callable[..., NoReturn], *args: Any, **kwargs: Any):
        """Immediately submits an I/O-bound task for execution.

        Args:
            task (Callable): Task to execute
            *args: Task arguments
            **kwargs: Task keyword arguments
        """
        future: Future[NoReturn] = self.executor.submit(task, *args, **kwargs)
        self.futures.append(future)

    def retrieve(self) -> Generator[Future[NoReturn] | Exception, None, None]:
        """A generator that yields completed tasks as they become available.

        Yields:
            The result of each completed task. If a task raised an exception,
            the exception object is yielded for that task.
        """
        while self.futures:
            # Wait for any future to complete
            done, _ = wait(self.futures, return_when=FIRST_COMPLETED)

            for future in done:
                try:
                    yield future.result()
                except Exception as exc:
                    self.logger.error(f"Task execution failed: {exc}")
                    yield exc
                self.futures.remove(future)

    def shutdown(self, wait: bool = True):
        """Shuts down the execution, optionally waiting for tasks to complete."""
        self.executor.shutdown(wait=wait)
