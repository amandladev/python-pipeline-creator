# 🚀 Pipeline Creator CLI

**A powerful CLI tool for creating and managing enterprise-grade CI/CD pipelines on AWS with intelligent automation.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![AWS CDK](https://img.shields.io/badge/AWS-CDK-orange.svg)](https://aws.amazon.com/cdk/)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## ✨ Features

- 🏗️ **Smart Pipeline Generation** - Automated AWS CodePipeline creation with CDK
- 📦 **Multi-Language Support** - Python, Node.js, React, and more
- 🧪 **Advanced Build Stages** - SonarQube, Snyk, Codecov, ESLint, Bandit integration
- 📧 **Intelligent Notifications** - Slack, Email, Webhooks with smart alerting rules  
- 📋 **Pipeline Templates** - Reusable templates for faster setup
- 🔄 **Template Inheritance** - Extend and customize existing templates
- ⚙️ **Interactive CLI** - User-friendly prompts and rich console output
- 🛡️ **Security First** - Built-in security scanning and best practices

## 🚀 Quick Start

### Installation

```bash
# 1. Clone and setup
git clone <repository-url>
cd pipeline_creator

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
# or .venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -e .
pip install aiohttp email-validator  # For notifications
```

### Create Your First Pipeline

```bash
# 1. Initialize a new pipeline
pipeline init

# 2. Use a template for quick setup (optional)
pipeline templates use react-app -P app_name=my-app

# 3. Generate AWS infrastructure
pipeline generate

# 4. Deploy your pipeline
pipeline deploy
```

## 📋 Complete Command Reference

### Core Pipeline Commands

#### `pipeline init`
Initialize pipeline configuration in your project.
```bash
pipeline init                    # Interactive setup
pipeline init --name my-app     # Quick setup with name
```

#### `pipeline generate`
Generate AWS CDK infrastructure files.
```bash
pipeline generate               # Generate all infrastructure
pipeline generate --force      # Overwrite existing files
```

#### `pipeline deploy`
Deploy your pipeline to AWS.
```bash
pipeline deploy                 # Deploy with confirmation
pipeline deploy --auto-approve  # Skip confirmations
```

#### `pipeline status`
Check your pipeline status.
```bash
pipeline status                 # Show current status
pipeline status --detailed     # Include execution history
```

#### `pipeline logs`
View pipeline logs.
```bash
pipeline logs                   # Latest execution logs
pipeline logs --build-id <id>  # Specific build logs
```

### 🧪 Extra Build Stages

#### `pipeline add-stage`
Add specialized build stages to your pipeline.
```bash
pipeline add-stage              # Interactive stage selection
pipeline add-stage sonarqube   # Add SonarQube analysis
pipeline add-stage snyk        # Add security scanning
pipeline add-stage codecov     # Add coverage reporting
pipeline add-stage docker      # Add Docker build
```

**Available Stages:**
- 🔍 **SonarQube Cloud** - Code quality analysis
- 🛡️ **Snyk Security** - Vulnerability scanning  
- 📊 **Codecov** - Coverage reporting
- 🐳 **Docker Build** - Container builds
- 🧹 **ESLint** - JavaScript/TypeScript linting
- 🐍 **Bandit** - Python security linting
- ⚙️ **Custom Stages** - Define your own build steps

### 📧 Notification System

#### `pipeline notifications`
Intelligent notification management with smart alerting rules.

```bash
# Setup notifications
pipeline notifications setup              # Interactive setup
pipeline notifications setup -c slack    # Setup specific channel

# Check status
pipeline notifications status            # View current config

# Test notifications  
pipeline notifications test              # Send test messages

# Disable notifications
pipeline notifications disable           # Disable all channels
```

**Supported Channels:**
- 📧 **Email** - HTML/text email notifications via SMTP
- 📢 **Slack** - Rich webhook notifications with formatting
- 🔗 **Webhooks** - Custom HTTP endpoints with JSON payloads

**Smart Features:**
- ⚡ **Failure Alerts** - Always notify on pipeline failures
- 🎉 **Recovery Notifications** - Alert when pipeline recovers
- 🔇 **Spam Prevention** - Intelligent rules to reduce noise
- 📈 **Event History** - Track notification patterns

### 📋 Template System

#### `pipeline templates`
Powerful template system for reusable pipeline configurations.

```bash
# List available templates
pipeline templates list                   # All templates
pipeline templates list --category api   # Filter by category

# Get template information
pipeline templates info react-app        # Detailed template info

# Use templates
pipeline templates use react-app \
  -P app_name=my-app \
  -P test_coverage_threshold=90

# Create custom templates
pipeline templates create my-template \
  --description "My custom pipeline" \
  --category web-frontend \
  --author "My Team"

# Template inheritance
pipeline templates extend react-app enhanced-react \
  --description "Enhanced React template"

# Share templates
pipeline templates export react-app template.json
pipeline templates import-template template.json
```

**Predefined Templates:**
- 🌐 **react-app** - Complete React application with S3 + CloudFront
- 🔌 **python-api** - Python/FastAPI API with ECS Fargate
- 🟨 **nodejs-api** - Node.js/Express API with containers

**Template Categories:**
- `web-frontend` - Frontend applications
- `web-backend` - Backend services  
- `api` - API services
- `microservice` - Microservices
- `mobile` - Mobile applications
- `data-processing` - Data pipelines
- `ml-ai` - Machine Learning workflows

## 🛠️ Prerequisites

- **Python 3.8+** with pip
- **AWS CLI** configured (`aws configure`)
- **Node.js 16+** (for AWS CDK)
- **Docker** (optional, for containerized builds)

## 📁 Project Structure

After initialization, your project will have:

```
your-project/
├── pipeline.json           # Main pipeline configuration
├── .pipeline/             
│   ├── cdk/               # Generated CDK files
│   ├── config.json        # Internal configuration
│   └── templates/         # User templates (if any)
└── buildspec.yml          # CodeBuild specification
```

## 🎯 Configuration Examples

### Basic Python API Pipeline
```json
{
  "name": "my-python-api",
  "project_type": "python",
  "runtime": {
    "language": "python", 
    "version": "3.11"
  },
  "build": {
    "commands": [
      "pip install -r requirements.txt",
      "pytest tests/",
      "docker build -t my-api ."
    ]
  },
  "deploy": {
    "type": "ecs-fargate",
    "config": {
      "container_port": 8000,
      "cpu": 256,
      "memory": 512
    }
  }
}
```

### React App with Extra Stages
```json
{
  "name": "my-react-app",
  "project_type": "react",
  "extra_stages": [
    {
      "name": "sonarqube",
      "type": "sonarqube_cloud",
      "config": {
        "project_key": "my-sonar-key",
        "sources": "src"
      }
    },
    {
      "name": "security-scan", 
      "type": "snyk",
      "config": {
        "language": "nodejs",
        "severity_threshold": "high"
      }
    }
  ],
  "notifications": {
    "enabled": true,
    "channels": ["slack", "email"],
    "events": ["pipeline_failed", "deploy_completed"]
  }
}
```

## 🚀 Advanced Usage

### Environment Variables
Set these environment variables for enhanced functionality:

```bash
export SONAR_TOKEN="your-sonar-token"
export SNYK_TOKEN="your-snyk-token" 
export CODECOV_TOKEN="your-codecov-token"
export SLACK_WEBHOOK_URL="your-slack-webhook"
```

### Custom Build Stages
Add custom build logic to your pipeline:

```json
{
  "extra_stages": [
    {
      "name": "custom-build",
      "type": "custom",
      "config": {
        "commands": [
          "echo 'Running custom build steps'",
          "npm run custom-script",
          "python custom_script.py"
        ],
        "environment_variables": {
          "CUSTOM_VAR": "custom_value"
        }
      }
    }
  ]
}
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pipeline_creator --cov-report=html

# Run specific test modules
pytest tests/test_templates.py
pytest tests/test_notifications.py
```

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Install** development dependencies (`pip install -e .[dev]`)
4. **Write** tests for your changes
5. **Run** tests (`pytest`)
6. **Commit** your changes (`git commit -m 'Add amazing feature'`)
7. **Push** to the branch (`git push origin feature/amazing-feature`)
8. **Create** a Pull Request

### Development Setup
```bash
# Install development dependencies
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install

# Run linting
flake8 pipeline_creator/
black pipeline_creator/

# Run type checking
mypy pipeline_creator/
```

## 📚 Documentation

- [Getting Started Guide](docs/getting-started.md)
- [Template Creation Guide](docs/templates.md)
- [Notification Setup](docs/notifications.md)
- [Advanced Configuration](docs/advanced.md)
- [API Reference](docs/api.md)

## ❓ Troubleshooting

### Common Issues

**Q: "ModuleNotFoundError" when running commands**  
A: Make sure you've activated your virtual environment and installed dependencies:
```bash
source .venv/bin/activate
pip install -e .
```

**Q: AWS deployment fails with permissions error**  
A: Ensure your AWS credentials have the necessary permissions:
```bash
aws sts get-caller-identity  # Check current identity
aws configure list          # Check configuration
```

**Q: Notifications not working**  
A: Check your notification configuration:
```bash
pipeline notifications status
pipeline notifications test
```

## 🎉 What's New

### v0.3.0 - Template System
- ✨ Complete template system with inheritance
- 📋 3 predefined templates (React, Python API, Node.js API)
- 🔄 Template import/export functionality
- 🎯 Interactive parameter configuration

### v0.2.0 - Smart Notifications  
- 📧 Multi-channel notification support (Email, Slack, Webhooks)
- ⚡ Smart alerting rules to reduce spam
- 🎨 Rich HTML email templates
- 📊 Event history and analytics

### v0.1.0 - Core Features
- 🏗️ AWS CodePipeline generation with CDK
- 🧪 Extra build stages (SonarQube, Snyk, Codecov)
- ⚙️ Interactive CLI with rich console output
- 📦 Multi-language project support

## 🔮 What's Next

We're continuously improving Pipeline Creator CLI! Here's our exciting roadmap:

### 🎯 v0.4.0 - Multi-Environment Support (In Progress)
- 🌍 **Environment Management** - Staging, production, and custom environments
- 🚪 **Approval Gates** - Manual approval workflows between environments  
- 🔄 **Progressive Deployments** - Blue-green and canary deployment strategies
- ⚙️ **Environment-Specific Configs** - Different settings per environment
- 🔁 **Automatic Rollbacks** - Smart rollback on deployment failures
- 🏷️ **Environment Tagging** - Resource organization and cost tracking

### 🚀 v0.5.0 - Enhanced Pipeline Intelligence
- 📊 **Pipeline Analytics** - Performance metrics and deployment insights
- 🤖 **AI-Powered Optimization** - Automatic pipeline improvements suggestions
- 🔍 **Dependency Analysis** - Smart dependency tracking and updates
- 📈 **Cost Optimization** - AWS cost analysis and recommendations
- 🕒 **Scheduling** - Time-based deployments and maintenance windows

### 🛡️ v0.6.0 - Enterprise Security & Governance
- 🔐 **RBAC Integration** - Role-based access control with AWS IAM
- 📋 **Compliance Templates** - SOC2, HIPAA, PCI-DSS compliant pipelines
- 🛡️ **Secret Management** - AWS Secrets Manager and Parameter Store integration
- 📊 **Audit Trails** - Comprehensive deployment and change logging
- 🔒 **Policy Enforcement** - Automated policy compliance checking

### 🌐 v0.7.0 - Multi-Cloud & Hybrid Support
- ☁️ **Azure DevOps** - Azure Pipelines generation and deployment
- 🔧 **Google Cloud Build** - GCP pipeline creation and management
- 🏢 **On-Premise Integration** - Jenkins and GitLab CI/CD support
- 🔗 **Multi-Cloud Deployments** - Cross-cloud deployment strategies
- 📦 **Universal Templates** - Cloud-agnostic pipeline templates

### 🎨 v0.8.0 - Developer Experience Enhancements
- 🖥️ **Web Dashboard** - Visual pipeline builder and monitoring
- 📱 **Mobile App** - Pipeline monitoring on the go
- 🔌 **IDE Extensions** - VS Code, IntelliJ, and other IDE integrations
- 🤝 **Git Integration** - Advanced Git hooks and branch strategies
- 📝 **Documentation Generator** - Auto-generate pipeline documentation

### 🧪 v0.9.0 - Advanced Testing & Quality
- 🤖 **Automated Testing** - AI-powered test generation and execution
- 🔍 **Performance Testing** - Load testing integration (k6, JMeter)
- 🌐 **Cross-Browser Testing** - Selenium Grid and Playwright support
- 📊 **Quality Gates** - Advanced quality metrics and thresholds
- 🐛 **Bug Prevention** - Predictive analysis for common issues

### 📦 v1.0.0 - Production Ready Enterprise Edition
- 🏢 **Enterprise Templates** - Industry-specific pipeline templates
- 📊 **Executive Dashboards** - C-level reporting and insights
- 🎓 **Training Materials** - Comprehensive documentation and tutorials
- 🔧 **Professional Support** - Dedicated support channels
- 🚀 **Performance Optimization** - Enterprise-scale performance tuning

## 💡 Community Requests

Vote for features you'd like to see next! Open an issue with the `feature-request` label:

- 🐍 **Python Package Publishing** - PyPI integration for Python projects
- 📦 **Docker Registry Support** - Private registry integration (ECR, Docker Hub)
- 🌊 **Kubernetes Deployments** - EKS and self-managed K8s support
- 🔄 **GitOps Integration** - ArgoCD and Flux support
- 📧 **Microsoft Teams** - Teams notification channel
- 🎯 **Terraform Integration** - Infrastructure as Code workflows
- 🔒 **HashiCorp Vault** - Advanced secret management
- 📈 **Datadog Integration** - Enhanced monitoring and alerting

## 🤝 Contributing to the Roadmap

We value community input! Here's how you can influence our roadmap:

1. **🗳️ Vote on Features** - Star issues you'd like prioritized
2. **💡 Suggest Ideas** - Open feature request issues
3. **🛠️ Contribute Code** - Submit PRs for roadmap items
4. **🐛 Report Issues** - Help us improve current features
5. **📖 Improve Docs** - Documentation contributions welcome

Join our [Discord Community](https://discord.gg/pipeline-creator) for roadmap discussions!

## 📄 License

MIT License - see the [LICENSE](LICENSE) file for details.

---

**Made with ❤️ by the Pipeline Creator Team**

*Streamlining DevOps, one pipeline at a time.*
