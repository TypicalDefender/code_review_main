#!/usr/bin/env python3
"""
Script to register a new app with the webhook service.

This script is for development and testing purposes only.
In a production environment, app registration would be handled by a proper admin interface.
"""

import os
import sys
import uuid
import secrets
import argparse
import json
import httpx

def generate_api_key():
    """Generate a random API key."""
    return secrets.token_urlsafe(32)

def generate_webhook_secret():
    """Generate a random webhook secret."""
    return secrets.token_hex(32)

def register_app(args):
    """Register a new app with the webhook service."""
    # Generate app ID if not provided
    app_id = args.id or f"app-{uuid.uuid4()}"
    
    # Generate API key and webhook secret if not provided
    api_key = args.api_key or generate_api_key()
    webhook_secret = args.webhook_secret or generate_webhook_secret()
    
    # Create app data
    app_data = {
        "id": app_id,
        "name": args.name,
        "description": args.description,
        "owner": args.owner,
        "permissions": args.permissions.split(",") if args.permissions else ["receive:webhook"],
        "scopes": [
            {
                "owner": args.repo_owner,
                "repositories": args.repositories.split(",") if args.repositories else None
            }
        ],
        "webhook_secret": webhook_secret,
        "api_key": api_key,
        "active": True
    }
    
    # Print app data
    print("App data:")
    print(json.dumps(app_data, indent=2))
    
    # Save app data to file if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump(app_data, f, indent=2)
        print(f"App data saved to {args.output}")
    
    # Register app with webhook service if requested
    if args.register:
        try:
            response = httpx.post(
                f"{args.url}/api/apps",
                json=app_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            print(f"App registered successfully: {response.json()}")
        except Exception as e:
            print(f"Error registering app: {e}")
    
    # Print GitHub webhook setup instructions
    print("\nGitHub Webhook Setup Instructions:")
    print(f"1. Go to your GitHub repository settings")
    print(f"2. Click on 'Webhooks' and then 'Add webhook'")
    print(f"3. Set the Payload URL to: {args.webhook_url}/{app_id}")
    print(f"4. Set the Content type to: application/json")
    print(f"5. Set the Secret to: {webhook_secret}")
    print(f"6. Select the events you want to trigger the webhook")
    print(f"7. Click 'Add webhook'")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Register a new app with the webhook service")
    
    # App information
    parser.add_argument("--id", help="App ID (generated if not provided)")
    parser.add_argument("--name", required=True, help="App name")
    parser.add_argument("--description", help="App description")
    parser.add_argument("--owner", required=True, help="App owner (email)")
    
    # Permissions and scopes
    parser.add_argument("--permissions", help="Comma-separated list of permissions")
    parser.add_argument("--repo-owner", help="Repository owner (user or organization)")
    parser.add_argument("--repositories", help="Comma-separated list of repositories")
    
    # Authentication
    parser.add_argument("--api-key", help="API key (generated if not provided)")
    parser.add_argument("--webhook-secret", help="Webhook secret (generated if not provided)")
    
    # Output
    parser.add_argument("--output", help="Output file for app data")
    
    # Registration
    parser.add_argument("--register", action="store_true", help="Register app with webhook service")
    parser.add_argument("--url", default="http://localhost:8000", help="Webhook service URL")
    parser.add_argument("--webhook-url", default="http://localhost:8000/webhooks/github", help="Webhook URL")
    
    args = parser.parse_args()
    register_app(args)

if __name__ == "__main__":
    main()
