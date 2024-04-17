import pytest


@pytest.fixture(scope="function")
def aws_runtime(monkeypatch):
    monkeypatch.setenv("cloud_provider", "aws")
