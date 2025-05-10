"""
Main entry point for the webhook service.

This service handles webhooks from various Git platforms (GitHub, GitLab, etc.)
and produces validated messages to Kafka topics for further processing.
"""

import os
import logging
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.config import Settings, get_settings
from src.auth.app_auth import AppAuthManager, get_app_auth_manager
from src.handlers.github_handler import GitHubWebhookHandler
from src.messaging.kafka_producer import KafkaProducer, get_kafka_producer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Webhook Service",
    description="Service for handling webhooks from Git platforms",
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

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    # Initialize Kafka producer
    kafka_producer = get_kafka_producer()
    await kafka_producer.start()
    logger.info("Kafka producer started")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    # Stop Kafka producer
    kafka_producer = get_kafka_producer()
    await kafka_producer.stop()
    logger.info("Kafka producer stopped")

# Define API routes
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Webhook Service"}

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.post("/webhooks/github/{app_id}")
async def github_webhook(
    app_id: str,
    request: Request,
    settings: Settings = Depends(get_settings),
    auth_manager: AppAuthManager = Depends(get_app_auth_manager),
    kafka_producer: KafkaProducer = Depends(get_kafka_producer),
):
    """GitHub webhook endpoint.
    
    Args:
        app_id: The ID of the app that is receiving the webhook
        request: The incoming webhook request
        
    Returns:
        A response indicating the result of processing the webhook
    """
    # Authenticate the app
    app = await auth_manager.authenticate_app(app_id, request)
    if not app:
        raise HTTPException(status_code=401, detail="Invalid app credentials")
    
    # Create webhook handler
    handler = GitHubWebhookHandler(app, kafka_producer)
    
    # Process the webhook
    return await handler.handle_webhook(request)

# Run the app
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=True,
    )
