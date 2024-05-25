from dataclasses import dataclass

from app.components.dns.models.dns_change_request_model import DnsChangeRequestModel
from app.utils.dataclass import DataclassBase
from app.workflows.instance_lifecycle.instance_lifecycle_context import InstanceLifecycleContext


@dataclass(kw_only=True)
class ScalingGroupLifecycleDnsChangeModel(DataclassBase):
    """Model for DNS change request during scaling group lifecycle.
    Contains the scaling group configuration and the DNS change request model.
    """

    # Contains the instance lifecycle context, required for processing the DNS change request
    instance_lifecycle_context: InstanceLifecycleContext
    # Contains the DNS change request model itself, specific to the dns provider
    dns_change_request: DnsChangeRequestModel
