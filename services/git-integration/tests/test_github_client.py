"""
Tests for the GitHub client.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys
import requests

# Add the src directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from src.github.client import GitHubClient


class TestGitHubClient(unittest.TestCase):
    """Tests for the GitHub client."""

    def setUp(self):
        """Set up the test environment."""
        # Create a patched version of the client to avoid real API calls
        with patch('src.github.client.requests.Session'):
            self.client = GitHubClient(token="test_token")
            # Replace the _request method with a mock to avoid real API calls
            self.client._request = MagicMock()

    @patch("src.github.client.requests.Session")
    def test_init(self, mock_session):
        """Test initialization of the client."""
        # Test with token provided
        client = GitHubClient(token="test_token")
        self.assertEqual(client.token, "test_token")
        mock_session.return_value.headers.update.assert_any_call({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "OpenSourceCodeReview-GitIntegration"
        })
        mock_session.return_value.headers.update.assert_any_call({
            "Authorization": "token test_token"
        })

        # Test with token from environment
        with patch.dict(os.environ, {"GITHUB_TOKEN": "env_token"}):
            client = GitHubClient()
            self.assertEqual(client.token, "env_token")

    @patch("src.github.client.requests.Session")
    def test_request(self, mock_session):
        """Test the _request method."""
        # Create a fresh client for this test
        with patch('src.github.client.requests.Session') as session_mock:
            client = GitHubClient(token="test_token")

            # Create a mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"key": "value"}

            # Set up the mock session to return our mock response
            session_mock.return_value.request.return_value = mock_response

            # Test successful request
            result = client._request("GET", "/test")
            self.assertEqual(result, {"key": "value"})
            session_mock.return_value.request.assert_called_with(
                "GET", "https://api.github.com/test",
            )

            # Test no content response
            mock_response.status_code = 204
            result = client._request("GET", "/test")
            self.assertEqual(result, {})

    def test_get_repository(self):
        """Test the get_repository method."""
        self.client._request.return_value = {"name": "test-repo"}
        result = self.client.get_repository("owner", "repo")
        self.assertEqual(result, {"name": "test-repo"})
        self.client._request.assert_called_with("GET", "/repos/owner/repo")

    def test_get_pull_requests(self):
        """Test the get_pull_requests method."""
        self.client._request.return_value = [{"number": 1}]
        result = self.client.get_pull_requests("owner", "repo")
        self.assertEqual(result, [{"number": 1}])
        self.client._request.assert_called_with("GET", "/repos/owner/repo/pulls", params={"state": "open"})

    def test_get_pull_request(self):
        """Test the get_pull_request method."""
        self.client._request.return_value = {"number": 1}
        result = self.client.get_pull_request("owner", "repo", 1)
        self.assertEqual(result, {"number": 1})
        self.client._request.assert_called_with("GET", "/repos/owner/repo/pulls/1")

    def test_get_pull_request_files(self):
        """Test the get_pull_request_files method."""
        self.client._request.return_value = [{"filename": "test.py"}]
        result = self.client.get_pull_request_files("owner", "repo", 1)
        self.assertEqual(result, [{"filename": "test.py"}])
        self.client._request.assert_called_with("GET", "/repos/owner/repo/pulls/1/files")

    def test_create_comment(self):
        """Test the create_comment method."""
        self.client._request.return_value = {"id": 1}
        result = self.client.create_comment("owner", "repo", 1, "test comment")
        self.assertEqual(result, {"id": 1})
        self.client._request.assert_called_with(
            "POST",
            "/repos/owner/repo/issues/1/comments",
            json={"body": "test comment"}
        )

    def test_create_review_comment(self):
        """Test the create_review_comment method."""
        self.client._request.return_value = {"id": 1}
        result = self.client.create_review_comment(
            "owner", "repo", 1, "test comment", "commit123", "file.py", 10
        )
        self.assertEqual(result, {"id": 1})
        self.client._request.assert_called_with(
            "POST",
            "/repos/owner/repo/pulls/1/comments",
            json={
                "body": "test comment",
                "commit_id": "commit123",
                "path": "file.py",
                "position": 10
            }
        )


if __name__ == "__main__":
    unittest.main()
