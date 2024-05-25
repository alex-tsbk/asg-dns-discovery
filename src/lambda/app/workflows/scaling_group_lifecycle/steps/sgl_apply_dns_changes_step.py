from app.components.dns.dns_management_interface import DnsManagementInterface
from app.config.models.dns_record_config import DnsRecordProvider
from app.config.models.scaling_group_config import ScalingGroupProceedMode
from app.domain.handlers.handler_context import HandlerContext
from app.utils.di import DIContainer
from app.utils.logging import get_logger
from app.workflows.scaling_group_lifecycle.sgl_context import ScalingGroupLifecycleContext
from app.workflows.scaling_group_lifecycle.sgl_step import ScalingGroupLifecycleStep


class ScalingGroupLifecycleApplyDnsChangesStep(ScalingGroupLifecycleStep):
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

        # Get distinct DNS providers from all scaling group configurations
        dns_providers = {
            instance_context.scaling_group_config.dns_config.provider for instance_context in context.instances_contexts
        }

        # Resolve DNS provider
        dns_management_services: dict[DnsRecordProvider, DnsManagementInterface] = {
            provider: self.di_container.resolve(DnsManagementInterface, provider.value) for provider in dns_providers
        }

        # Compute upfront whether all instances contexts are considered operational
        operational_instances = [
            instance_context
            for instance_context in context.instances_contexts
            if instance_context.instance_model and instance_context.operational
        ]
        all_instances_operational = len(operational_instances) == len(context.instances_contexts)

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
            # Build change. This will make DNS change request model immutable onwards.
            dns_change_request_model = dns_change.dns_change_request.build_change()
            self.logger.info(f"DNS Change: {dns_change_request_model.get_change()}")

            # Break if in what-if mode
            if sg_config.what_if is True:
                self.logger.info("What-If Mode: DNS changes will not be applied. Printing DNS changes only.")
                continue

            # Assess `multiple_config_proceed_mode` configuration
            if (
                sg_config.multiple_config_proceed_mode is ScalingGroupProceedMode.ALL_OPERATIONAL
                and not all_instances_operational
            ):
                # In this case it's required that all instances are operational for all DNS changes to be applied
                self.logger.info(
                    f"Scaling Group {sg_config.scaling_group_name} has instances that are not operational."
                    + "DNS changes will not be applied for this scaling group."
                )
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
