import os

import pytest


@pytest.fixture(scope="module")
def aws_runtime():
    cur_value = os.environ.get("cloud_provider", "")
    os.environ["cloud_provider"] = "aws"
    yield
    os.environ["cloud_provider"] = cur_value if cur_value else ""
