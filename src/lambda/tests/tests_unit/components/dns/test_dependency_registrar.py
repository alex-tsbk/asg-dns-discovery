from typing import Callable
from unittest.mock import MagicMock

from app.components.dns.dependency_registrar import register_services
from app.components.dns.dns_management_interface import DnsManagementInterface
from app.components.dns.internal.aws.aws_dns_management_service import AwsDnsManagementService
from app.utils.di import DILifetimeScope

# from app.components.dns.internal.cloudflare.cloudflare_dns_management_service import CloudflareDnsManagementService


# def test_register_services():
#     di_container = MagicMock()

#     register_services(di_container, MagicMock())

#     di_container.register.assert_any_call(
#         DnsManagementInterface, CloudflareDnsManagementService, name="cloudflare", lifetime="scoped"
#     )


def test_register_services_when_running_on_aws(aws_runtime):
    di_container = MagicMock()

    register_services(di_container, MagicMock())

    di_container.register.assert_any_call(
        DnsManagementInterface, AwsDnsManagementService, name="route53", lifetime=DILifetimeScope.SCOPED
    )
