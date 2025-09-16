"""
Utility functions for console output and formatting

This module provides colorized console output functions using rich library
for better user experience.
"""

from rich.console import Console
from rich.text import Text
from rich import print as rich_print
import sys

console = Console()


def print_success(message: str) -> None:
    """Print a success message in green"""
    text = Text()
    text.append("✅ ", style="bold green")
    text.append(str(message), style="green")
    console.print(text)


def print_error(message: str) -> None:
    """Print an error message in red"""
    text = Text()
    text.append("❌ ", style="bold red")
    text.append(str(message), style="red")
    console.print(text)


def print_warning(message: str) -> None:
    """Print a warning message in yellow"""
    text = Text()
    text.append("⚠️ ", style="bold yellow")
    text.append(str(message), style="yellow")
    console.print(text)


def print_info(message: str) -> None:
    """Print an info message in blue"""
    text = Text()
    text.append("ℹ️ ", style="bold blue")
    text.append(str(message), style="blue")
    console.print(text)


def print_step(message: str, step_num: int = None) -> None:
    """Print a step message with optional numbering"""
    text = Text()
    if step_num:
        text.append(f"{step_num}. ", style="bold cyan")
    text.append("🔄 ", style="bold cyan")
    text.append(str(message), style="cyan")
    console.print(text)


def print_header(title: str) -> None:
    """Print a header with decorative formatting"""
    console.print()
    console.rule(f"[bold cyan]{title}[/bold cyan]")
    console.print()


def print_json(data: dict) -> None:
    """Pretty print JSON data"""
    rich_print(data)


def confirm(message: str, default: bool = False) -> bool:
    """
    Ask user for confirmation
    
    Args:
        message: The confirmation message
        default: Default value if user just presses Enter
        
    Returns:
        True if user confirms, False otherwise
    """
    suffix = " [Y/n]" if default else " [y/N]"
    text = Text()
    text.append("❓ ", style="bold yellow")
    text.append(message + suffix, style="yellow")
    
    console.print(text, end="")
    
    try:
        choice = input(" ").lower().strip()
        if choice == '':
            return default
        elif choice in ['y', 'yes']:
            return True
        elif choice in ['n', 'no']:
            return False
        else:
            print_warning("Please enter 'y' or 'n'")
            return confirm(message, default)
    except KeyboardInterrupt:
        print_warning("\nOperation cancelled")
        return False