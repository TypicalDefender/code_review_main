# Git Integration Service

This service handles integration with Git platforms (GitHub, GitLab, etc.) and provides a unified API for other services to interact with Git repositories.

## Features

- Webhook handling for Git platforms
- Kafka integration for consuming webhook events
- API for retrieving repository and pull request information
- Standardized models for Git objects across different platforms

## Supported Platforms

- GitHub (implemented)
- GitLab (planned)
- Azure DevOps (planned)
- Bitbucket (planned)

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set environment variables:
   ```
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Run the service:
   ```
   python src/main.py
   ```

## API Endpoints

- `GET /`: Root endpoint
- `GET /health`: Health check endpoint
- `POST /webhooks/github`: GitHub webhook endpoint
- `GET /api/pull-requests/{platform}/{owner}/{repo}/{number}`: Get pull request information

## Docker

Build the Docker image:
```
docker build -t git-integration-service .
```

Run the Docker container:
```
docker run -p 8000:8000 \
  -e GITHUB_TOKEN=your_github_token \
  -e GITHUB_WEBHOOK_SECRET=your_webhook_secret \
  -e KAFKA_BOOTSTRAP_SERVERS=kafka:9092 \
  git-integration-service
```

## Development

This service is part of the Open Source AI Code Review System. It is designed to be run as a microservice in a larger system.
