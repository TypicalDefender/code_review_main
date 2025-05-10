"""
Data models for representing Git objects.
These models are used to standardize data across different Git platforms.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union


class GitPlatform(Enum):
    """Enum representing supported Git platforms."""
    GITHUB = "github"
    GITLAB = "gitlab"
    AZURE_DEVOPS = "azure-devops"
    BITBUCKET = "bitbucket"


class PullRequestState(Enum):
    """Enum representing pull request states."""
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


@dataclass
class User:
    """Model representing a Git user."""
    id: str
    username: str
    name: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    platform: GitPlatform = GitPlatform.GITHUB
    
    @classmethod
    def from_github(cls, data: Dict[str, Any]) -> 'User':
        """Create a User instance from GitHub API data."""
        return cls(
            id=str(data.get('id')),
            username=data.get('login'),
            name=data.get('name'),
            email=data.get('email'),
            avatar_url=data.get('avatar_url'),
            platform=GitPlatform.GITHUB
        )


@dataclass
class Repository:
    """Model representing a Git repository."""
    id: str
    name: str
    full_name: str
    owner: User
    description: Optional[str] = None
    private: bool = False
    url: Optional[str] = None
    default_branch: str = "main"
    platform: GitPlatform = GitPlatform.GITHUB
    
    @classmethod
    def from_github(cls, data: Dict[str, Any]) -> 'Repository':
        """Create a Repository instance from GitHub API data."""
        return cls(
            id=str(data.get('id')),
            name=data.get('name'),
            full_name=data.get('full_name'),
            owner=User.from_github(data.get('owner', {})),
            description=data.get('description'),
            private=data.get('private', False),
            url=data.get('html_url'),
            default_branch=data.get('default_branch', 'main'),
            platform=GitPlatform.GITHUB
        )


@dataclass
class FileChange:
    """Model representing a file change in a pull request."""
    filename: str
    status: str  # added, modified, removed
    additions: int = 0
    deletions: int = 0
    changes: int = 0
    patch: Optional[str] = None
    blob_url: Optional[str] = None
    
    @classmethod
    def from_github(cls, data: Dict[str, Any]) -> 'FileChange':
        """Create a FileChange instance from GitHub API data."""
        return cls(
            filename=data.get('filename'),
            status=data.get('status'),
            additions=data.get('additions', 0),
            deletions=data.get('deletions', 0),
            changes=data.get('changes', 0),
            patch=data.get('patch'),
            blob_url=data.get('blob_url')
        )


@dataclass
class PullRequest:
    """Model representing a pull request."""
    id: str
    number: int
    title: str
    body: Optional[str]
    state: PullRequestState
    created_at: datetime
    updated_at: datetime
    user: User
    repository: Repository
    base_branch: str
    head_branch: str
    head_sha: str
    files: List[FileChange] = field(default_factory=list)
    platform: GitPlatform = GitPlatform.GITHUB
    
    @classmethod
    def from_github(cls, data: Dict[str, Any], repository: Optional[Repository] = None) -> 'PullRequest':
        """Create a PullRequest instance from GitHub API data."""
        state = PullRequestState.MERGED if data.get('merged') else \
                PullRequestState.CLOSED if data.get('state') == 'closed' else \
                PullRequestState.OPEN
        
        return cls(
            id=str(data.get('id')),
            number=data.get('number'),
            title=data.get('title'),
            body=data.get('body'),
            state=state,
            created_at=datetime.fromisoformat(data.get('created_at').replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(data.get('updated_at').replace('Z', '+00:00')),
            user=User.from_github(data.get('user', {})),
            repository=repository or Repository.from_github(data.get('base', {}).get('repo', {})),
            base_branch=data.get('base', {}).get('ref'),
            head_branch=data.get('head', {}).get('ref'),
            head_sha=data.get('head', {}).get('sha'),
            platform=GitPlatform.GITHUB
        )


@dataclass
class Comment:
    """Model representing a comment on a pull request."""
    id: str
    body: str
    user: User
    created_at: datetime
    updated_at: Optional[datetime] = None
    path: Optional[str] = None
    position: Optional[int] = None
    commit_id: Optional[str] = None
    platform: GitPlatform = GitPlatform.GITHUB
    
    @classmethod
    def from_github(cls, data: Dict[str, Any]) -> 'Comment':
        """Create a Comment instance from GitHub API data."""
        return cls(
            id=str(data.get('id')),
            body=data.get('body'),
            user=User.from_github(data.get('user', {})),
            created_at=datetime.fromisoformat(data.get('created_at').replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(data.get('updated_at').replace('Z', '+00:00')) 
                if data.get('updated_at') else None,
            path=data.get('path'),
            position=data.get('position'),
            commit_id=data.get('commit_id'),
            platform=GitPlatform.GITHUB
        )
