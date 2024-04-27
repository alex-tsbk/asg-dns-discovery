import json
from typing import Any

from app.components.lifecycle.models.lifecycle_event_model import LifecycleEventModel
from app.components.lifecycle.models.lifecycle_event_model_factory import LifecycleEventModelFactory
from app.handlers.contexts.scaling_group_lifecycle_context import ScalingGroupLifecycleContext
from app.handlers.handler_interface import HandlerInterface
from app.utils.exceptions import BusinessException
from app.utils.logging import get_logger
from app.utils.serialization import to_json


class AwsScalingGroupLifecycleEventHandler:
    """Class responsible for handling AutoScalingGroup EC2 instances lifecycle events from AWS SNS"""

    def __init__(
        self,
        lifecycle_event_model_factory: LifecycleEventModelFactory,
        scaling_group_lifecycle_handler: HandlerInterface[ScalingGroupLifecycleContext],
    ):
        self.lifecycle_event_model_factory = lifecycle_event_model_factory
        self.scaling_group_lifecycle_handler = scaling_group_lifecycle_handler

    def handle(self, event: dict[str, Any], context: Any) -> dict[str, Any]:
        """Lambda handler function to be invoked by AWS SNS

        Args:
            event [dict]: Example of event object passed to the handler when instance is terminating:
                ```json
                {
                    "Records": [
                        {
                            "EventSource": "aws:sns",
                            "EventVersion": "1.0",
                            "EventSubscriptionArn": "arn:aws:sns:us-east-1:123456789012:dev-sg-dns-discovery:f4fdba36-a856-4dde-ad38-99aa1190c534",
                            "Sns": {
                                "Type": "Notification",
                                "MessageId": "4a9f3fdc-a3e3-58db-b23b-61a4edd05553",
                                "TopicArn": "arn:aws:sns:us-east-1:123456789012:dev-sg-dns-discovery",
                                "Subject": "Auto Scaling:  Lifecycle action 'TERMINATING' for instance i-05629ab7d9287e205 in progress.",
                                "Message": "{\"Origin\":\"AutoScalingGroup\",\"LifecycleHookName\":\"dev-sg-dns-discovery-drain\",
                                    \"Destination\":\"EC2\",\"AccountId\":\"123456789012\",\"RequestId\":\"f02639a5-62b9-0772-d50e-09647ae07b49\",
                                    \"LifecycleTransition\":\"autoscaling:EC2_INSTANCE_TERMINATING\",\"AutoScalingGroupName\":\"example-asg\",
                                    \"Service\":\"AWS Auto Scaling\",\"Time\":\"2024-03-23T03:26:43.904Z\",\"EC2InstanceId\":\"i-05629ab7d9287e205\",
                                    \"LifecycleActionToken\":\"465e0162-e6af-4786-b4e8-bb544ae58790\"}",
                                "Timestamp": "2024-03-23T03:26:43.936Z",
                                "SignatureVersion": "1",
                                "Signature": "kp5cD...OtDwCg==",
                                "SigningCertUrl": "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-60eadc530605d63b8e62a523676ef735.pem",
                                "UnsubscribeUrl": "https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:123456789012:dev-sg-dns-discovery:f4fdba36-a856-4dde-ad38-99aa1190c534",
                                "MessageAttributes": {}
                            }
                        }
                    ]
                }
                ```

                with message extracted:
                ```json
                {
                    "Origin": "AutoScalingGroup",
                    "LifecycleHookName": "dev-sg-dns-discovery-drain",
                    "Destination": "EC2",
                    "AccountId": "123456789012",
                    "RequestId": "f02639a5-62b9-0772-d50e-09647ae07b49",
                    "LifecycleTransition": "autoscaling:EC2_INSTANCE_TERMINATING",
                    "AutoScalingGroupName": "example-asg",
                    "Service": "AWS Auto Scaling",
                    "Time": "2024-03-23T03:26:43.904Z",
                    "EC2InstanceId": "i-05629ab7d9287e205",
                    "LifecycleActionToken": "465e0162-e6af-4786-b4e8-bb544ae58790"
                }
                ```

                Example of event object passed to the handler when instance is launching:
                2024-03-23 04:14:47,482 - asg-service-discovery - 139826470618560 - DEBUG - Received event:
                ```json
                {
                    "Records": [
                        {
                            "EventSource": "aws:sns",
                            "EventVersion": "1.0",
                            "EventSubscriptionArn": "arn:aws:sns:us-east-1:123456789012:dev-sg-dns-discovery:f4fdba36-a856-4dde-ad38-99aa1190c534",
                            "Sns": {
                                "Type": "Notification",
                                "MessageId": "aaaa557e-eab9-5564-882a-0b06bf03034e",
                                "TopicArn": "arn:aws:sns:us-east-1:123456789012:dev-sg-dns-discovery",
                                "Subject": "Auto Scaling:  Lifecycle action 'LAUNCHING' for instance i-085e741d27b2407a8 in progress.",
                                "Message": "{
                                    \"Origin\":\"EC2\",\"LifecycleHookName\":\"dev-sg-dns-discovery-register\",
                                    \"Destination\":\"AutoScalingGroup\",\"AccountId\":\"123456789012\",
                                    \"RequestId\":\"b4b639a5-d7e1-d6a6-988d-594d59fbfc05\",
                                    \"LifecycleTransition\":\"autoscaling:EC2_INSTANCE_LAUNCHING\",
                                    \"AutoScalingGroupName\":\"example-asg\",\"Service\":\"AWS Auto Scaling\",
                                    \"Time\":\"2024-03-23T03:58:50.043Z\",\"EC2InstanceId\":\"i-085e741d27b2407a8\",
                                    \"LifecycleActionToken\":\"c9f2cd07-a390-4a22-913e-16df11021521\"}",
                                "Timestamp": "2024-03-23T03:58:50.084Z",
                                "SignatureVersion": "1",
                                "Signature": "GKV8c...Jw==",
                                "SigningCertUrl": "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-60eadc530605d63b8e62a523676ef735.pem",
                                "UnsubscribeUrl": "https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:123456789012:dev-sg-dns-discovery:f4fdba36-a856-4dde-ad38-99aa1190c534",
                                "MessageAttributes": {}
                            }
                        }
                    ]
                }
                ```

                with message extracted:
                ```json
                {
                    "Origin": "EC2",
                    "LifecycleHookName": "dev-sg-dns-discovery-register",
                    "Destination": "AutoScalingGroup",
                    "AccountId": "123456789012",
                    "RequestId": "b4b639a5-d7e1-d6a6-988d-594d59fbfc05",
                    "LifecycleTransition": "autoscaling:EC2_INSTANCE_LAUNCHING",
                    "AutoScalingGroupName": "example-asg",
                    "Service": "AWS Auto Scaling",
                    "Time": "2024-03-23T03:58:50.043Z",
                    "EC2InstanceId": "i-085e741d27b2407a8",
                    "LifecycleActionToken": "c9f2cd07-a390-4a22-913e-16df11021521"
                }
                ```

            context [Any]: Lambda context object
        """
        logger = get_logger()
        sns_message: dict[str, Any] = {}
        logger.debug(f"Received event: {to_json(event)}")
        # Extract Message from Records -> SNS
        if "Records" in event and len(event["Records"]) > 0 and "Sns" in event["Records"][0]:
            sns_message = json.loads(event["Records"][0]["Sns"]["Message"])
            logger.debug(f"Extracted ['Records'][0]['Sns']['Message']: {to_json(sns_message)}")

        # If no SNS message found, return 500
        if not sns_message:
            logger.warning("No SNS event found in the event object")
            return {"statusCode": 500, "body": "No SNS event found in the event object"}

        # If this is a test notification, return 200 OK
        if not sns_message.get("Origin", "") and not sns_message.get("Destination", ""):
            logger.info("Received notification that is not a lifecycle event. Ignoring...")
            return {
                "statusCode": 200,
                "body": "Received notification that is not a lifecycle event. 'Origin' and 'Destination' not found on the message object.",
            }

        # We received an SNS message but it's not a lifecycle event
        if not sns_message.get("LifecycleTransition", ""):
            logger.warning("No lifecycle transition found in the SNS message. Ignoring...")
            return {"statusCode": 400, "body": "No lifecycle transition found in the SNS message object. Ignoring."}

        # Build lifecycle event model
        try:
            event_model: LifecycleEventModel = self.lifecycle_event_model_factory.create(sns_message)
        except Exception as e:
            raise BusinessException(f"Error creating lifecycle event model: {str(e)}") from e

        scaling_group_lifecycle_context = ScalingGroupLifecycleContext(event=event_model)

        # Looks like we have a lifecycle event, let's handle it
        logger.debug("Initializing lifecycle service handling...")
        try:
            logger.info(
                f"Handling lifecycle event for AutoScalingGroup: {sns_message['AutoScalingGroupName']} and EC2 instance: {sns_message['EC2InstanceId']}"
            )
            result = self.scaling_group_lifecycle_handler.handle(scaling_group_lifecycle_context)
        except Exception as e:
            # TODO: Submit failure data point to CloudWatch
            logger.error(f"Error handling lifecycle event: {str(e)}")
            return {"statusCode": 500, "body": "Error handling lifecycle event"}
        else:
            if result:
                logger.info("Lifecycle event handled successfully")
            else:
                logger.warning("Lifecycle event not handled")

        return {"statusCode": 200, "handled": result, "body": "Lifecycle action completed"}
