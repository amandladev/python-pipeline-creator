"""
File utility functions for Pipeline Creator CLI

This module provides utility functions for file operations and validations.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


def ensure_directory(path: Path) -> None:
    """
    Ensure directory exists, create if it doesn't
    
    Args:
        path: Directory path to ensure exists
    """
    path.mkdir(parents=True, exist_ok=True)


def read_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Read and parse JSON file
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Parsed JSON data or None if file doesn't exist or is invalid
    """
    try:
        if not file_path.exists():
            return None
            
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def write_json_file(file_path: Path, data: Dict[str, Any], indent: int = 2) -> bool:
    """
    Write data to JSON file
    
    Args:
        file_path: Path to write JSON file
        data: Data to write
        indent: JSON indentation level
        
    Returns:
        True if successful, False otherwise
    """
    try:
        ensure_directory(file_path.parent)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return True
    except IOError:
        return False


def is_git_repository() -> bool:
    """
    Check if current directory is a git repository
    
    Returns:
        True if git repository, False otherwise
    """
    return (Path.cwd() / ".git").exists()


def get_git_remote_url() -> Optional[str]:
    """
    Get git remote URL if available
    
    Returns:
        Git remote URL or None
    """
    try:
        import subprocess
        result = subprocess.run(
            ['git', 'config', '--get', 'remote.origin.url'],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return None


def find_project_files() -> Dict[str, bool]:
    """
    Find common project files in current directory
    
    Returns:
        Dictionary of file existence status
    """
    current_dir = Path.cwd()
    files_to_check = {
        'package.json': (current_dir / 'package.json').exists(),
        'requirements.txt': (current_dir / 'requirements.txt').exists(),
        'setup.py': (current_dir / 'setup.py').exists(),
        'Dockerfile': (current_dir / 'Dockerfile').exists(),
        'docker-compose.yml': (current_dir / 'docker-compose.yml').exists(),
        'go.mod': (current_dir / 'go.mod').exists(),
        'pom.xml': (current_dir / 'pom.xml').exists(),
        'README.md': (current_dir / 'README.md').exists(),
        '.gitignore': (current_dir / '.gitignore').exists(),
    }
    return files_to_check


def validate_project_name(name: str) -> bool:
    """
    Validate project name format
    
    Args:
        name: Project name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not name:
        return False
    
    # Allow alphanumeric, hyphens, underscores
    # Must start with letter or number
    import re
    pattern = r'^[a-zA-Z0-9][a-zA-Z0-9_-]*$'
    return re.match(pattern, name) is not None


def get_file_size_human(file_path: Path) -> str:
    """
    Get human-readable file size
    
    Args:
        file_path: Path to file
        
    Returns:
        Human-readable file size string
    """
    try:
        size = file_path.stat().st_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    except OSError:
        return "Unknown"