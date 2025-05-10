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

import aiohttp
from fastapi import Request, HTTPException, Depends
from pydantic import BaseModel

from .client import GitHubClient
from ..common.message_queue import MessageQueue
from ..common.config import Config

logger = logging.getLogger(__name__)

class PullRequestEvent(BaseModel):
    """Model for pull request events."""
    action: str
    pull_request: Dict[str, Any]
    repository: Dict[str, Any]
    sender: Dict[str, Any]

class IssueCommentEvent(BaseModel):
    """Model for issue comment events."""
    action: str
    issue: Dict[str, Any]
    comment: Dict[str, Any]
    repository: Dict[str, Any]
    sender: Dict[str, Any]

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

        # Process the event based on its type
        if event_type == "ping":
            return {"message": "Pong!"}
        elif event_type == "pull_request":
            return await self._handle_pull_request_event(payload)
        elif event_type == "issue_comment":
            return await self._handle_issue_comment_event(payload)
        else:
            logger.info(f"Ignoring unsupported event type: {event_type}")
            return {"message": f"Event type {event_type} not supported"}

    async def _handle_pull_request_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a pull request event.

        Args:
            payload: The webhook payload

        Returns:
            A response indicating the result of processing the event
        """
        try:
            event = PullRequestEvent(**payload)
        except Exception as e:
            logger.error(f"Error parsing pull request event: {e}")
            raise HTTPException(status_code=400, detail="Invalid pull request event payload")

        # Only process opened or synchronized pull requests
        if event.action not in ["opened", "synchronize", "reopened"]:
            return {"message": f"Ignoring pull request action: {event.action}"}

        # Extract relevant information
        repo_owner = event.repository["owner"]["login"]
        repo_name = event.repository["name"]
        pr_number = event.pull_request["number"]
        head_sha = event.pull_request["head"]["sha"]
        base_sha = event.pull_request["base"]["sha"]

        # Queue the pull request for review
        await self.message_queue.publish(
            "pull_request.review",
            {
                "platform": "github",
                "repo_owner": repo_owner,
                "repo_name": repo_name,
                "pr_number": pr_number,
                "head_sha": head_sha,
                "base_sha": base_sha,
                "title": event.pull_request["title"],
                "description": event.pull_request["body"],
                "user": event.sender["login"],
                "created_at": event.pull_request["created_at"],
                "updated_at": event.pull_request["updated_at"],
            }
        )

        return {
            "message": "Pull request queued for review",
            "repo": f"{repo_owner}/{repo_name}",
            "pr_number": pr_number,
        }

    async def _handle_issue_comment_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an issue comment event.

        Args:
            payload: The webhook payload

        Returns:
            A response indicating the result of processing the event
        """
        try:
            event = IssueCommentEvent(**payload)
        except Exception as e:
            logger.error(f"Error parsing issue comment event: {e}")
            raise HTTPException(status_code=400, detail="Invalid issue comment event payload")

        # Only process created comments on pull requests
        if event.action != "created" or "pull_request" not in event.issue:
            return {"message": "Ignoring comment: not a new comment on a pull request"}

        # Extract relevant information
        repo_owner = event.repository["owner"]["login"]
        repo_name = event.repository["name"]
        pr_number = event.issue["number"]
        comment_id = event.comment["id"]
        comment_body = event.comment["body"]
        user = event.sender["login"]

        # Check if the comment is addressed to the bot
        bot_name = self.config.get("chat.commands.prefix", "@opencr")
        if not comment_body.startswith(bot_name):
            return {"message": "Ignoring comment: not addressed to the bot"}

        # Queue the comment for processing
        await self.message_queue.publish(
            "comment.process",
            {
                "platform": "github",
                "repo_owner": repo_owner,
                "repo_name": repo_name,
                "pr_number": pr_number,
                "comment_id": comment_id,
                "comment_body": comment_body,
                "user": user,
                "created_at": event.comment["created_at"],
            }
        )

        return {
            "message": "Comment queued for processing",
            "repo": f"{repo_owner}/{repo_name}",
            "pr_number": pr_number,
            "comment_id": comment_id,
        }
