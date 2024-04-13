from datetime import UTC, datetime, timedelta
from functools import wraps
from typing import Any, Callable


def measure_time_taken[T](func: Callable[..., T]):
    """Wrapper function to measure the time taken by a function in milliseconds.

    Args:
        func (Callable[..., T]): Function to measure the time taken for

    Returns:
        tuple[T, float]: Tuple containing the result of the function and the time taken in milliseconds
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> tuple[T, float]:
        start_time = datetime.now(UTC)
        result = func(*args, **kwargs)
        end_time = datetime.now(UTC)
        time_delta = end_time - start_time
        milliseconds_total = time_delta / timedelta(milliseconds=1)
        return result, milliseconds_total

    return wrapper
