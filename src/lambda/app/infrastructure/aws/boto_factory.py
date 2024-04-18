from typing import Any, Optional

import boto3
from app.utils import environment
from botocore.config import Config
from botocore.stub import Stubber

from .boto_config import CONFIG


def resolve_client(client_name: str, config: Optional[Config] = None) -> Any:
    """Returns a Boto3 client for the given service name.

    Args:
        client_name (str): Name of the Boto3 client to create
        config (Config, optional): Boto3 configuration. Defaults to None.

    Remarks:
        This function is used to abstract the creation of Boto3 clients,
        so that it can be easily mocked in unit tests.

    Returns:
        Any: Boto3 client
    """
    if config is None:
        config = CONFIG

    # If running in test environment, return a stub.
    if (
        environment.try_get_value("PYTEST_CURRENT_TEST", "") != ""
        or environment.try_get_value("PYTEST_COLLECTION", False) is True
    ):
        return Stubber(boto3.client(client_name, region_name="no-region"))  # type: ignore

    return boto3.client(client_name, config=config)  # type: ignore
