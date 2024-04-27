from app.context import RUNTIME_CONTEXT
from app.utils.di import DIContainer

from .dns_management_interface import DnsManagementInterface


def register_services(di_container: DIContainer):
    """Registers services concrete implementations in the DI container.

    Args:
        di_container (DIContainer): DI container
    """

    if RUNTIME_CONTEXT.is_aws:
        from .internal.aws.aws_dns_management_service import AwsDnsManagementService

        di_container.register(DnsManagementInterface, AwsDnsManagementService, name="route53")
