"""
Init command for Pipeline Creator CLI

This module handles the initialization of pipeline configuration.
Creates the .pipeline directory and config.json with default settings.
"""

import click
import json
import os
from pathlib import Path
from typing import Dict, Any

from ..utils.console import (
    print_success, print_error, print_info, print_warning, 
    print_step, print_header, confirm
)


def get_default_config() -> Dict[str, Any]:
    """
    Get default configuration for pipeline
    
    Returns:
        Default configuration dictionary
    """
    return {
        "version": "1.0",
        "project_name": "",
        "aws_region": "us-east-1",
        "environment": "dev",
        "pipeline": {
            "type": "basic",
            "build_spec": {
                "runtime": "python",
                "version": "3.9",
                "commands": {
                    "pre_build": [
                        "echo Logging in to Amazon ECR...",
                        "pip install -r requirements.txt"
                    ],
                    "build": [
                        "echo Build started on `date`",
                        "echo Running tests...",
                        "python -m pytest",
                        "echo Build completed on `date`"
                    ],
                    "post_build": [
                        "echo Build completed successfully"
                    ]
                }
            },
            "artifacts": {
                "files": ["**/*"]
            }
        },
        "deployment": {
            "strategy": "rolling",
            "auto_rollback": True
        },
        "notifications": {
            "slack": {
                "enabled": False,
                "webhook_url": ""
            },
            "email": {
                "enabled": False,
                "addresses": []
            }
        }
    }


def validate_project_directory() -> bool:
    """
    Validate that current directory is suitable for pipeline initialization
    
    Returns:
        True if valid, False otherwise
    """
    current_dir = Path.cwd()
    
    # Check if it looks like a project directory
    common_files = [
        "package.json", "requirements.txt", "Dockerfile", 
        "README.md", ".git", "src", "app"
    ]
    
    has_project_files = any((current_dir / file).exists() for file in common_files)
    
    if not has_project_files:
        print_warning("This doesn't appear to be a project directory.")
        print_info("Consider running this command in your project root directory.")
        return confirm("Continue anyway?", default=False)
    
    return True


def detect_project_type() -> str:
    """
    Try to detect the project type based on files present
    
    Returns:
        Detected project type
    """
    current_dir = Path.cwd()
    
    if (current_dir / "package.json").exists():
        return "node"
    elif (current_dir / "requirements.txt").exists() or (current_dir / "setup.py").exists():
        return "python"
    elif (current_dir / "go.mod").exists():
        return "go"
    elif (current_dir / "pom.xml").exists():
        return "java"
    elif (current_dir / "Dockerfile").exists():
        return "docker"
    else:
        return "generic"


def create_pipeline_directory() -> Path:
    """
    Create .pipeline directory if it doesn't exist
    
    Returns:
        Path to .pipeline directory
    """
    pipeline_dir = Path.cwd() / ".pipeline"
    pipeline_dir.mkdir(exist_ok=True)
    return pipeline_dir


def save_config(config: Dict[str, Any], config_path: Path) -> None:
    """
    Save configuration to JSON file
    
    Args:
        config: Configuration dictionary
        config_path: Path to save configuration
    """
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


@click.command()
@click.option('--project-name', '-n', help='Name of the project')
@click.option('--region', '-r', default='us-east-1', help='AWS region')
@click.option('--environment', '-e', default='dev', help='Environment (dev, staging, prod)')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing configuration')
def init_command(project_name: str, region: str, environment: str, force: bool):
    """
    Initialize pipeline configuration in the current directory.
    
    This command creates a .pipeline directory with a config.json file
    containing the basic configuration needed for your CI/CD pipeline.
    
    Examples:
        pipeline init                           # Interactive initialization
        pipeline init -n myapp -r us-west-2    # With project name and region
        pipeline init --force                  # Overwrite existing config
    """
    print_header("Pipeline Initialization")
    
    # Validate current directory
    if not validate_project_directory():
        print_error("Initialization cancelled.")
        return
    
    # Check if .pipeline directory already exists
    pipeline_dir = Path.cwd() / ".pipeline"
    config_path = pipeline_dir / "config.json"
    
    if config_path.exists() and not force:
        print_warning("Pipeline configuration already exists!")
        print_info(f"Found existing config at: {config_path}")
        if not confirm("Do you want to overwrite it?", default=False):
            print_info("Use --force flag to overwrite without confirmation.")
            return
    
    print_step("Setting up pipeline configuration...")
    
    # Get default configuration
    config = get_default_config()
    
    # Detect project type
    detected_type = detect_project_type()
    print_info(f"Detected project type: {detected_type}")
    
    # Get project name
    if not project_name:
        current_dir_name = Path.cwd().name
        project_name = click.prompt(
            "Project name", 
            default=current_dir_name,
            type=str
        )
    
    # Update configuration with user inputs
    config["project_name"] = project_name
    config["aws_region"] = region
    config["environment"] = environment
    config["pipeline"]["detected_type"] = detected_type
    
    print_step("Creating pipeline directory...")
    create_pipeline_directory()
    
    print_step("Saving configuration...")
    save_config(config, config_path)
    
    # Create .gitignore entry if needed
    gitignore_path = Path.cwd() / ".gitignore"
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            gitignore_content = f.read()
        
        if ".pipeline/" not in gitignore_content:
            print_step("Adding .pipeline/ to .gitignore...")
            with open(gitignore_path, 'a') as f:
                f.write("\n# Pipeline Creator\n.pipeline/\n")
    
    print_success("Pipeline configuration initialized successfully!")
    print_info(f"📁 Configuration saved to: {config_path}")
    print_info(f"🎯 Project: {project_name}")
    print_info(f"🌍 Region: {region}")
    print_info(f"🔧 Environment: {environment}")
    
    print("\nNext steps:")
    print_info("1. Review and customize .pipeline/config.json")
    print_info("2. Run 'pipeline generate' to create CDK infrastructure")
    print_info("3. Run 'pipeline deploy' to deploy your pipeline")