"""
GitHub webhook handler for the webhook service.

This module processes webhooks from GitHub, extracting relevant information
and producing validated messages to Kafka topics.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

from fastapi import Request, HTTPException

from src.models.app import App
from src.models.webhook import (
    GitPlatform,
    WebhookEventType,
    WebhookPayload,
    PullRequestWebhookPayload,
    IssueWebhookPayload,
    CommentWebhookPayload,
    PushWebhookPayload,
)
from src.messaging.kafka_producer import KafkaProducer

logger = logging.getLogger(__name__)

class GitHubWebhookHandler:
    """Handler for GitHub webhooks."""
    
    def __init__(self, app: App, kafka_producer: KafkaProducer):
        """Initialize the GitHub webhook handler.
        
        Args:
            app: The app that received the webhook
            kafka_producer: The Kafka producer for sending messages
        """
        self.app = app
        self.kafka_producer = kafka_producer
    
    async def handle_webhook(self, request: Request) -> Dict[str, Any]:
        """Handle a GitHub webhook.
        
        Args:
            request: The incoming webhook request
            
        Returns:
            A response indicating the result of processing the webhook
            
        Raises:
            HTTPException: If the webhook is invalid or cannot be processed
        """
        # Get the event type
        event_type = request.headers.get("X-GitHub-Event")
        if not event_type:
            raise HTTPException(status_code=400, detail="Missing event type")
        
        # Get the delivery ID
        delivery_id = request.headers.get("X-GitHub-Delivery")
        if not delivery_id:
            delivery_id = str(uuid.uuid4())
        
        # Parse the webhook payload
        try:
            body = await request.body()
            payload = json.loads(body)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        # Send the raw event to Kafka
        await self.kafka_producer.send_github_raw_event(
            message={
                "platform": GitPlatform.GITHUB.value,
                "event_type": event_type,
                "delivery_id": delivery_id,
                "timestamp": datetime.utcnow().isoformat(),
                "app_id": self.app.id,
                "payload": payload,
                "headers": dict(request.headers)
            },
            key=delivery_id
        )
        
        # Process the event based on its type
        try:
            if event_type == "ping":
                return await self._handle_ping_event(payload, delivery_id)
            elif event_type == "pull_request":
                return await self._handle_pull_request_event(payload, delivery_id)
            elif event_type == "issues":
                return await self._handle_issue_event(payload, delivery_id)
            elif event_type == "issue_comment":
                return await self._handle_issue_comment_event(payload, delivery_id)
            elif event_type == "pull_request_review":
                return await self._handle_pull_request_review_event(payload, delivery_id)
            elif event_type == "pull_request_review_comment":
                return await self._handle_pull_request_review_comment_event(payload, delivery_id)
            elif event_type == "push":
                return await self._handle_push_event(payload, delivery_id)
            else:
                logger.info(f"Ignoring unsupported event type: {event_type}")
                return {"message": f"Event type {event_type} not supported"}
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")
    
    async def _handle_ping_event(self, payload: Dict[str, Any], delivery_id: str) -> Dict[str, Any]:
        """Handle a ping event.
        
        Args:
            payload: The webhook payload
            delivery_id: The delivery ID
            
        Returns:
            A response indicating the result of processing the webhook
        """
        # Create a webhook payload
        webhook_payload = WebhookPayload(
            platform=GitPlatform.GITHUB,
            event_type=WebhookEventType.PING,
            delivery_id=delivery_id,
            app_id=self.app.id,
            raw_payload=payload,
            repository=payload.get("repository"),
            sender=payload.get("sender")
        )
        
        # Send the validated event to Kafka
        await self.kafka_producer.send_github_validated_event(
            message=webhook_payload.dict(),
            key=delivery_id
        )
        
        return {"message": "Pong!"}
    
    async def _handle_pull_request_event(self, payload: Dict[str, Any], delivery_id: str) -> Dict[str, Any]:
        """Handle a pull request event.
        
        Args:
            payload: The webhook payload
            delivery_id: The delivery ID
            
        Returns:
            A response indicating the result of processing the webhook
        """
        # Map GitHub action to webhook event type
        action = payload.get("action", "")
        event_type_map = {
            "opened": WebhookEventType.PULL_REQUEST_OPENED,
            "closed": WebhookEventType.PULL_REQUEST_CLOSED,
            "reopened": WebhookEventType.PULL_REQUEST_REOPENED,
            "edited": WebhookEventType.PULL_REQUEST_EDITED,
            "assigned": WebhookEventType.PULL_REQUEST_ASSIGNED,
            "unassigned": WebhookEventType.PULL_REQUEST_UNASSIGNED,
            "review_requested": WebhookEventType.PULL_REQUEST_REVIEW_REQUESTED,
            "review_request_removed": WebhookEventType.PULL_REQUEST_REVIEW_REQUEST_REMOVED,
            "labeled": WebhookEventType.PULL_REQUEST_LABELED,
            "unlabeled": WebhookEventType.PULL_REQUEST_UNLABELED,
            "synchronize": WebhookEventType.PULL_REQUEST_SYNCHRONIZED
        }
        event_type = event_type_map.get(action, WebhookEventType.OTHER)
        
        # Create a webhook payload
        webhook_payload = PullRequestWebhookPayload(
            platform=GitPlatform.GITHUB,
            event_type=event_type,
            delivery_id=delivery_id,
            app_id=self.app.id,
            raw_payload=payload,
            repository=payload.get("repository"),
            sender=payload.get("sender"),
            pull_request=payload.get("pull_request", {}),
            action=action
        )
        
        # Send the validated event to Kafka
        await self.kafka_producer.send_github_validated_event(
            message=webhook_payload.dict(),
            key=delivery_id
        )
        
        return {
            "message": f"Pull request event processed: {action}",
            "event_type": event_type.value,
            "delivery_id": delivery_id
        }
    
    # Additional event handlers would be implemented here
    # For brevity, I'm only showing the ping and pull request handlers
    # The other handlers would follow a similar pattern
    
    async def _handle_issue_event(self, payload: Dict[str, Any], delivery_id: str) -> Dict[str, Any]:
        """Handle an issue event."""
        # Implementation would be similar to _handle_pull_request_event
        return {"message": "Issue event processed"}
    
    async def _handle_issue_comment_event(self, payload: Dict[str, Any], delivery_id: str) -> Dict[str, Any]:
        """Handle an issue comment event."""
        # Implementation would be similar to _handle_pull_request_event
        return {"message": "Issue comment event processed"}
    
    async def _handle_pull_request_review_event(self, payload: Dict[str, Any], delivery_id: str) -> Dict[str, Any]:
        """Handle a pull request review event."""
        # Implementation would be similar to _handle_pull_request_event
        return {"message": "Pull request review event processed"}
    
    async def _handle_pull_request_review_comment_event(self, payload: Dict[str, Any], delivery_id: str) -> Dict[str, Any]:
        """Handle a pull request review comment event."""
        # Implementation would be similar to _handle_pull_request_event
        return {"message": "Pull request review comment event processed"}
    
    async def _handle_push_event(self, payload: Dict[str, Any], delivery_id: str) -> Dict[str, Any]:
        """Handle a push event."""
        # Implementation would be similar to _handle_pull_request_event
        return {"message": "Push event processed"}
