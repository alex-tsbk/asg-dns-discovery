import threading
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from time import sleep
from typing import Any, Callable, ClassVar, Generator

from app.components.concurrency.task_scheduler_interface import TaskSchedulerInterface

# from app.context import RUNTIME_CONTEXT
from app.utils import environment
from app.utils.exceptions import BusinessException
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

    # Tracks workers in use at class level to prevent abuse of the thread pool
    # across all concurrent task scheduler instances
    workers_in_use: int = 0
    workers_in_use_lock = threading.Lock()

    def __init__(self):
        """Initializes the task scheduler with a thread pool executor."""
        self.logger = get_logger()
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.futures: list[Future[Any]] = []

    def place(self, task: Callable[..., Any], *args: Any, **kwargs: Any):
        """Immediately submits an I/O-bound task for execution.

        Args:
            task (Callable): Task to execute
            *args: Task arguments
            **kwargs: Task keyword arguments
        """
        while True:
            # Double-check locking to ensure the worker limit is not exceeded
            if self.workers_in_use < self.max_workers:
                with self.workers_in_use_lock:
                    if self.workers_in_use < self.max_workers:
                        self.workers_in_use += 1
                        break
            # Block main thread until a worker is available,
            # then submit the task for execution
            self.logger.warning(
                f"Thread pool is full: {self.workers_in_use}/{self.max_workers} in use, waiting for a worker to become available.."
            )
            sleep(0.01)  # 10 ms

        try:
            future: Future[Any] = self.executor.submit(task, *args, **kwargs)
            self.futures.append(future)
        except Exception as exc:
            self.workers_in_use -= 1
            raise BusinessException(f"Task submission failed: {exc}")

    def retrieve(self) -> Generator[Future[Any] | Exception, None, None]:
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
                finally:
                    # Remove the completed future and decrement the workers in use
                    self.workers_in_use -= 1
                self.futures.remove(future)

    def shutdown(self, wait: bool = True):
        """Shuts down the execution, optionally waiting for tasks to complete."""
        self.executor.shutdown(wait=wait)
