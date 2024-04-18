from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from app.infrastructure.aws.boto_factory import resolve_client
from app.utils.exceptions import CloudProviderException
from app.utils.logging import get_logger
from app.utils.serialization import to_json
from app.utils.singleton import Singleton
from botocore.exceptions import ClientError

if TYPE_CHECKING:
    from mypy_boto3_route53.client import Route53Client
    from mypy_boto3_route53.type_defs import ChangeBatchTypeDef, ResourceRecordSetTypeDef


class Route53Service(metaclass=Singleton):
    """
    Service class for managing DNS records using AWS Route53.
    """

    route53_client: ClassVar[Route53Client] = resolve_client("route53")  # type: ignore
    cached_hosted_zones: dict[str, str] = {}

    def __init__(self):
        self.logger = get_logger()

    def get_hosted_zone_name(self, hosted_zone_id: str) -> str:
        """Get hosted zone name by hosted zone ID.

        Returns the name of the hosted zone.

        For more information please visit:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/route53/client/get_hosted_zone.html
        """
        if hosted_zone_id in self.cached_hosted_zones:
            return self.cached_hosted_zones[hosted_zone_id]

        try:
            response = self.route53_client.get_hosted_zone(Id=hosted_zone_id)
            self.logger.debug(f"get_hosted_zone response: {to_json(response)}")
            hosted_zone_name = response["HostedZone"]["Name"]
            self.cached_hosted_zones[hosted_zone_id] = hosted_zone_name
            return hosted_zone_name
        except ClientError as e:
            message = f"Error getting hosted zone name: {str(e)}"
            raise CloudProviderException(e, message)

    def read_record(self, hosted_zone_id: str, record_name: str, record_type: str) -> ResourceRecordSetTypeDef | None:
        """Get information about a specific record.

        For more information please visit:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/route53.html
        """
        try:
            response = self.route53_client.list_resource_record_sets(
                HostedZoneId=hosted_zone_id,
                StartRecordName=record_name,
                StartRecordType=record_type,  # type: ignore
                MaxItems="1",
            )
            self.logger.debug(f"read_record response: {to_json(response)}")
            for record in response["ResourceRecordSets"]:
                if record["Name"] == record_name and record["Type"] == record_type:
                    return record
            return None
        except ClientError as e:
            message = f"Error reading record: {str(e)}"
            raise CloudProviderException(e, message)

    def change_resource_record_sets(self, hosted_zone_id: str, change: ChangeBatchTypeDef) -> bool:
        """Create, change, or delete a resource record set.

        For more information please visit:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/route53.html#Route53.Client.change_resource_record_sets

        Args:
            hosted_zone_id [str]: The ID of the hosted zone that contains the resource record sets that you want to change.

            change_batch [DnsChangeRequestModel]: A complex type that contains an array of change items.

            {
                'Changes': [{
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': domain_name,
                        'Type': record_type,
                        'TTL': ttl,
                        'ResourceRecords': [{'Value': value} for value in values]
                    }
                }]
            }

        Raises:
            ClientError: When call fails to underlying boto3 function
        """
        try:
            response = self.route53_client.change_resource_record_sets(HostedZoneId=hosted_zone_id, ChangeBatch=change)
            self.logger.debug(f"change_resource_record_sets response: {to_json(response)}")
            # Wait for the change to propagate
            waiter = self.route53_client.get_waiter("resource_record_sets_changed")
            waiter.wait(Id=response["ChangeInfo"]["Id"])
            self.logger.debug(f"Resource record sets changed: {response['ChangeInfo']['Id']}")
            return True
        except ClientError as e:
            message = f"Error changing resource record sets: {str(e)}"
            raise CloudProviderException(e, message)
