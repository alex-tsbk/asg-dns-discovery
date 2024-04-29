from typing import Any, Protocol


class HandlerProtocol(Protocol):
    """Handler protocol that all handlers handling external events should comply to."""

    def handle(self, event: dict[str, Any], context: Any) -> dict[str, Any]:
        """Handles inbound events.

        Args:
            event (dict[str, Any]): Event data
            context (Any): Context data

        Returns:
            dict[str, Any]: Response data
        """
        return {}
