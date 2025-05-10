"""
GitHub webhook handler for OpenCodeReview.

This module processes webhooks from GitHub, extracting relevant information
and triggering the appropriate actions based on the event type.
"""

import hmac
import hashlib
import json
import logging
from typing import Dict, Any, Optional, Tuple

from fastapi import Request, HTTPException, Depends
from pydantic import ValidationError

from .client import GitHubClient
from .event_processor import EventProcessor
from ..common.message_queue import MessageQueue
from ..common.config import Config

logger = logging.getLogger(__name__)

class WebhookHandler:
    """Handler for GitHub webhooks."""

    def __init__(self, config: Config, message_queue: MessageQueue, github_client: GitHubClient):
        """Initialize the webhook handler.

        Args:
            config: The system configuration
            message_queue: The message queue for async processing
            github_client: The GitHub client for API interactions
        """
        self.config = config
        self.message_queue = message_queue
        self.github_client = github_client
        self.webhook_secret = config.get("git.github.webhook_secret")
        self.event_processor = EventProcessor(
            message_queue=message_queue,
            github_client=github_client,
            bot_prefix=config.get("chat.commands.prefix", "@opencr")
        )

    async def verify_signature(self, request: Request) -> bool:
        """Verify the webhook signature.

        Args:
            request: The incoming request

        Returns:
            True if the signature is valid, False otherwise
        """
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured, skipping signature verification")
            return True

        signature_header = request.headers.get("X-Hub-Signature-256")
        if not signature_header:
            logger.warning("No signature header in request")
            return False

        try:
            body = await request.body()
            signature = hmac.new(
                self.webhook_secret.encode(),
                msg=body,
                digestmod=hashlib.sha256
            ).hexdigest()
            expected_signature = f"sha256={signature}"

            return hmac.compare_digest(expected_signature, signature_header)
        except Exception as e:
            logger.error(f"Error verifying signature: {e}")
            return False

    async def handle_webhook(self, request: Request) -> Dict[str, Any]:
        """Handle a GitHub webhook.

        Args:
            request: The incoming webhook request

        Returns:
            A response indicating the result of processing the webhook

        Raises:
            HTTPException: If the webhook is invalid or cannot be processed
        """
        # Verify the webhook signature
        if not await self.verify_signature(request):
            raise HTTPException(status_code=401, detail="Invalid signature")

        # Get the event type
        event_type = request.headers.get("X-GitHub-Event")
        if not event_type:
            raise HTTPException(status_code=400, detail="Missing event type")

        # Parse the webhook payload
        try:
            body = await request.body()
            payload = json.loads(body)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")

        # Process the event using the event processor
        try:
            return await self.event_processor.process_event(event_type, payload)
        except ValidationError as e:
            logger.error(f"Error validating {event_type} event: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid {event_type} event payload")
        except Exception as e:
            logger.error(f"Error processing {event_type} event: {e}")
            raise HTTPException(status_code=500, detail=f"Error processing {event_type} event")


