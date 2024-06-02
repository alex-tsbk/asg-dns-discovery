from app.components.dns.dns_management_interface import DnsManagementInterface
from app.components.dns.models.dns_change_request_model import IGNORED_DNS_CHANGE_REQUEST
from app.config.models.dns_record_config import DnsRecordProvider
from app.domain.handlers.handler_context import HandlerContext
from app.utils.di import DIContainer
from app.utils.logging import get_logger
from app.workflows.scaling_group_lifecycle.sgl_context import ScalingGroupLifecycleContext
from app.workflows.scaling_group_lifecycle.sgl_step import ScalingGroupLifecycleStep


class ScalingGroupLifecycleDnsApplyChangesStep(ScalingGroupLifecycleStep):
    """
    Step that applies DNS changes for instances in a scaling group
    """

    def __init__(
        self,
        di_container: DIContainer,
    ):
        self.logger = get_logger()
        self.di_container = di_container
        super().__init__()

    def handle(self, context: ScalingGroupLifecycleContext) -> HandlerContext:
        """Handles the scaling group lifecycle event

        Args:
            context (ScalingGroupLifecycleContext): Context in which the handler is executed
        """

        # Get DNS providers from all scaling group configurations
        dns_providers = context.instance_contexts_manager.get_dns_providers()

        # Resolve DNS provider
        dns_management_services: dict[DnsRecordProvider, DnsManagementInterface] = {
            provider: self.di_container.resolve(DnsManagementInterface, provider.value) for provider in dns_providers
        }

        # Iterate over all DNS change requests and apply them, if possible
        for dns_change in context.dns_change_requests:
            # Extract required properties
            sg_config = dns_change.instance_lifecycle_context.scaling_group_config

            # Print the DNS changes
            self.logger.info(
                f"Preparing for applying DNS changes for Scaling Group '{sg_config.scaling_group_name}'"
                + f" and instance {dns_change.instance_lifecycle_context.instance_id}"
                + f" tracking DNS configuration: {sg_config.dns_config.hash}"
            )

            # If we need to ignore the DNS change request, log and continue
            if dns_change.dns_change_request == IGNORED_DNS_CHANGE_REQUEST:
                self.logger.info("DNS Change: Ignored DNS change request as no actions are required.")
                continue

            # Build change. This will make DNS change request model immutable onwards.
            dns_change_request_model = dns_change.dns_change_request.build_change()
            self.logger.info(f"DNS Change: {dns_change_request_model.get_change()}")

            # Break if in what-if mode
            if sg_config.what_if is True:
                self.logger.info("What-If Mode: DNS changes will not be applied. Printing DNS changes only.")
                continue

            dns_provider = sg_config.dns_config.provider
            dns_management_service = dns_management_services[dns_provider]
            self.logger.info("*** Applying DNS change ***")
            # TODO: Possible optimization can be performed to batch DNS changes for the same DNS provider/Hosted Zone into single change
            result = dns_management_service.apply_change_request(dns_change.dns_change_request)
            if not result.success:
                # TODO: Record data point for failed DNS change
                self.logger.error(f"Failed to apply DNS change: {result.message}")
            self.logger.info(f"DNS change result: {result.to_dict()}")
            self.logger.info("*** DNS change applied ***")

        return super().handle(context)
