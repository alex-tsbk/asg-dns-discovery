from app.utils import environment
from app.utils.singleton import Singleton


class RuntimeContext(metaclass=Singleton):
    """Provides runtime context information - execution environment, cloud provider, etc."""

    @property
    def is_aws(self) -> bool:
        return environment.try_get_value("cloud_provider", "").lower() == "aws"

    @property
    def is_local_development(self) -> bool:
        """Returns True if the environment is local development, False otherwise."""
        return environment.try_get_value("SG_DNS_DISCOVERY__ENVIRONMENT", "").lower() == "local"


RUNTIME_CONTEXT = RuntimeContext()
