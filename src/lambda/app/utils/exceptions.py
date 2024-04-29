from app.contexts.runtime_context import RUNTIME_CONTEXT
from app.utils.logging import get_logger


class BusinessException(Exception):
    """Encapsulates an exception that is a business error"""

    def __init__(self, message: str):
        super().__init__(message)
        self.logger = get_logger()
        self.message = message
        self.logger.error(f"Business exception: {message}", exc_info=True)


class CloudProviderException(Exception):
    """Encapsulates a cloud provider exception from concrete implementation of underlying cloud provider"""

    def __init__(self, underlying_exception: Exception, message: str = "Cloud provider error"):
        super().__init__(message)
        self.logger = get_logger()
        self.message = message
        self.underlying_exception = underlying_exception
        self.logger.error(f"Cloud provider error: {message} -> {underlying_exception}", exc_info=True)

    def __str__(self) -> str:
        return f"{self.message}: {self.underlying_exception}"

    def __repr__(self) -> str:
        return f"CloudProviderError({self.message}, {self.underlying_exception})"

    def extract_code(self) -> str:
        """Extracts the error code from the underlying exception"""
        if self.is_aws():
            return self.underlying_exception.response["Error"]["Code"]  # type: ignore
        return ""

    def is_aws(self) -> bool:
        """Returns True if the error is an AWS error, False otherwise"""
        if not RUNTIME_CONTEXT.is_aws:
            return False
        from botocore.exceptions import ClientError

        return isinstance(self.underlying_exception, ClientError)
