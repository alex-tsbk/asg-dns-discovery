from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from app.entities.envelope import Envelope
from app.infrastructure.aws.boto_factory import resolve_client
from app.utils.exceptions import CloudProviderException
from app.utils.logging import get_logger
from app.utils.serialization import to_json
from app.utils.singleton import Singleton
from botocore.exceptions import ClientError

if TYPE_CHECKING:
    from mypy_boto3_sqs.client import SQSClient
    from mypy_boto3_sqs.type_defs import SendMessageResultTypeDef


class SqsService(metaclass=Singleton):
    """
    Service class for enqueuing messages to AWS SQS.
    """

    sqs_client: ClassVar[SQSClient] = resolve_client("sqs")  # type: ignore

    def __init__(self, endpoint: str):
        self.logger = get_logger()
        self.endpoint = endpoint

    def enqueue(self, message: Envelope) -> SendMessageResultTypeDef:
        """Enqueues a message to the specified SQS queue.

        Args:
            queue_url (str): _description_
            message (Envelope): _description_
        """
        try:
            payload = message.to_dict()
            self.logger.debug(f"Message payload: {to_json(payload)}")
            response = self.sqs_client.send_message(
                QueueUrl=self.endpoint,
                MessageBody=str(payload),
            )
            self.logger.debug(f"Enqueued message to SQS ('{self.endpoint}')")
            self.logger.debug(f"SQS response: {to_json(response)}")
            return response
        except ClientError as e:
            raise CloudProviderException(e, f"Failed to enqueue message to SQS: {e}")
