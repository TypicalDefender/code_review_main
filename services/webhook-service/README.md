# Webhook Service

This service handles webhooks from various Git platforms (GitHub, GitLab, etc.) and produces validated messages to Kafka topics for further processing.

## Features

- Generic webhook receiver with app-based authentication
- Validation and enrichment of webhook payloads
- Kafka integration for message queuing
- Support for multiple Git platforms (GitHub implemented, others planned)

## Architecture

The webhook service follows a message validation/enrichment pattern:

1. **Webhook Receiver**: Receives webhooks from Git platforms
2. **Authentication**: Validates the webhook signature and authenticates the app
3. **Validation**: Validates the webhook payload structure
4. **Enrichment**: Enriches the payload with additional context
5. **Message Production**: Produces validated messages to Kafka topics

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Run the service:
   ```
   uvicorn src.main:app --reload
   ```

## API Endpoints

- `GET /`: Root endpoint
- `GET /health`: Health check endpoint
- `POST /webhooks/github/{app_id}`: GitHub webhook endpoint

## App-Based Authentication

The webhook service uses app-based authentication to secure webhooks. Each app has:

- A unique identifier
- A webhook secret for validating webhook signatures
- An API key for authenticating API requests
- A set of permissions that define what the app can do
- A set of scopes that define which repositories the app can access

## Kafka Topics

The webhook service produces messages to the following Kafka topics:

- `webhook.github.raw`: Raw GitHub webhook events
- `webhook.github.validated`: Validated GitHub webhook events

## Docker

Build the Docker image:
```
docker build -t webhook-service .
```

Run the Docker container:
```
docker run -p 8000:8000 -e KAFKA_BOOTSTRAP_SERVERS=kafka:9092 webhook-service
```

## Development

This service is part of the Open Source AI Code Review System. It is designed to be run as a microservice in a larger system.

### Adding Support for New Git Platforms

To add support for a new Git platform:

1. Create a new handler in `src/handlers/`
2. Add the platform to the `GitPlatform` enum in `src/models/webhook.py`
3. Add the platform's event types to the `WebhookEventType` enum
4. Add a new endpoint in `src/main.py`
5. Add Kafka topics for the platform in `src/config.py`
