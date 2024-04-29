from app.utils import environment
from app.utils.singleton import Singleton

# from functools import cached_property


class _RuntimeContext(metaclass=Singleton):
    """Provides runtime context information - execution environment, cloud provider, etc."""

    @property
    def cloud_provider(self) -> str:
        return environment.try_get_value("cloud_provider", "").lower()

    @property
    def is_aws(self) -> bool:
        return self.cloud_provider == "aws"

    @property
    def is_local_development(self) -> bool:
        """Returns True if the environment is local development, False otherwise."""
        return environment.try_get_value("SG_DNS_DISCOVERY__ENVIRONMENT", "").lower() == "local"

    @property
    def is_test_context(self) -> bool:
        """Returns True if the environment is test context, False otherwise."""
        return environment.try_get_value(" PYTEST_CURRENT_TEST", "").lower() != ""


RUNTIME_CONTEXT = _RuntimeContext()
