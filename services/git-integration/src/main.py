"""
Main entry point for the git-integration service.

This service handles integration with Git platforms (GitHub, GitLab, etc.)
and provides a unified API for other services to interact with Git repositories.
"""

import os
import logging
import asyncio
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional

from src.github.client import GitHubClient
from src.github.webhook_handler import WebhookHandler
from src.github.kafka_webhook_handler import KafkaWebhookHandler
from src.common.kafka_consumer import KafkaConsumer
from src.models import GitPlatform

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Git Integration Service",
    description="Service for integrating with Git platforms",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock configuration and message queue for now
class Config:
    """Simple configuration class."""

    def __init__(self):
        self.config = {
            # GitHub configuration
            "git.github.webhook_secret": os.environ.get("GITHUB_WEBHOOK_SECRET"),
            "git.github.token": os.environ.get("GITHUB_TOKEN"),

            # Chat configuration
            "chat.commands.prefix": os.environ.get("CHAT_COMMANDS_PREFIX", "@opencr"),

            # Kafka configuration
            "kafka.bootstrap_servers": os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
            "kafka.security_protocol": os.environ.get("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
            "kafka.sasl_mechanism": os.environ.get("KAFKA_SASL_MECHANISM"),
            "kafka.sasl_username": os.environ.get("KAFKA_SASL_USERNAME"),
            "kafka.sasl_password": os.environ.get("KAFKA_SASL_PASSWORD"),
            "kafka.consumer_group_id": os.environ.get("KAFKA_CONSUMER_GROUP_ID", "git-integration"),
            "kafka.auto_offset_reset": os.environ.get("KAFKA_AUTO_OFFSET_RESET", "earliest"),
            "kafka.github_validated_topic": os.environ.get("KAFKA_GITHUB_VALIDATED_TOPIC", "webhook.github.validated"),
        }

    def get(self, key, default=None):
        """Get a configuration value."""
        return self.config.get(key, default)

class MessageQueue:
    """Simple message queue class."""

    async def publish(self, topic: str, message: Dict[str, Any]):
        """Publish a message to a topic."""
        logger.info(f"Publishing message to {topic}: {message}")
        # In a real implementation, this would publish to a message broker
        return True

# Create dependencies
def get_config():
    """Get the configuration."""
    return Config()

def get_message_queue():
    """Get the message queue."""
    return MessageQueue()

def get_github_client():
    """Get the GitHub client."""
    token = os.environ.get("GITHUB_TOKEN")
    return GitHubClient(token=token)

def get_webhook_handler(
    config: Config = Depends(get_config),
    message_queue: MessageQueue = Depends(get_message_queue),
    github_client: GitHubClient = Depends(get_github_client),
):
    """Get the webhook handler."""
    return WebhookHandler(config, message_queue, github_client)

def get_kafka_consumer(config: Config = Depends(get_config)):
    """Get the Kafka consumer."""
    return KafkaConsumer(config)

def get_kafka_webhook_handler(
    config: Config = Depends(get_config),
    message_queue: MessageQueue = Depends(get_message_queue),
    github_client: GitHubClient = Depends(get_github_client),
):
    """Get the Kafka webhook handler."""
    return KafkaWebhookHandler(config, message_queue, github_client)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    # Initialize Kafka consumer
    config = get_config()
    kafka_consumer = get_kafka_consumer(config)
    kafka_webhook_handler = get_kafka_webhook_handler(config, get_message_queue(), get_github_client())

    # Register handlers for Kafka topics
    kafka_consumer.register_handler(
        config.get("kafka.github_validated_topic"),
        kafka_webhook_handler.handle_webhook_event
    )

    # Start the Kafka consumer
    await kafka_consumer.start()
    logger.info("Kafka consumer started")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    # Stop Kafka consumer
    kafka_consumer = get_kafka_consumer()
    await kafka_consumer.stop()
    logger.info("Kafka consumer stopped")

# Define API routes
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Git Integration Service"}

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.post("/webhooks/github")
async def github_webhook(
    request: Request,
    webhook_handler: WebhookHandler = Depends(get_webhook_handler),
):
    """GitHub webhook endpoint."""
    return await webhook_handler.handle_webhook(request)

# Define API models
class PullRequestInfo(BaseModel):
    """Model for pull request information."""
    platform: GitPlatform
    owner: str
    repo: str
    number: int

class PullRequestResponse(BaseModel):
    """Model for pull request response."""
    id: str
    number: int
    title: str
    url: str

@app.get("/api/pull-requests/{platform}/{owner}/{repo}/{number}")
async def get_pull_request(
    platform: GitPlatform,
    owner: str,
    repo: str,
    number: int,
    github_client: GitHubClient = Depends(get_github_client),
):
    """Get information about a pull request."""
    if platform == GitPlatform.GITHUB:
        try:
            pr_data = github_client.get_pull_request(owner, repo, number)
            return PullRequestResponse(
                id=str(pr_data["id"]),
                number=pr_data["number"],
                title=pr_data["title"],
                url=pr_data["html_url"],
            )
        except Exception as e:
            logger.error(f"Error getting pull request: {e}")
            raise HTTPException(status_code=500, detail="Error getting pull request")
    else:
        raise HTTPException(status_code=400, detail=f"Platform {platform} not supported yet")

# Run the app
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=True,
    )
