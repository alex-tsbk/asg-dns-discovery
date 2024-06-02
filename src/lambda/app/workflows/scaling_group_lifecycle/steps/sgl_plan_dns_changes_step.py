import datetime
from typing import Optional

from app.components.dns.dns_management_interface import DnsManagementInterface
from app.components.dns.models.dns_change_command import DnsChangeCommand, DnsChangeCommandAction, DnsChangeCommandValue
from app.components.lifecycle.models.lifecycle_event_model import LifecycleTransition
from app.components.metadata.instance_metadata_interface import InstanceMetadataInterface
from app.components.metadata.models.metadata_result_model import MetadataResultModel
from app.config.models.dns_record_config import DnsRecordConfig, DnsRecordProvider
from app.domain.handlers.handler_context import HandlerContext
from app.utils.di import DIContainer
from app.utils.exceptions import BusinessException
from app.utils.logging import get_logger
from app.workflows.scaling_group_lifecycle.models.sgl_dns_change_model import ScalingGroupLifecycleDnsChangeModel
from app.workflows.scaling_group_lifecycle.sgl_context import ScalingGroupLifecycleContext
from app.workflows.scaling_group_lifecycle.sgl_step import ScalingGroupLifecycleStep


class ScalingGroupLifecyclePlanDnsChangesStep(ScalingGroupLifecycleStep):
    """
    Step that plans DNS changes for instances in a scaling group
    """

    def __init__(
        self,
        instance_metadata_service: InstanceMetadataInterface,
        di_container: DIContainer,
    ):
        self.logger = get_logger()
        self.instance_metadata_service = instance_metadata_service
        self.di_container = di_container
        super().__init__()

    def handle(self, context: ScalingGroupLifecycleContext) -> HandlerContext:
        """Handles the scaling group lifecycle event

        Args:
            context (ScalingGroupLifecycleContext): Context in which the handler is executed
        """

        event = context.event

        # Get distinct DNS providers from all scaling group configurations
        dns_providers = context.instance_contexts_manager.get_dns_providers()

        # Resolve DNS provider
        dns_management_services: dict[DnsRecordProvider, DnsManagementInterface] = {
            provider: self.di_container.resolve(DnsManagementInterface, provider.value) for provider in dns_providers
        }

        # for each scaling group configuration, resolve value from instance metadata
        for instance_context in context.instance_contexts_manager.get_operational_contexts():
            # If for any reason we were unable to resolve the instance model, raise an exception
            if not instance_context.instance_model:
                raise BusinessException(f"Instance model not found for instance: {instance_context.instance_id}")

            instance_id = instance_context.instance_id
            dns_config: DnsRecordConfig = instance_context.scaling_group_config.dns_config

            metadata_result: MetadataResultModel = self.instance_metadata_service.resolve_value(
                instance_context.instance_model,
                dns_config.value_source,
            )
            self.logger.debug(
                f"Resolved metadata for {instance_id}: {metadata_result.value} ({metadata_result.value_source})"
            )

            # Create a DNS change command based on the lifecycle event transition and the resolved metadata value
            dns_change_command_action: Optional[DnsChangeCommandAction] = None

            if event.transition == LifecycleTransition.LAUNCHING:
                dns_change_command_action = DnsChangeCommandAction.APPEND

            if event.transition == LifecycleTransition.DRAINING:
                dns_change_command_action = DnsChangeCommandAction.REMOVE

            if not dns_change_command_action:
                raise BusinessException(
                    f"Unsupported lifecycle event transition: {event.transition} for instance context {instance_context}."
                )

            dns_change_command = DnsChangeCommand(
                action=dns_change_command_action,
                dns_config=dns_config,
                values=[
                    DnsChangeCommandValue(
                        dns_value=metadata_result.value,
                        launch_time=datetime.datetime.fromtimestamp(
                            instance_context.instance_model.instance_launch_timestamp
                        ),
                        instance_id=instance_context.instance_id,
                    )
                ],
            )

            # Resolve the DNS management service for the DNS provider
            provider_dns_management_service = dns_management_services[dns_config.provider]

            # Generate a DNS change request based on the DNS change command
            dns_change_request = provider_dns_management_service.generate_change_request(dns_change_command)

            # Create a model to represent the DNS change request alongside with the scaling group configuration
            sgl_dns_change_request_model = ScalingGroupLifecycleDnsChangeModel(
                instance_lifecycle_context=instance_context,
                dns_change_request=dns_change_request,
            )

            # Append the DNS change request to the context
            context.dns_change_requests.append(sgl_dns_change_request_model)

        return super().handle(context)
