import pytest


def pytest_configure(config):
    """
    Allow plugins and conftest files to perform initial configuration.
    """


def pytest_collection(session):
    """
    Called when performing tests collection.
    """


@pytest.fixture(scope="function")
def aws_runtime(monkeypatch):
    monkeypatch.setenv("cloud_provider", "aws")
