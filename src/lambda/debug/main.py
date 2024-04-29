import argparse
import sys
from typing import Any

from moto import mock_aws

from . import utils
from .seeders.dynamo_db_data_seeder import DynamoDBDataSeeder

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
        dynamodb_seeder = DynamoDBDataSeeder()
        dynamodb_seeder.patch_environment()
        dynamodb_seeder.seed_default_data()
        # Handle event
        main.event_request_handler(event, None)


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
