from __future__ import annotations

import functools
from collections.abc import Callable, Mapping
from typing import Any, Iterable, Optional

# Specifies maximum numbers of retries for boto3 functions
BOTO3_FUNCTION_MAX_RETRY = 3

# Specifies number of retries when automation hits throttling exception
BOTO3_THROTTLING_RETRY_LIMIT = 20

def paginated_call[T: Mapping[str, Any], K: Any](
    resource_selector: Callable[[T], Iterable[K]],
    paginator_name_request: str = "NextToken",
    paginator_name_response: str = "NextToken",
    on_success: Optional[Callable[[Iterable[K]], None]] = None,
) -> Callable[[Callable[..., T]], Callable[..., Iterable[K]]]:  # fmt: skip ; Black issue with Python 3.12 syntax
    """Executes a paginated boto3 call and returns aggregated results

    Args:
        resource_selector (Callable[[T], Iterable[K]]): Function to extract resources from response object
        paginator_name_request (str): Property name used to supply pagination token to the subsequent request
        paginator_name_response (str): Property name on the response object containing pagination token (if any)
        on_success (Optional[Callable[[Iterable[T]], None]], optional): Callback function to execute on each successful response. Defaults to None.

    Usage example:
        ```python
        instances: list[InstanceTypeDef] = []
        kwargs: dict[str, Any] = {"InstanceIds": instance_ids}

        def selector(response: DescribeInstancesResultTypeDef) -> Iterable[ReservationTypeDef]:
            return response["Reservations"]

        @paginated_call(selector, "NextToken", "NextToken")
        def describe_instances(**invoke_kwargs: Any) -> DescribeInstancesResultTypeDef:
            return self.ec2_client.describe_instances(**invoke_kwargs)

        resources = describe_instances(**kwargs)
        instances.extend(*[resource["Instances"] for resource in resources])
        ```
    """

    def decorator(func: Callable[..., T]) -> Callable[[Any, dict[str, Any]], Iterable[K]]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Iterable[K]:
            """Returns aggregated result for boto3 function where request/response supports pagination"""
            resolved_resources: list[K] = []
            nextMarker: str = ""
            while True:
                if nextMarker:
                    kwargs[paginator_name_request] = nextMarker
                response: T = func(*args, **kwargs)
                result: Iterable[K] = resource_selector(response)
                resolved_resources.extend(result)
                if on_success:
                    on_success(result)
                nextMarker: str = response.get(paginator_name_response, "")
                if not nextMarker:
                    break
            return resolved_resources

        return wrapper

    return decorator
