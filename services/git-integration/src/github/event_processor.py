"""
GitHub event processor for the git-integration service.

This module processes GitHub events, extracting relevant information
and triggering the appropriate actions based on the event type.
"""

import logging
from typing import Dict, Any, Optional, Tuple

from pydantic import BaseModel, ValidationError

from ..common.message_queue import MessageQueue
from .client import GitHubClient

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

class EventProcessor:
    """Processor for GitHub events."""

    def __init__(self, message_queue: MessageQueue, github_client: GitHubClient, bot_prefix: str = "@opencr"):
        """Initialize the event processor.

        Args:
            message_queue: The message queue for async processing
            github_client: The GitHub client for API interactions
            bot_prefix: The prefix used to identify commands addressed to the bot
        """
        self.message_queue = message_queue
        self.github_client = github_client
        self.bot_prefix = bot_prefix

    async def process_pull_request_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process a pull request event.

        Args:
            payload: The event payload

        Returns:
            A response indicating the result of processing the event

        Raises:
            ValidationError: If the payload is invalid
        """
        # Parse and validate the event
        event = PullRequestEvent(**payload)

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

    async def process_issue_comment_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process an issue comment event.

        Args:
            payload: The event payload

        Returns:
            A response indicating the result of processing the event

        Raises:
            ValidationError: If the payload is invalid
        """
        # Parse and validate the event
        event = IssueCommentEvent(**payload)

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
        if not comment_body.startswith(self.bot_prefix):
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

    async def process_event(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process a GitHub event.

        Args:
            event_type: The type of event (e.g., "pull_request", "issue_comment")
            payload: The event payload

        Returns:
            A response indicating the result of processing the event
        """
        try:
            if event_type == "ping":
                return {"message": "Pong!"}
            elif event_type == "pull_request":
                return await self.process_pull_request_event(payload)
            elif event_type == "issue_comment":
                return await self.process_issue_comment_event(payload)
            else:
                logger.info(f"Ignoring unsupported event type: {event_type}")
                return {"message": f"Event type {event_type} not supported"}
        except ValidationError as e:
            logger.error(f"Error validating {event_type} event: {e}")
            raise
        except Exception as e:
            logger.error(f"Error processing {event_type} event: {e}")
            raise
