import argparse
import sys
from datetime import UTC, datetime
from typing import Any

from debug.aws.seeders.ec2_data_seeder import Ec2DataSeeder
from debug.aws.seeders.networking_seeder import NetworkingSeeder, NetworkingSeederResponse
from debug.aws.seeders.route53_seeder import Route53Seeder
from moto import mock_aws

from . import utils
from .aws.seeders import constants
from .aws.seeders.dynamo_db_data_seeder import DynamoDBDataSeeder

# https://docs.python.org/3/library/argparse.html
parser = argparse.ArgumentParser(
    prog="Scaling Group DNS Discovery Application Debugger",
    description="Debugs the Scaling Group DNS Discovery Application",
    epilog="See the README for more information on how to use this debugger.",
)

parser.add_argument(
    "-c",
    "--cloud-provider",
    dest="cloud_provider",
    type=str,
    required=True,
    help="The cloud provider to debug the application for.",
    choices=["aws"],
)

parser.add_argument(
    "-e",
    "--event-family",
    dest="event_family",
    type=str,
    required=True,
    help="The event family to debug the application for. For example, 'asg-lifecycle'.",
    choices=[
        "asg-lifecycle",  # ASG Lifecycle
    ],
)

parser.add_argument(
    "-n",
    "--event-name",
    dest="event_name",
    type=str,
    required=True,
    help="The event name to debug the application for.",
)

parser.add_argument(
    "-w",
    "--event-wrapper-name",
    dest="wrapper_name",
    type=str,
    required=False,
    help="The wrapper to wrap event with. This makes it easy to craft events without needing to figure out full SNS message.",
)


def debug_event_request_handler(event: dict[str, Any]):
    """Debugs the event request handler.

    Args:
        event (dict[str, Any]): The event to debug the event request handler for.
            This is the event that is passed to the event request handler (SNS message in AWS).
    """
    from app import main

    with mock_aws(config={"core": {"reset_boto3_session": False}}):
        # Load seeders to set up infrastructure
        networking_seeder = NetworkingSeeder()
        networking_info: NetworkingSeederResponse = networking_seeder.setup_aws_networking()
        # Create Route53 Hosted Zone
        route53_seeder = Route53Seeder(domain_name="sgdnsdiscovery.com")
        route53_info = route53_seeder.setup_route53()
        # Seed config data
        dynamodb_seeder = DynamoDBDataSeeder()
        dynamodb_seeder.patch_environment()
        dynamodb_seeder.seed_config_data(route53_info.hosted_zone_id)
        # Provision EC2 instances
        ec2_seeder = Ec2DataSeeder()
        # Provisions 2 ASGs with 2 instances each
        asg_data = ec2_seeder.seed_data_for_sg_lch(networking_info)

        # During lifecycle events, we'll be dealing in the context of a single ASG,
        # however, there might be multiple DNS configurations for the ASG. To test things
        # reliably, we're basing scenarios on the assumption that there is already 1 Instance
        # in a give ASG, and for newly launched instances, or when terminating one, we'll be
        # using "Primary" EC2 instance from the constants.py file.
        # This is to ensure that we have a reliable instance to test the DNS configurations against.
        # This is a bit of a hack, but it's a necessary one.

        # Patch event with instance ids from data seeded, as it's impossible to predict instance ids
        event = utils.str_replace(
            event, constants.INSTANCE_ID_PRIMARY, asg_data.scaling_groups[constants.ASG_PRIMARY][0]
        )
        event = utils.str_replace(
            event, constants.INSTANCE_ID_SECONDARY, asg_data.scaling_groups[constants.ASG_PRIMARY][1]
        )

        # Patch bootstrap method to return the DI container, so we can decorate handlers with
        # with Debug-able decorators (health checks service, etc)
        utils.patch_startup()

        # Handle event and measure time taken
        time_start = datetime.now(UTC)
        main.event_request_handler(event, None)
        time_end = datetime.now(UTC)
        print(f"Execution time in seconds: {(time_end - time_start).total_seconds()}")


if __name__ == "__main__":
    # Parse arguments
    args = parser.parse_args(sys.argv[1:])  # type: ignore
    # Load event
    event = utils.load_event(
        cloud_provider=args.cloud_provider, event_family=args.event_family, event_name=args.event_name
    )
    if args.wrapper_name:
        event = utils.wrap(cloud_provider=args.cloud_provider, wrapper_name=args.wrapper_name, message=event)

    # Call the event request handler
    if args.event_family in [
        "asg-lifecycle",
    ]:
        debug_event_request_handler(event)
