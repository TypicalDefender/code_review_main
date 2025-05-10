# Open Source AI Code Review System - Project Structure

```
/
├── .github/                      # GitHub specific files
│   ├── workflows/                # GitHub Actions workflows
│   │   ├── ci.yml                # Continuous Integration workflow
│   │   └── release.yml           # Release workflow
│   └── ISSUE_TEMPLATE/           # Issue templates
├── docs/                         # Documentation
│   ├── architecture/             # Architecture documentation
│   ├── api/                      # API documentation
│   ├── deployment/               # Deployment guides
│   └── user-guides/              # User guides
├── services/                     # Microservices
│   ├── api-gateway/              # API Gateway service
│   │   ├── src/                  # Source code
│   │   ├── Dockerfile            # Docker configuration
│   │   └── requirements.txt      # Dependencies
│   ├── git-integration/          # Git platform integration service
│   │   ├── src/                  # Source code
│   │   │   ├── github/           # GitHub integration
│   │   │   ├── gitlab/           # GitLab integration
│   │   │   ├── azure-devops/     # Azure DevOps integration
│   │   │   └── bitbucket/        # Bitbucket integration
│   │   ├── Dockerfile            # Docker configuration
│   │   └── requirements.txt      # Dependencies
│   ├── code-analysis/            # Code analysis service
│   │   ├── src/                  # Source code
│   │   │   ├── parsers/          # Code parsers
│   │   │   ├── analyzers/        # Static analyzers
│   │   │   └── security/         # Security analyzers
│   │   ├── Dockerfile            # Docker configuration
│   │   └── requirements.txt      # Dependencies
│   ├── ai-review/                # AI review service
│   │   ├── src/                  # Source code
│   │   │   ├── llm/              # LLM integration
│   │   │   ├── prompts/          # Prompt templates
│   │   │   └── suggestions/      # Suggestion generators
│   │   ├── Dockerfile            # Docker configuration
│   │   └── requirements.txt      # Dependencies
│   ├── chat/                     # Chat service
│   │   ├── src/                  # Source code
│   │   ├── Dockerfile            # Docker configuration
│   │   └── requirements.txt      # Dependencies
│   ├── knowledge-base/           # Knowledge base service
│   │   ├── src/                  # Source code
│   │   ├── Dockerfile            # Docker configuration
│   │   └── requirements.txt      # Dependencies
│   ├── config-manager/           # Configuration management service
│   │   ├── src/                  # Source code
│   │   ├── Dockerfile            # Docker configuration
│   │   └── requirements.txt      # Dependencies
│   ├── reporting/                # Reporting service
│   │   ├── src/                  # Source code
│   │   ├── Dockerfile            # Docker configuration
│   │   └── requirements.txt      # Dependencies
│   └── issue-tracking/           # Issue tracking service
│       ├── src/                  # Source code
│       ├── Dockerfile            # Docker configuration
│       └── requirements.txt      # Dependencies
├── web/                          # Web UI
│   ├── src/                      # Source code
│   ├── public/                   # Public assets
│   ├── Dockerfile                # Docker configuration
│   └── package.json              # Dependencies
├── deployment/                   # Deployment configurations
│   ├── docker-compose.yml        # Docker Compose configuration
│   ├── kubernetes/               # Kubernetes manifests
│   │   ├── services/             # Service manifests
│   │   └── deployments/          # Deployment manifests
│   └── helm/                     # Helm charts
├── scripts/                      # Utility scripts
│   ├── setup.sh                  # Setup script
│   └── deploy.sh                 # Deployment script
├── .gitignore                    # Git ignore file
├── LICENSE                       # License file
└── README.md                     # Project README
```
