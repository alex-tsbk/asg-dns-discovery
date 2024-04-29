import json
import os

import boto3
import pytest
from _pytest.fixtures import SubRequest
from app.integrations.aws import boto_factory
from boto3.resources.base import ServiceResource
from botocore.client import BaseClient
from botocore.stub import Stubber
from moto import mock_aws
from moto.server import ThreadedMotoServer


@pytest.fixture(scope="function")
def aws_cloud_provider(monkeypatch):
    monkeypatch.setenv("cloud_provider", "aws")


@pytest.fixture(scope="function")
def aws_credentials(monkeypatch):
    """Sets up environment variables required for integration tests run."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture(scope="function")
def aws(aws_cloud_provider, aws_credentials):
    with mock_aws():
        yield
