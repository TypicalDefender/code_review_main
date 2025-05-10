# OpenCodeReview

<p align="center">
  <img src="docs/images/logo.png" alt="OpenCodeReview Logo" width="200"/>
</p>

<p align="center">
  <strong>Open Source AI-powered Code Review System</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#getting-started">Getting Started</a> •
  <a href="#deployment">Deployment</a> •
  <a href="#configuration">Configuration</a> •
  <a href="#contributing">Contributing</a> •
  <a href="#license">License</a>
</p>

---

## Features

OpenCodeReview is an open-source AI-powered code review system that helps teams improve code quality, catch bugs early, and streamline the review process.

### Key Features

- **AI-Powered Code Reviews**: Automated, context-aware code reviews using state-of-the-art language models
- **Git Platform Integration**: Seamless integration with GitHub, GitLab, Azure DevOps, and Bitbucket
- **Interactive Chat**: Natural language conversations about code changes directly in pull requests
- **Static Analysis**: Integration with popular linters and security analysis tools
- **Customizable Reviews**: Configure review strictness and focus areas based on your team's preferences
- **Learning Capability**: System learns from feedback to improve future reviews
- **Issue Tracking**: Integration with popular issue tracking systems
- **Custom Reports**: Generate detailed reports on code quality and changes
- **Self-Hosted Option**: Deploy on your own infrastructure for complete control and privacy

## Architecture

OpenCodeReview is built using a microservices architecture, with each component handling a specific aspect of the code review process.

### Core Components

- **Git Integration Service**: Handles communication with Git platforms
- **Code Analysis Engine**: Parses and analyzes code changes
- **AI Review Service**: Generates intelligent code reviews using LLMs
- **Chat Service**: Manages natural language conversations
- **Knowledge Base**: Stores and applies learned preferences
- **Configuration Manager**: Handles system configuration
- **Reporting Service**: Generates reports and summaries
- **Issue Tracking Integration**: Connects with issue tracking systems

For more details, see the [Architecture Documentation](docs/architecture/README.md).

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Git
- Python 3.9+
- Node.js 16+

### Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/opencodereviews/opencodereviews.git
   cd opencodereviews
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Start the services:
   ```bash
   docker-compose up -d
   ```

4. Access the web interface:
   ```
   http://localhost:3000
   ```

For more detailed instructions, see the [Getting Started Guide](docs/user-guides/getting-started.md).

## Deployment

OpenCodeReview can be deployed in various environments:

### Docker Compose

Ideal for small teams or testing:

```bash
docker-compose -f deployment/docker-compose.yml up -d
```

### Kubernetes

For production environments:

```bash
kubectl apply -f deployment/kubernetes/
```

### Helm

For managed Kubernetes environments:

```bash
helm install opencodereviews deployment/helm/opencodereviews
```

For more deployment options, see the [Deployment Guide](docs/deployment/README.md).

## Configuration

OpenCodeReview is highly configurable through a YAML configuration file. See [sample-config.yaml](sample-config.yaml) for a complete example.

### Basic Configuration

Create a `.opencodereviews.yaml` file in the root of your repository:

```yaml
reviews:
  profile: "Balanced"
  scope:
    include:
      - "**/*.py"
      - "**/*.js"
    exclude:
      - "**/node_modules/**"
  
  instructions:
    default: |
      Focus on code quality, security, and performance issues.
```

For more configuration options, see the [Configuration Guide](docs/user-guides/configuration.md).

## Contributing

We welcome contributions from the community! Please see our [Contributing Guidelines](CONTRIBUTING.md) for more information.

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/opencodereviews/opencodereviews.git
   cd opencodereviews
   ```

2. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

3. Run tests:
   ```bash
   pytest
   ```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Made with ❤️ by the OpenCodeReview Team
</p>
