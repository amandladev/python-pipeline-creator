"""
Configuration utilities for Pipeline Creator
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

from .console import print_error, print_warning


def get_config_path() -> Path:
    """Get the path to the pipeline configuration file"""
    return Path(".pipeline/config.json")


def check_config_exists() -> bool:
    """Check if pipeline configuration exists"""
    return get_config_path().exists()


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load pipeline configuration from JSON file
    
    Args:
        config_path: Optional path to config file, defaults to .pipeline/config.json
    
    Returns:
        Configuration dictionary
    
    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config file is invalid JSON
    """
    if config_path:
        config_file = Path(config_path)
    else:
        config_file = get_config_path()
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in configuration file: {str(e)}", e.doc, e.pos)


def save_config(config: Dict[str, Any], config_path: Optional[str] = None) -> bool:
    """
    Save pipeline configuration to JSON file
    
    Args:
        config: Configuration dictionary to save
        config_path: Optional path to config file, defaults to .pipeline/config.json
    
    Returns:
        True if saved successfully, False otherwise
    """
    if config_path:
        config_file = Path(config_path)
    else:
        config_file = get_config_path()
    
    try:
        # Create directory if it doesn't exist
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save configuration
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print_error(f"Failed to save configuration: {str(e)}")
        return False


def get_config_value(key: str, default: Any = None, config_path: Optional[str] = None) -> Any:
    """
    Get a specific value from configuration
    
    Args:
        key: Configuration key (supports dot notation like 'aws.region')
        default: Default value if key not found
        config_path: Optional path to config file
    
    Returns:
        Configuration value or default
    """
    try:
        config = load_config(config_path)
        
        # Support dot notation for nested keys
        keys = key.split('.')
        value = config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def set_config_value(key: str, value: Any, config_path: Optional[str] = None) -> bool:
    """
    Set a specific value in configuration
    
    Args:
        key: Configuration key (supports dot notation like 'aws.region')
        value: Value to set
        config_path: Optional path to config file
    
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        # Load existing config or create new one
        try:
            config = load_config(config_path)
        except FileNotFoundError:
            config = {}
        
        # Support dot notation for nested keys
        keys = key.split('.')
        current = config
        
        # Navigate to parent of target key
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        
        # Set the final value
        current[keys[-1]] = value
        
        # Save configuration
        return save_config(config, config_path)
    
    except Exception as e:
        print_error(f"Failed to set configuration value: {str(e)}")
        return False


def merge_config(updates: Dict[str, Any], config_path: Optional[str] = None) -> bool:
    """
    Merge updates into existing configuration
    
    Args:
        updates: Dictionary of updates to merge
        config_path: Optional path to config file
    
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        # Load existing config or create new one
        try:
            config = load_config(config_path)
        except FileNotFoundError:
            config = {}
        
        # Deep merge the updates
        config = _deep_merge(config, updates)
        
        # Save configuration
        return save_config(config, config_path)
    
    except Exception as e:
        print_error(f"Failed to merge configuration: {str(e)}")
        return False


def _deep_merge(base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries
    
    Args:
        base: Base dictionary
        updates: Updates to merge into base
    
    Returns:
        Merged dictionary
    """
    result = base.copy()
    
    for key, value in updates.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def backup_config(config_path: Optional[str] = None) -> Optional[str]:
    """
    Create a backup of the current configuration
    
    Args:
        config_path: Optional path to config file
    
    Returns:
        Path to backup file or None if backup failed
    """
    if config_path:
        config_file = Path(config_path)
    else:
        config_file = get_config_path()
    
    if not config_file.exists():
        print_warning("No configuration file to backup")
        return None
    
    try:
        # Create backup filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = config_file.parent / f"config_backup_{timestamp}.json"
        
        # Copy configuration file
        import shutil
        shutil.copy2(config_file, backup_file)
        
        return str(backup_file)
    
    except Exception as e:
        print_error(f"Failed to create backup: {str(e)}")
        return None


def restore_config(backup_path: str, config_path: Optional[str] = None) -> bool:
    """
    Restore configuration from backup
    
    Args:
        backup_path: Path to backup file
        config_path: Optional path to config file to restore to
    
    Returns:
        True if restored successfully, False otherwise
    """
    backup_file = Path(backup_path)
    
    if not backup_file.exists():
        print_error(f"Backup file not found: {backup_path}")
        return False
    
    if config_path:
        config_file = Path(config_path)
    else:
        config_file = get_config_path()
    
    try:
        # Validate backup file is valid JSON
        with open(backup_file, 'r', encoding='utf-8') as f:
            json.load(f)
        
        # Copy backup to config location
        import shutil
        config_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup_file, config_file)
        
        return True
    
    except Exception as e:
        print_error(f"Failed to restore from backup: {str(e)}")
        return False


def validate_config(config: Optional[Dict[str, Any]] = None, config_path: Optional[str] = None) -> Dict[str, list]:
    """
    Validate configuration structure and required fields
    
    Args:
        config: Configuration dictionary to validate (optional)
        config_path: Path to config file to validate (optional)
    
    Returns:
        Dictionary with 'errors' and 'warnings' lists
    """
    errors = []
    warnings = []
    
    try:
        if config is None:
            config = load_config(config_path)
    except FileNotFoundError:
        errors.append("Configuration file not found")
        return {"errors": errors, "warnings": warnings}
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON: {str(e)}")
        return {"errors": errors, "warnings": warnings}
    
    # Required fields
    required_fields = [
        "version",
        "project_name", 
        "aws_region",
        "pipeline"
    ]
    
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")
    
    # Validate specific sections
    if "pipeline" in config:
        pipeline_config = config["pipeline"]
        
        # Required pipeline fields
        required_pipeline_fields = ["build_spec", "artifacts"]
        for field in required_pipeline_fields:
            if field not in pipeline_config:
                errors.append(f"Missing required pipeline field: {field}")
        
        # Validate build_spec
        if "build_spec" in pipeline_config:
            build_spec = pipeline_config["build_spec"]
            required_build_fields = ["commands"]
            
            for field in required_build_fields:
                if field not in build_spec:
                    errors.append(f"Missing required build_spec field: {field}")
            
            # Validate commands structure
            if "commands" in build_spec:
                commands = build_spec["commands"]
                required_phases = ["pre_build", "build", "post_build"]
                
                for phase in required_phases:
                    if phase not in commands:
                        warnings.append(f"Missing build phase: {phase}")
                    elif not isinstance(commands[phase], list):
                        errors.append(f"Build phase {phase} should be a list of commands")
    
    # Validate notifications if present
    if "notifications" in config:
        notifications = config["notifications"]
        
        # Check Slack configuration
        if "slack" in notifications:
            slack_config = notifications["slack"]
            if slack_config.get("enabled", False):
                if not slack_config.get("webhook_url"):
                    warnings.append("Slack enabled but no webhook URL configured")
        
        # Check Email configuration
        if "email" in notifications:
            email_config = notifications["email"]
            if email_config.get("enabled", False):
                required_email_fields = ["smtp_server", "username", "to_emails"]
                for field in required_email_fields:
                    if not email_config.get(field):
                        warnings.append(f"Email enabled but missing: {field}")
    
    return {"errors": errors, "warnings": warnings}