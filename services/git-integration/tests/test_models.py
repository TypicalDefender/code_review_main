"""
Tests for the data models.
"""

import unittest
from datetime import datetime
import os
import sys

# Add the src directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from models import User, Repository, FileChange, PullRequest, Comment, GitPlatform, PullRequestState


class TestModels(unittest.TestCase):
    """Tests for the data models."""

    def test_user_from_github(self):
        """Test creating a User from GitHub data."""
        github_data = {
            "id": 12345,
            "login": "testuser",
            "name": "Test User",
            "email": "test@example.com",
            "avatar_url": "https://example.com/avatar.png"
        }
        
        user = User.from_github(github_data)
        
        self.assertEqual(user.id, "12345")
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.name, "Test User")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.avatar_url, "https://example.com/avatar.png")
        self.assertEqual(user.platform, GitPlatform.GITHUB)

    def test_repository_from_github(self):
        """Test creating a Repository from GitHub data."""
        github_data = {
            "id": 67890,
            "name": "test-repo",
            "full_name": "testuser/test-repo",
            "owner": {
                "id": 12345,
                "login": "testuser"
            },
            "description": "A test repository",
            "private": True,
            "html_url": "https://github.com/testuser/test-repo",
            "default_branch": "main"
        }
        
        repo = Repository.from_github(github_data)
        
        self.assertEqual(repo.id, "67890")
        self.assertEqual(repo.name, "test-repo")
        self.assertEqual(repo.full_name, "testuser/test-repo")
        self.assertEqual(repo.owner.id, "12345")
        self.assertEqual(repo.owner.username, "testuser")
        self.assertEqual(repo.description, "A test repository")
        self.assertTrue(repo.private)
        self.assertEqual(repo.url, "https://github.com/testuser/test-repo")
        self.assertEqual(repo.default_branch, "main")
        self.assertEqual(repo.platform, GitPlatform.GITHUB)

    def test_file_change_from_github(self):
        """Test creating a FileChange from GitHub data."""
        github_data = {
            "filename": "test.py",
            "status": "modified",
            "additions": 10,
            "deletions": 5,
            "changes": 15,
            "patch": "@@ -1,5 +1,10 @@",
            "blob_url": "https://github.com/testuser/test-repo/blob/main/test.py"
        }
        
        file_change = FileChange.from_github(github_data)
        
        self.assertEqual(file_change.filename, "test.py")
        self.assertEqual(file_change.status, "modified")
        self.assertEqual(file_change.additions, 10)
        self.assertEqual(file_change.deletions, 5)
        self.assertEqual(file_change.changes, 15)
        self.assertEqual(file_change.patch, "@@ -1,5 +1,10 @@")
        self.assertEqual(file_change.blob_url, "https://github.com/testuser/test-repo/blob/main/test.py")

    def test_pull_request_from_github(self):
        """Test creating a PullRequest from GitHub data."""
        github_data = {
            "id": 54321,
            "number": 42,
            "title": "Test PR",
            "body": "This is a test pull request",
            "state": "open",
            "merged": False,
            "created_at": "2023-05-10T12:00:00Z",
            "updated_at": "2023-05-10T13:00:00Z",
            "user": {
                "id": 12345,
                "login": "testuser"
            },
            "base": {
                "ref": "main",
                "repo": {
                    "id": 67890,
                    "name": "test-repo",
                    "full_name": "testuser/test-repo",
                    "owner": {
                        "id": 12345,
                        "login": "testuser"
                    }
                }
            },
            "head": {
                "ref": "feature-branch",
                "sha": "abcdef123456"
            }
        }
        
        pr = PullRequest.from_github(github_data)
        
        self.assertEqual(pr.id, "54321")
        self.assertEqual(pr.number, 42)
        self.assertEqual(pr.title, "Test PR")
        self.assertEqual(pr.body, "This is a test pull request")
        self.assertEqual(pr.state, PullRequestState.OPEN)
        self.assertEqual(pr.created_at, datetime.fromisoformat("2023-05-10T12:00:00+00:00"))
        self.assertEqual(pr.updated_at, datetime.fromisoformat("2023-05-10T13:00:00+00:00"))
        self.assertEqual(pr.user.id, "12345")
        self.assertEqual(pr.user.username, "testuser")
        self.assertEqual(pr.repository.id, "67890")
        self.assertEqual(pr.repository.name, "test-repo")
        self.assertEqual(pr.base_branch, "main")
        self.assertEqual(pr.head_branch, "feature-branch")
        self.assertEqual(pr.head_sha, "abcdef123456")
        self.assertEqual(pr.platform, GitPlatform.GITHUB)

    def test_comment_from_github(self):
        """Test creating a Comment from GitHub data."""
        github_data = {
            "id": 98765,
            "body": "This is a test comment",
            "user": {
                "id": 12345,
                "login": "testuser"
            },
            "created_at": "2023-05-10T14:00:00Z",
            "updated_at": "2023-05-10T15:00:00Z",
            "path": "test.py",
            "position": 10,
            "commit_id": "abcdef123456"
        }
        
        comment = Comment.from_github(github_data)
        
        self.assertEqual(comment.id, "98765")
        self.assertEqual(comment.body, "This is a test comment")
        self.assertEqual(comment.user.id, "12345")
        self.assertEqual(comment.user.username, "testuser")
        self.assertEqual(comment.created_at, datetime.fromisoformat("2023-05-10T14:00:00+00:00"))
        self.assertEqual(comment.updated_at, datetime.fromisoformat("2023-05-10T15:00:00+00:00"))
        self.assertEqual(comment.path, "test.py")
        self.assertEqual(comment.position, 10)
        self.assertEqual(comment.commit_id, "abcdef123456")
        self.assertEqual(comment.platform, GitPlatform.GITHUB)


if __name__ == "__main__":
    unittest.main()
