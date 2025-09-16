"""
Status command for Pipeline Creator CLI

This module handles checking the status of the deployed pipeline.
"""

import click
import json
from pathlib import Path
from datetime import datetime

from ..utils.console import (
    print_success, print_error, print_info, print_warning, 
    print_step, print_header
)


def check_config_exists() -> bool:
    """Check if pipeline configuration exists"""
    config_path = Path.cwd() / ".pipeline" / "config.json"
    return config_path.exists()


def load_config() -> dict:
    """Load pipeline configuration"""
    config_path = Path.cwd() / ".pipeline" / "config.json"
    with open(config_path, 'r') as f:
        return json.load(f)


@click.command()
@click.option('--detailed', '-d', is_flag=True, help='Show detailed status information')
@click.option('--refresh', '-r', is_flag=True, help='Refresh status from AWS')
def status_command(detailed: bool, refresh: bool):
    """
    Show the current status of your CI/CD pipeline.
    
    This command displays information about your pipeline deployment,
    recent builds, and overall health status.
    
    Examples:
        pipeline status           # Show basic status
        pipeline status -d        # Show detailed status
        pipeline status -r        # Refresh from AWS
    """
    print_header("Pipeline Status")
    
    # Check if configuration exists
    if not check_config_exists():
        print_error("No pipeline configuration found!")
        print_info("Run 'pipeline init' first to initialize the configuration.")
        return
    
    print_step("Loading configuration...")
    config = load_config()
    
    project_name = config.get('project_name', 'my-pipeline')
    environment = config.get('environment', 'dev')
    region = config.get('aws_region', 'us-east-1')
    
    print_info(f"📦 Project: {project_name}")
    print_info(f"🌍 Environment: {environment}")
    print_info(f"🗺️ Region: {region}")
    
    if refresh:
        print_step("Refreshing status from AWS...")
    else:
        print_step("Checking pipeline status...")
    
    # For MVP, show mock status information
    print_warning("🚧 Status checking is coming soon!")
    
    print_info("\nPipeline Overview:")
    print_info("  📊 Status: Not Deployed")
    print_info("  📅 Last Updated: N/A")
    print_info("  🔧 Configuration: Ready")
    
    if detailed:
        print_info("\nDetailed Information:")
        print_info("  • Pipeline: Not created yet")
        print_info("  • CodeBuild: Not configured")
        print_info("  • S3 Artifacts: Not created")
        print_info("  • IAM Roles: Not created")
        print_info("  • CloudWatch: Not configured")
        
        print_info("\nRecent Activity:")
        print_info("  • No deployments yet")
        print_info("  • No builds executed")
    
    print_info("\nThis command will show:")
    print_info("  • Pipeline deployment status")
    print_info("  • Recent build history")
    print_info("  • Resource health checks")
    print_info("  • Error notifications")
    
    print_success("Status check completed!")
    print_info("Full status monitoring will be available after deployment.")