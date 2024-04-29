from typing import Optional

import boto3
from boto3.resources.base import ServiceResource
from botocore.client import BaseClient
from botocore.config import Config

from .boto_config import CONFIG


def resolve_client(client_name: str, config: Optional[Config] = None) -> BaseClient:
    """Returns a Boto3 client for the given service name.

    Args:
        client_name (str): Name of the Boto3 client to create
        config (Config, optional): Boto3 configuration. Defaults to None.

    Remarks:
        This function is used to abstract the creation of Boto3 clients,
        so that it can be stubbed in tests.

    Returns:
        Any: Boto3 client
    """
    if config is None:
        config = CONFIG

    return boto3.client(client_name, config=config)  # type: ignore


def resolve_resource(resource_name: str, config: Optional[Config] = None) -> ServiceResource:
    """Returns a Boto3 resource for the given service name.

    Args:
        resource_name (str): Name of the Boto3 resource to create
        config (Config, optional): Boto3 configuration. Defaults to None.

    Remarks:
        This function is used to abstract the creation of Boto3 resources,
        so that it can be easily mocked in unit tests.

    Returns:
        Any: Boto3 resource
    """
    if config is None:
        config = CONFIG

    return boto3.resource(resource_name, config=config)  # type: ignore
