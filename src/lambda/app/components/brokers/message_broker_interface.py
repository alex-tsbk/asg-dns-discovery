from abc import ABCMeta, abstractmethod

from app.entities.envelope import Envelope


class MessageBrokerInterface(metaclass=ABCMeta):
    """Interface for message brokers."""

    @abstractmethod
    def publish(self, envelope: Envelope) -> bool:
        """Publishes a message to the message broker.

        Args:
            envelope (Envelope): The envelope of the message.

        Returns:
            bool: True if the message was published successfully, False otherwise.
        """
        pass
