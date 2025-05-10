"""
App models for the webhook service.

This module defines the data models for apps that use the webhook service.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class AppPermission(str, Enum):
    """Permissions that can be granted to an app."""
    
    # Repository permissions
    READ_REPOSITORY = "read:repository"
    WRITE_REPOSITORY = "write:repository"
    
    # Pull request permissions
    READ_PULL_REQUEST = "read:pull_request"
    WRITE_PULL_REQUEST = "write:pull_request"
    
    # Issue permissions
    READ_ISSUE = "read:issue"
    WRITE_ISSUE = "write:issue"
    
    # Comment permissions
    READ_COMMENT = "read:comment"
    WRITE_COMMENT = "write:comment"
    
    # Webhook permissions
    RECEIVE_WEBHOOK = "receive:webhook"

class AppScope(BaseModel):
    """Scope of an app's access."""
    
    # The organization or user that owns the repositories
    owner: Optional[str] = None
    
    # The repositories that the app has access to (if None, all repositories)
    repositories: Optional[List[str]] = None

class App(BaseModel):
    """App that can use the webhook service."""
    
    # App identifier
    id: str = Field(..., description="Unique identifier for the app")
    
    # App name
    name: str = Field(..., description="Name of the app")
    
    # App description
    description: Optional[str] = Field(None, description="Description of the app")
    
    # App owner
    owner: str = Field(..., description="Owner of the app")
    
    # App permissions
    permissions: List[AppPermission] = Field(
        default_factory=list,
        description="Permissions granted to the app"
    )
    
    # App scopes
    scopes: List[AppScope] = Field(
        default_factory=list,
        description="Scopes of the app's access"
    )
    
    # App webhook secret
    webhook_secret: str = Field(..., description="Secret for validating webhooks")
    
    # App API key
    api_key: str = Field(..., description="API key for authenticating API requests")
    
    # Whether the app is active
    active: bool = Field(default=True, description="Whether the app is active")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "id": "my-app-1",
                "name": "My App",
                "description": "My awesome app",
                "owner": "john.doe@example.com",
                "permissions": [
                    "read:repository",
                    "read:pull_request",
                    "receive:webhook"
                ],
                "scopes": [
                    {
                        "owner": "my-org",
                        "repositories": ["repo1", "repo2"]
                    }
                ],
                "webhook_secret": "my-webhook-secret",
                "api_key": "my-api-key",
                "active": True
            }
        }
