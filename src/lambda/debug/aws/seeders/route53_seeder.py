from dataclasses import dataclass

import boto3
from app.utils.logging import get_logger
from mypy_boto3_route53 import Route53Client
from mypy_boto3_route53.type_defs import CreateHostedZoneResponseTypeDef


@dataclass
class Route53SeederResponse:
    hosted_zone_id: str
    domain_name: str


class Route53Seeder:
    def __init__(self, domain_name: str = "sgdnsdiscovery.com"):
        self.logger = get_logger()
        self.route53_client: Route53Client = boto3.client("route53", region_name="us-east-1")  # type: ignore
        self.domain_name = domain_name

    def setup_route53(self) -> Route53SeederResponse:
        # Create a Hosted Zone
        response: CreateHostedZoneResponseTypeDef = self.route53_client.create_hosted_zone(
            Name=self.domain_name,
            CallerReference=str(hash(f"{self.domain_name}")),
            HostedZoneConfig={"Comment": "Hosted zone created by Route53Seeder", "PrivateZone": False},
        )
        hosted_zone_id = response["HostedZone"]["Id"]
        self.logger.debug(f"Created Hosted Zone ID: {hosted_zone_id} for domain {self.domain_name}")

        # Add basic DNS records
        # A record pointing to a dummy IP address
        self.route53_client.change_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            ChangeBatch={
                "Comment": "Initial A record",
                "Changes": [
                    {
                        "Action": "CREATE",
                        "ResourceRecordSet": {
                            "Name": self.domain_name,
                            "Type": "A",
                            "TTL": 300,
                            "ResourceRecords": [{"Value": "192.0.2.1"}],
                        },
                    }
                ],
            },
        )

        return Route53SeederResponse(hosted_zone_id=hosted_zone_id, domain_name=self.domain_name)

    def set_record(self, hosted_zone_id: str, record_name: str, record_type: str, record_values: list[str]) -> None:
        if record_type not in ["A", "CNAME"]:
            self.logger.error(f"Invalid record type: {record_type}")
            return

        self.route53_client.change_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            ChangeBatch={
                "Comment": f"Setting {record_type} record for {record_name}",
                "Changes": [
                    {
                        "Action": "CREATE",
                        "ResourceRecordSet": {
                            "Name": record_name,
                            "Type": record_type,  # type: ignore
                            "TTL": 300,
                            "ResourceRecords": [{"Value": record_value} for record_value in record_values],
                        },
                    }
                ],
            },
        )


# Usage
if __name__ == "__main__":
    seeder = Route53Seeder()
    response = seeder.setup_route53()
    print(f"Created Hosted Zone ID: {response.hosted_zone_id} for domain {response.domain_name}")
