import os
import uuid

import pytest
from app.utils.environment import get


@pytest.fixture
def random_env_key():
    # We don't want to mess up with the existing environment variables
    key = uuid.uuid4().hex
    yield key
    os.environ.pop(key, None)


def test_get_should_return_value(random_env_key):
    # Test when environment variable is set
    os.environ[random_env_key] = "value"
    assert get(random_env_key) == "value"


def test_get_should_return_default_value(random_env_key):
    # Test when environment variable is not set
    assert get(random_env_key, "default") == "default"


def test_get_should_convert_type(random_env_key):
    # Test when environment variable is set and should be converted to int
    os.environ[random_env_key] = "1"
    result = get(random_env_key, 0)
    assert result == 1
    assert type(result) is int
