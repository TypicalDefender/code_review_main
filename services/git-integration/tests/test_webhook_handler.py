"""
Tests for the GitHub webhook handler.
"""

import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import json
import os
import sys
import hmac
import hashlib

# Add the src directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from src.github.webhook_handler import WebhookHandler


class TestWebhookHandler(unittest.TestCase):
    """Tests for the GitHub webhook handler."""

    def setUp(self):
        """Set up the test environment."""
        self.config = MagicMock()
        self.config.get.return_value = "test_secret"

        self.message_queue = MagicMock()
        self.message_queue.publish = AsyncMock()

        self.github_client = MagicMock()

        self.handler = WebhookHandler(self.config, self.message_queue, self.github_client)

    @patch("github.webhook_handler.hmac")
    async def test_verify_signature(self, mock_hmac):
        """Test the verify_signature method."""
        # Mock the request
        request = MagicMock()
        request.body = AsyncMock(return_value=b'{"test": "data"}')
        request.headers = {"X-Hub-Signature-256": "sha256=test_signature"}

        # Mock hmac.compare_digest to return True
        mock_hmac.compare_digest.return_value = True

        # Test successful verification
        result = await self.handler.verify_signature(request)
        self.assertTrue(result)

        # Test failed verification
        mock_hmac.compare_digest.return_value = False
        result = await self.handler.verify_signature(request)
        self.assertFalse(result)

        # Test missing signature header
        request.headers = {}
        result = await self.handler.verify_signature(request)
        self.assertFalse(result)

    @patch("github.webhook_handler.WebhookHandler.verify_signature")
    async def test_handle_webhook(self, mock_verify):
        """Test the handle_webhook method."""
        # Mock the request
        request = MagicMock()
        request.body = AsyncMock(return_value=b'{"action": "opened", "pull_request": {"number": 1}, "repository": {"name": "test-repo", "owner": {"login": "test-owner"}}}')
        request.headers = {
            "X-Hub-Signature-256": "sha256=test_signature",
            "X-GitHub-Event": "pull_request"
        }

        # Mock verify_signature to return True
        mock_verify.return_value = True

        # Mock _handle_pull_request_event
        self.handler._handle_pull_request_event = AsyncMock(return_value={"message": "success"})

        # Test successful handling of pull request event
        result = await self.handler.handle_webhook(request)
        self.assertEqual(result, {"message": "success"})
        self.handler._handle_pull_request_event.assert_called_once()

        # Test ping event
        request.headers["X-GitHub-Event"] = "ping"
        result = await self.handler.handle_webhook(request)
        self.assertEqual(result, {"message": "Pong!"})

        # Test unsupported event
        request.headers["X-GitHub-Event"] = "unsupported"
        result = await self.handler.handle_webhook(request)
        self.assertEqual(result["message"], "Event type unsupported not supported")

        # Test invalid signature
        mock_verify.return_value = False
        with self.assertRaises(Exception):
            await self.handler.handle_webhook(request)

    async def test_handle_pull_request_event(self):
        """Test the _handle_pull_request_event method."""
        # Test payload
        payload = {
            "action": "opened",
            "pull_request": {
                "number": 1,
                "title": "Test PR",
                "body": "Test description",
                "created_at": "2023-05-10T12:00:00Z",
                "updated_at": "2023-05-10T12:00:00Z",
                "head": {"sha": "test-sha"},
                "base": {"sha": "base-sha"}
            },
            "repository": {
                "name": "test-repo",
                "owner": {"login": "test-owner"}
            },
            "sender": {"login": "test-user"}
        }

        # Test successful handling
        result = await self.handler._handle_pull_request_event(payload)
        self.assertEqual(result["message"], "Pull request queued for review")
        self.assertEqual(result["repo"], "test-owner/test-repo")
        self.assertEqual(result["pr_number"], 1)

        # Verify message_queue.publish was called with the right arguments
        self.message_queue.publish.assert_called_once()
        args = self.message_queue.publish.call_args[0]
        self.assertEqual(args[0], "pull_request.review")
        self.assertEqual(args[1]["platform"], "github")
        self.assertEqual(args[1]["repo_owner"], "test-owner")
        self.assertEqual(args[1]["repo_name"], "test-repo")
        self.assertEqual(args[1]["pr_number"], 1)

        # Test ignored action
        payload["action"] = "closed"
        result = await self.handler._handle_pull_request_event(payload)
        self.assertEqual(result["message"], "Ignoring pull request action: closed")


if __name__ == "__main__":
    unittest.main()
