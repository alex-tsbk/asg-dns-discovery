from functools import cached_property

from app.utils import environment
from app.utils.singleton import Singleton


class _RuntimeContext(metaclass=Singleton):
    """Provides runtime context information - execution environment, cloud provider, etc."""

    @cached_property
    def cloud_provider(self) -> str:
        return environment.try_get_value("cloud_provider", "").lower()

    @cached_property
    def is_aws(self) -> bool:
        return self.cloud_provider == "aws"

    @cached_property
    def is_local_development(self) -> bool:
        """Returns True if the environment is local development, False otherwise."""
        return environment.try_get_value("SG_DNS_DISCOVERY__ENVIRONMENT", "").lower() == "local"


RUNTIME_CONTEXT = _RuntimeContext()
