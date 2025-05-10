"""
GitHub API client for the git-integration service.
This module provides functionality to interact with the GitHub API.
"""

import os
import requests
from typing import Dict, List, Optional, Any, Union
import logging

logger = logging.getLogger(__name__)

class GitHubClient:
    """
    Client for interacting with the GitHub API.
    """
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize the GitHub client.
        
        Args:
            token: GitHub personal access token or app token
        """
        self.token = token or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            logger.warning("No GitHub token provided. Requests may be rate-limited.")
        
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "OpenSourceCodeReview-GitIntegration"
        })
        
        if self.token:
            self.session.headers.update({
                "Authorization": f"token {self.token}"
            })
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Union[Dict, List, Any]:
        """
        Make a request to the GitHub API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            Response data as JSON
            
        Raises:
            requests.HTTPError: If the request fails
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        
        if response.status_code == 204:  # No content
            return {}
            
        return response.json()
    
    def get_repository(self, owner: str, repo: str) -> Dict:
        """
        Get information about a repository.
        
        Args:
            owner: Repository owner (user or organization)
            repo: Repository name
            
        Returns:
            Repository information
        """
        return self._request("GET", f"/repos/{owner}/{repo}")
    
    def get_pull_requests(self, owner: str, repo: str, state: str = "open") -> List[Dict]:
        """
        Get pull requests for a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: Pull request state (open, closed, all)
            
        Returns:
            List of pull requests
        """
        return self._request("GET", f"/repos/{owner}/{repo}/pulls", params={"state": state})
    
    def get_pull_request(self, owner: str, repo: str, pr_number: int) -> Dict:
        """
        Get a specific pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            
        Returns:
            Pull request information
        """
        return self._request("GET", f"/repos/{owner}/{repo}/pulls/{pr_number}")
    
    def get_pull_request_files(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """
        Get files changed in a pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            
        Returns:
            List of files changed in the pull request
        """
        return self._request("GET", f"/repos/{owner}/{repo}/pulls/{pr_number}/files")
    
    def create_comment(self, owner: str, repo: str, pr_number: int, body: str) -> Dict:
        """
        Create a comment on a pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            body: Comment text
            
        Returns:
            Created comment information
        """
        return self._request("POST", f"/repos/{owner}/{repo}/issues/{pr_number}/comments", 
                            json={"body": body})
    
    def create_review_comment(self, owner: str, repo: str, pr_number: int, 
                             body: str, commit_id: str, path: str, position: int) -> Dict:
        """
        Create a review comment on a specific line of a pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            body: Comment text
            commit_id: Commit SHA
            path: File path
            position: Position in the diff
            
        Returns:
            Created review comment information
        """
        return self._request("POST", f"/repos/{owner}/{repo}/pulls/{pr_number}/comments",
                            json={
                                "body": body,
                                "commit_id": commit_id,
                                "path": path,
                                "position": position
                            })
