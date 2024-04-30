from app.components.brokers.message_broker_interface import MessageBrokerInterface
from app.events.envelope import Envelope
from app.integrations.aws.services.sqs_service import SqsService


class AwsMessageBrokerService(MessageBrokerInterface):
    """Service for publishing messages to AWS message broker."""

    def __init__(self, aws_sqs_service: SqsService) -> None:
        self.aws_sqs_service = aws_sqs_service

    def publish(self, envelope: Envelope) -> bool:
        """Publishes a message to the AWS message broker.

        Args:
            envelope (Envelope): The envelope of the message.

        Returns:
            bool: True if the message was published successfully, False otherwise.
        """
        # Publish the message to the AWS message broker
        result = self.aws_sqs_service.enqueue(envelope)
        # Extract response metadata
        status_code = result["ResponseMetadata"]["HTTPStatusCode"]
        if status_code == 200:
            return True
        return False
