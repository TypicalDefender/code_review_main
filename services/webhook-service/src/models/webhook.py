"""
Webhook models for the webhook service.

This module defines the data models for webhooks received by the service.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

class GitPlatform(str, Enum):
    """Git platforms supported by the webhook service."""
    
    GITHUB = "github"
    GITLAB = "gitlab"
    AZURE_DEVOPS = "azure_devops"
    BITBUCKET = "bitbucket"

class WebhookEventType(str, Enum):
    """Types of webhook events."""
    
    # Pull request events
    PULL_REQUEST_OPENED = "pull_request.opened"
    PULL_REQUEST_CLOSED = "pull_request.closed"
    PULL_REQUEST_REOPENED = "pull_request.reopened"
    PULL_REQUEST_EDITED = "pull_request.edited"
    PULL_REQUEST_ASSIGNED = "pull_request.assigned"
    PULL_REQUEST_UNASSIGNED = "pull_request.unassigned"
    PULL_REQUEST_REVIEW_REQUESTED = "pull_request.review_requested"
    PULL_REQUEST_REVIEW_REQUEST_REMOVED = "pull_request.review_request_removed"
    PULL_REQUEST_LABELED = "pull_request.labeled"
    PULL_REQUEST_UNLABELED = "pull_request.unlabeled"
    PULL_REQUEST_SYNCHRONIZED = "pull_request.synchronized"
    
    # Pull request review events
    PULL_REQUEST_REVIEW_SUBMITTED = "pull_request_review.submitted"
    PULL_REQUEST_REVIEW_EDITED = "pull_request_review.edited"
    PULL_REQUEST_REVIEW_DISMISSED = "pull_request_review.dismissed"
    
    # Pull request review comment events
    PULL_REQUEST_REVIEW_COMMENT_CREATED = "pull_request_review_comment.created"
    PULL_REQUEST_REVIEW_COMMENT_EDITED = "pull_request_review_comment.edited"
    PULL_REQUEST_REVIEW_COMMENT_DELETED = "pull_request_review_comment.deleted"
    
    # Issue events
    ISSUE_OPENED = "issue.opened"
    ISSUE_CLOSED = "issue.closed"
    ISSUE_REOPENED = "issue.reopened"
    ISSUE_EDITED = "issue.edited"
    ISSUE_ASSIGNED = "issue.assigned"
    ISSUE_UNASSIGNED = "issue.unassigned"
    ISSUE_LABELED = "issue.labeled"
    ISSUE_UNLABELED = "issue.unlabeled"
    
    # Issue comment events
    ISSUE_COMMENT_CREATED = "issue_comment.created"
    ISSUE_COMMENT_EDITED = "issue_comment.edited"
    ISSUE_COMMENT_DELETED = "issue_comment.deleted"
    
    # Push events
    PUSH = "push"
    
    # Repository events
    REPOSITORY_CREATED = "repository.created"
    REPOSITORY_DELETED = "repository.deleted"
    REPOSITORY_ARCHIVED = "repository.archived"
    REPOSITORY_UNARCHIVED = "repository.unarchived"
    REPOSITORY_EDITED = "repository.edited"
    REPOSITORY_RENAMED = "repository.renamed"
    REPOSITORY_TRANSFERRED = "repository.transferred"
    REPOSITORY_PUBLICIZED = "repository.publicized"
    REPOSITORY_PRIVATIZED = "repository.privatized"
    
    # Other events
    PING = "ping"
    OTHER = "other"

class WebhookPayload(BaseModel):
    """Base model for webhook payloads."""
    
    # Webhook metadata
    platform: GitPlatform = Field(..., description="Git platform that sent the webhook")
    event_type: WebhookEventType = Field(..., description="Type of webhook event")
    delivery_id: str = Field(..., description="Unique identifier for the webhook delivery")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the webhook")
    
    # App information
    app_id: str = Field(..., description="ID of the app that received the webhook")
    
    # Raw payload
    raw_payload: Dict[str, Any] = Field(..., description="Raw webhook payload")
    
    # Validated and enriched data (populated during processing)
    repository: Optional[Dict[str, Any]] = Field(None, description="Repository information")
    sender: Optional[Dict[str, Any]] = Field(None, description="Sender information")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PullRequestWebhookPayload(WebhookPayload):
    """Model for pull request webhook payloads."""
    
    # Pull request information
    pull_request: Dict[str, Any] = Field(..., description="Pull request information")
    
    # Action information
    action: str = Field(..., description="Action that triggered the webhook")

class IssueWebhookPayload(WebhookPayload):
    """Model for issue webhook payloads."""
    
    # Issue information
    issue: Dict[str, Any] = Field(..., description="Issue information")
    
    # Action information
    action: str = Field(..., description="Action that triggered the webhook")

class CommentWebhookPayload(WebhookPayload):
    """Model for comment webhook payloads."""
    
    # Comment information
    comment: Dict[str, Any] = Field(..., description="Comment information")
    
    # Parent information (issue or pull request)
    parent: Dict[str, Any] = Field(..., description="Parent information (issue or pull request)")
    
    # Action information
    action: str = Field(..., description="Action that triggered the webhook")

class PushWebhookPayload(WebhookPayload):
    """Model for push webhook payloads."""
    
    # Push information
    ref: str = Field(..., description="Git ref that was pushed")
    before: str = Field(..., description="SHA of the reference before the push")
    after: str = Field(..., description="SHA of the reference after the push")
    
    # Commits information
    commits: List[Dict[str, Any]] = Field(..., description="Commits in the push")
