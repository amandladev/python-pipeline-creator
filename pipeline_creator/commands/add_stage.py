"""
Add-stage command for Pipeline Creator CLI

This module handles adding extra build stages like SonarQube, security scanning, etc.
"""

import click
import json
from pathlib import Path
from typing import Dict, Any

from ..utils.console import (
    print_success, print_error, print_info, print_warning, 
    print_step, print_header, confirm
)
from ..templates.stages.extra_stages import AVAILABLE_STAGES, get_stage_template


def check_config_exists() -> bool:
    """Check if pipeline configuration exists"""
    config_path = Path.cwd() / ".pipeline" / "config.json"
    return config_path.exists()


def load_config() -> dict:
    """Load pipeline configuration"""
    config_path = Path.cwd() / ".pipeline" / "config.json"
    with open(config_path, 'r') as f:
        return json.load(f)


def save_config(config: dict) -> bool:
    """Save pipeline configuration"""
    try:
        config_path = Path.cwd() / ".pipeline" / "config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print_error(f"Error saving configuration: {str(e)}")
        return False


def add_stage_to_config(config: dict, stage_name: str, stage_config: dict) -> dict:
    """Add stage configuration to pipeline config"""
    if "extra_stages" not in config:
        config["extra_stages"] = []
    
    # Remove existing stage with same name
    config["extra_stages"] = [s for s in config["extra_stages"] if s.get("name") != stage_name]
    
    # Add new stage
    config["extra_stages"].append(stage_config)
    
    return config


def prompt_for_stage_config(stage_template: dict) -> dict:
    """Prompt user for stage-specific configuration"""
    stage_config = {
        "name": stage_template["name"],
        "enabled": True,
        "phase": stage_template["phase"],
        "config": {}
    }
    
    required_config = stage_template.get("required_config", {})
    
    if required_config:
        print_info(f"📋 Configuration required for {stage_template['display_name']}:")
        
        for key, description in required_config.items():
            value = click.prompt(f"  {description}", type=str)
            stage_config["config"][key] = value
    
    return stage_config


@click.command()
@click.argument('stage_name', required=False)
@click.option('--list', 'list_stages', is_flag=True, help='List available stages')
@click.option('--remove', '-r', help='Remove a stage by name')
@click.option('--show-config', '-s', is_flag=True, help='Show current extra stages configuration')
def add_stage_command(stage_name: str, list_stages: bool, remove: str, show_config: bool):
    """
    Add extra build stages to your pipeline.
    
    Add quality gates, security scanning, and other tools to your CI/CD pipeline.
    
    Examples:
        pipeline add-stage sonarqube     # Add SonarQube Cloud analysis
        pipeline add-stage snyk          # Add Snyk security scanning
        pipeline add-stage --list        # List available stages
        pipeline add-stage --remove snyk # Remove a stage
        pipeline add-stage --show-config # Show current configuration
    """
    print_header("Add Extra Build Stage")
    
    # Check if configuration exists
    if not check_config_exists():
        print_error("❌ No pipeline configuration found!")
        print_info("Run 'pipeline init' first to initialize your pipeline configuration.")
        return
    
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        print_error(f"Error loading configuration: {str(e)}")
        return
    
    # List available stages
    if list_stages:
        print_info("🔧 Available Extra Stages:")
        print_info("")
        
        for name, template in AVAILABLE_STAGES.items():
            phase_emoji = {
                "pre_build": "🚀",
                "build": "🔨", 
                "post_build": "✅"
            }.get(template["phase"], "⚙️")
            
            print_info(f"  {phase_emoji} {name.ljust(12)} - {template['display_name']}")
            print_info(f"     {template['description']}")
            print_info(f"     Phase: {template['phase']}")
            print_info("")
        
        return
    
    # Show current configuration
    if show_config:
        extra_stages = config.get("extra_stages", [])
        
        if not extra_stages:
            print_info("ℹ️ No extra stages configured")
            return
        
        print_info("🔧 Current Extra Stages:")
        print_info("")
        
        for stage in extra_stages:
            status = "✅ Enabled" if stage.get("enabled", True) else "❌ Disabled"
            print_info(f"  • {stage['name']} - {status}")
            print_info(f"    Phase: {stage['phase']}")
            if stage.get("config"):
                print_info(f"    Config: {stage['config']}")
            print_info("")
        
        return
    
    # Remove a stage
    if remove:
        extra_stages = config.get("extra_stages", [])
        original_count = len(extra_stages)
        
        config["extra_stages"] = [s for s in extra_stages if s.get("name") != remove]
        
        if len(config["extra_stages"]) < original_count:
            if save_config(config):
                print_success(f"✅ Removed stage '{remove}' successfully!")
            else:
                print_error("❌ Failed to save configuration")
        else:
            print_warning(f"⚠️ Stage '{remove}' not found")
        
        return
    
    # Add a stage
    if not stage_name:
        print_error("❌ Please specify a stage name")
        print_info("Use 'pipeline add-stage --list' to see available stages")
        return
    
    # Check if stage exists
    if stage_name not in AVAILABLE_STAGES:
        print_error(f"❌ Stage '{stage_name}' not available")
        print_info("Use 'pipeline add-stage --list' to see available stages")
        return
    
    stage_template = get_stage_template(stage_name)
    
    print_info(f"🔧 Adding stage: {stage_template['display_name']}")
    print_info(f"📝 Description: {stage_template['description']}")
    print_info(f"⚙️ Phase: {stage_template['phase']}")
    print_info("")
    
    # Check if stage already exists
    existing_stages = config.get("extra_stages", [])
    existing_names = [s.get("name") for s in existing_stages]
    
    if stage_name in existing_names:
        print_warning(f"⚠️ Stage '{stage_name}' already exists")
        if not confirm("Do you want to replace it?"):
            print_info("Operation cancelled")
            return
    
    # Prompt for configuration
    print_step("Configuring stage...")
    stage_config = prompt_for_stage_config(stage_template)
    
    # Add to configuration
    print_step("Updating pipeline configuration...")
    config = add_stage_to_config(config, stage_name, stage_config)
    
    # Save configuration
    if save_config(config):
        print_success(f"✅ Stage '{stage_name}' added successfully!")
        print_info("")
        print_info("🚀 Next steps:")
        print_info("  1. Run 'pipeline generate' to update CDK files")
        print_info("  2. Run 'pipeline deploy' to apply changes")
        
        # Show environment variables needed
        env_vars = stage_template.get("environment_variables", [])
        if env_vars:
            print_info("")
            print_info("🔐 Required secrets in AWS Secrets Manager:")
            for var in env_vars:
                if var.get("type") == "SECRETS_MANAGER":
                    print_info(f"  • {var['value']} (for {var['name']})")
    else:
        print_error("❌ Failed to add stage")