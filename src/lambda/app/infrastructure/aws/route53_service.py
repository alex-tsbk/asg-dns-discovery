from __future__ import annotations

from typing import TYPE_CHECKING

import boto3
from botocore.exceptions import ClientError

if TYPE_CHECKING:
    from mypy_boto3_route53.client import Route53Client

from app.components.dns.aws.aws_dns_change_request_model import AwsDnsChangeRequestModel
from app.infrastructure.aws import boto_config
from app.utils.exceptions import CloudProviderException
from app.utils.logging import get_logger
from app.utils.serialization import to_json


class Route53Service:
    """
    Service class for managing DNS records using AWS Route53.
    """

    route53_client: Route53Client = boto3.client("route53", config=boto_config.CONFIG)
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
            self.logger.error(message)
            raise CloudProviderException(message, e)

    def read_record(self, hosted_zone_id: str, record_name: str, record_type: str) -> dict:
        """Get information about a specific record.

        For more information please visit:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/route53.html
        """
        try:
            response = self.route53_client.list_resource_record_sets(
                HostedZoneId=hosted_zone_id,
                StartRecordName=record_name,
                StartRecordType=record_type,
                MaxItems="1",
            )
            self.logger.debug(f"read_record response: {to_json(response)}")
            for record in response["ResourceRecordSets"]:
                if record["Name"] == record_name and record["Type"] == record_type:
                    return record
            return None
        except ClientError as e:
            message = f"Error reading record: {str(e)}"
            self.logger.error(message)
            raise CloudProviderException(message, e)

    def change_resource_record_sets(self, hosted_zone_id: str, change: AwsDnsChangeRequestModel) -> None:
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
            response = self.route53_client.change_resource_record_sets(
                HostedZoneId=hosted_zone_id, ChangeBatch=change.get_change()
            )
            self.logger.debug(f"change_resource_record_sets response: {to_json(response)}")
            # Wait for the change to propagate
            waiter = self.route53_client.get_waiter("resource_record_sets_changed")
            waiter.wait(Id=response["ChangeInfo"]["Id"])
            self.logger.debug(f"Resource record sets changed: {response['ChangeInfo']['Id']}")
        except ClientError as e:
            message = f"Error changing resource record sets: {str(e)}"
            self.logger.error(message)
            raise CloudProviderException(message, e)
