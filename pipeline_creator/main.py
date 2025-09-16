#!/usr/bin/env python3
"""
Main CLI module for Pipeline Creator

This module defines the main command group and all subcommands for the Pipeline Creator CLI.
"""

import click
import sys
import os
from rich.console import Console
from rich.text import Text

from .utils.console import print_success, print_error, print_info, print_warning
from .commands.init import init_command
from .commands.generate import generate_command
from .commands.deploy import deploy_command
from .commands.status import status_command
from .commands.logs import logs_command
from .commands.add_stage import add_stage_command
from .commands.notifications import notifications_command
from .commands.templates import templates

console = Console()

# Context settings for better help formatting
CONTEXT_SETTINGS = {'help_option_names': ['-h', '--help']}


@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True)
@click.version_option(version='0.1.0', prog_name='pipeline')
@click.pass_context
def cli(ctx):
    """
    🚀 Pipeline Creator CLI - Create and manage CI/CD pipelines on AWS
    
    A modern CLI tool that helps developers set up and deploy CI/CD pipelines 
    in AWS quickly and easily.
    
    Examples:
        pipeline init              # Initialize pipeline configuration
        pipeline generate          # Generate CDK infrastructure files  
        pipeline deploy            # Deploy the pipeline
        pipeline status            # Check pipeline status
        pipeline logs              # View deployment logs
    """
    if ctx.invoked_subcommand is None:
        # Show welcome message when no command is provided
        welcome_text = Text()
        welcome_text.append("🚀 ", style="bold cyan")
        welcome_text.append("Pipeline Creator CLI", style="bold white")
        welcome_text.append(" v0.1.0", style="dim white")
        
        console.print("\n")
        console.print(welcome_text)
        console.print("A modern tool for creating CI/CD pipelines on AWS\n", style="dim")
        
        # Show basic usage
        print_info("Usage: pipeline [OPTIONS] COMMAND [ARGS]...")
        print_info("Try 'pipeline --help' for more information.")
        console.print()


# Register all commands
cli.add_command(init_command, name="init")
cli.add_command(generate_command, name="generate")
cli.add_command(deploy_command, name="deploy")
cli.add_command(status_command, name="status")
cli.add_command(logs_command, name="logs")
cli.add_command(add_stage_command, name="add-stage")
cli.add_command(notifications_command, name="notifications")
cli.add_command(templates, name="templates")
def main():
    """Entry point for the CLI"""
    try:
        cli()
    except KeyboardInterrupt:
        print_warning("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()