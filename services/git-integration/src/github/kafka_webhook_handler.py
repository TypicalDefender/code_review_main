"""
Kafka-based GitHub webhook handler for the git-integration service.

This module processes GitHub webhook events from Kafka topics.
"""

import logging
from typing import Dict, Any, Optional

from ..common.message_queue import MessageQueue
from ..common.config import Config
from .client import GitHubClient
from .event_processor import EventProcessor

logger = logging.getLogger(__name__)

class KafkaWebhookHandler:
    """Handler for GitHub webhooks from Kafka."""

    def __init__(self, config: Config, message_queue: MessageQueue, github_client: GitHubClient):
        """Initialize the Kafka webhook handler.

        Args:
            config: The system configuration
            message_queue: The message queue for async processing
            github_client: The GitHub client for API interactions
        """
        self.config = config
        self.message_queue = message_queue
        self.github_client = github_client
        self.event_processor = EventProcessor(
            message_queue=message_queue,
            github_client=github_client,
            bot_prefix=config.get("chat.commands.prefix", "@opencr")
        )

    async def handle_webhook_event(self, message: Dict[str, Any], key: Optional[str] = None) -> None:
        """Handle a webhook event from Kafka.

        Args:
            message: The Kafka message
            key: The message key (optional)
        """
        try:
            # Extract event data
            event_type = message.get("event_type")
            if not event_type:
                logger.warning("Missing event type in message")
                return

            # Extract the raw payload
            raw_payload = message.get("raw_payload", {})
            if not raw_payload:
                logger.warning("Missing raw payload in message")
                return

            # Process the event using the event processor
            try:
                result = await self.event_processor.process_event(event_type, raw_payload)
                logger.info(f"Event processed: {result.get('message')}")
            except Exception as e:
                logger.error(f"Error processing event: {e}")
        except Exception as e:
            logger.error(f"Error handling webhook event: {e}")
