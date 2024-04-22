import pytest


def pytest_configure(config):
    """
    Allow plugins and conftest files to perform initial configuration.
    """
    __patch_boto3_client_factory()


def pytest_collection(session):
    """
    Called for performing the test collection.
    """
    __patch_boto3_client_factory()


def __patch_boto3_client_factory():
    """Patch the Boto3 client factory to prevent real AWS calls during unit tests."""
    from app.infrastructure.aws import boto_factory

    # Do not materialize boto3 clients during unit tests,
    # we'll never be running against real AWS services in these tests
    def resolve_client(client_name: str, config=None):
        return None

    print("patching resolve_client")
    boto_factory.resolve_client = resolve_client


@pytest.fixture(scope="function")
def aws_runtime(monkeypatch):
    monkeypatch.setenv("cloud_provider", "aws")


# @pytest.fixture(autouse=True, scope="function")
# def boto_factory_resolve_client(monkeypatch, request: SubRequest):
#     """Stubs functionality for sending messages during tests run.

#     Returns:`
#         list[Notification]: List containing all logged messages during unit tests session.
#     """

#     def resolve_client(client_name: str) -> BaseClient:
#         return Stubber(boto3.client(client_name, region_name="no-region"))

#     monkeypatch.setattr(
#         boto_factory,
#         boto_factory.resolve_client.__name__,
#         request.param if request and hasattr(request, "param") else resolve_client,
#     )
