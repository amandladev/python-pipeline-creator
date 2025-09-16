"""
Extra Build Stages Templates for Pipeline Creator

This module contains templates for additional build stages like SonarQube, security scanning, etc.
"""

# SonarQube Cloud stage
SONARQUBE_STAGE = {
    "name": "sonarqube",
    "display_name": "SonarQube Cloud Analysis",
    "description": "Code quality and security analysis with SonarQube Cloud",
    "phase": "post_build",
    "environment_variables": [
        {
            "name": "SONAR_TOKEN",
            "type": "SECRETS_MANAGER",
            "value": "sonarqube-token"
        }
    ],
    "commands": [
        "echo Installing SonarQube Scanner...",
        "pip install sonar-scanner",
        "echo Running SonarQube analysis...",
        "sonar-scanner -Dsonar.projectKey={project_key} -Dsonar.organization={organization} -Dsonar.host.url=https://sonarcloud.io -Dsonar.login=$SONAR_TOKEN",
        "echo SonarQube analysis completed"
    ],
    "required_config": {
        "project_key": "SonarQube project key",
        "organization": "SonarQube organization"
    }
}

# Snyk Security Scanning
SNYK_STAGE = {
    "name": "snyk",
    "display_name": "Snyk Security Scan", 
    "description": "Security vulnerability scanning with Snyk",
    "phase": "post_build",
    "environment_variables": [
        {
            "name": "SNYK_TOKEN",
            "type": "SECRETS_MANAGER",
            "value": "snyk-token"
        }
    ],
    "commands": [
        "echo Installing Snyk CLI...",
        "npm install -g snyk",
        "echo Authenticating with Snyk...",
        "snyk auth $SNYK_TOKEN",
        "echo Running security scan...",
        "snyk test --severity-threshold=high",
        "snyk monitor",
        "echo Security scan completed"
    ],
    "required_config": {}
}

# Code Coverage with Codecov
CODECOV_STAGE = {
    "name": "codecov",
    "display_name": "Codecov Coverage Upload",
    "description": "Upload test coverage to Codecov",
    "phase": "post_build", 
    "environment_variables": [
        {
            "name": "CODECOV_TOKEN",
            "type": "SECRETS_MANAGER", 
            "value": "codecov-token"
        }
    ],
    "commands": [
        "echo Installing coverage tools...",
        "pip install pytest-cov codecov",
        "echo Running tests with coverage...",
        "python -m pytest --cov=. --cov-report=xml",
        "echo Uploading coverage to Codecov...",
        "codecov -t $CODECOV_TOKEN",
        "echo Coverage upload completed"
    ],
    "required_config": {}
}

# Docker Build and Push
DOCKER_STAGE = {
    "name": "docker", 
    "display_name": "Docker Build & Push",
    "description": "Build and push Docker images to ECR",
    "phase": "post_build",
    "environment_variables": [],
    "commands": [
        "echo Logging in to Amazon ECR...",
        "aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY_URI",
        "echo Build started on `date`",
        "echo Building the Docker image...",
        "docker build -t $IMAGE_REPO_NAME:$IMAGE_TAG .",
        "docker tag $IMAGE_REPO_NAME:$IMAGE_TAG $ECR_REPOSITORY_URI:$IMAGE_TAG",
        "echo Pushing the Docker image...",
        "docker push $ECR_REPOSITORY_URI:$IMAGE_TAG",
        "echo Docker build and push completed on `date`"
    ],
    "required_config": {
        "ecr_repository": "ECR repository name"
    }
}

# ESLint for JavaScript/TypeScript projects
ESLINT_STAGE = {
    "name": "eslint",
    "display_name": "ESLint Code Quality",
    "description": "JavaScript/TypeScript code quality with ESLint",
    "phase": "build",
    "environment_variables": [],
    "commands": [
        "echo Installing ESLint...",
        "npm install -g eslint",
        "echo Running ESLint...",
        "eslint . --ext .js,.jsx,.ts,.tsx --format json --output-file eslint-report.json || true",
        "echo ESLint analysis completed"
    ],
    "required_config": {}
}

# Bandit Security Linter for Python
BANDIT_STAGE = {
    "name": "bandit",
    "display_name": "Bandit Security Linter",
    "description": "Python security linter with Bandit",
    "phase": "build",
    "environment_variables": [],
    "commands": [
        "echo Installing Bandit...",
        "pip install bandit",
        "echo Running security analysis...",
        "bandit -r . -f json -o bandit-report.json || true",
        "echo Security analysis completed"
    ],
    "required_config": {}
}

# Custom stage template
CUSTOM_STAGE = {
    "name": "custom",
    "display_name": "Custom Stage",
    "description": "Custom build stage with user-defined commands", 
    "phase": "build",  # Can be pre_build, build, or post_build
    "environment_variables": [],
    "commands": [
        "echo Running custom commands...",
        "# Add your custom commands here"
    ],
    "required_config": {
        "commands": "List of custom commands to run"
    }
}

# Available stages registry
AVAILABLE_STAGES = {
    "sonarqube": SONARQUBE_STAGE,
    "snyk": SNYK_STAGE, 
    "codecov": CODECOV_STAGE,
    "docker": DOCKER_STAGE,
    "eslint": ESLINT_STAGE,
    "bandit": BANDIT_STAGE,
    "custom": CUSTOM_STAGE
}

def get_stage_template(stage_name: str) -> dict:
    """Get stage template by name"""
    return AVAILABLE_STAGES.get(stage_name, {})

def list_available_stages() -> list:
    """List all available stage names"""
    return list(AVAILABLE_STAGES.keys())

def get_stages_by_phase(phase: str) -> list:
    """Get stages that run in a specific phase"""
    return [
        name for name, config in AVAILABLE_STAGES.items() 
        if config.get("phase") == phase
    ]