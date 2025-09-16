"""
Generate command for Pipeline Creator CLI

This module handles the generation of CDK infrastructure files.
"""

import click
import json
import os
import re
from pathlib import Path
from typing import Dict, Any

from ..utils.console import (
    print_success, print_error, print_info, print_warning, 
    print_step, print_header
)
from ..utils.aws_utils import check_aws_credentials, get_aws_account_info
from ..templates.cdk_python import (
    CDK_APP_TEMPLATE, PIPELINE_STACK_TEMPLATE, CDK_JSON_TEMPLATE,
    REQUIREMENTS_TEMPLATE, README_TEMPLATE
)
from ..templates.stages.extra_stages import get_stage_template


def check_config_exists() -> bool:
    """Check if pipeline configuration exists"""
    config_path = Path.cwd() / ".pipeline" / "config.json"
    return config_path.exists()


def load_config() -> dict:
    """Load pipeline configuration"""
    config_path = Path.cwd() / ".pipeline" / "config.json"
    with open(config_path, 'r') as f:
        return json.load(f)


def to_snake_case(name: str) -> str:
    """Convert string to snake_case"""
    # Replace hyphens with underscores first
    name = name.replace('-', '_')
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def to_pascal_case(name: str) -> str:
    """Convert string to PascalCase"""
    return ''.join(word.capitalize() for word in re.split(r'[-_\s]+', name))


def process_extra_stages(config: Dict[str, Any]) -> Dict[str, list]:
    """Process extra stages and return commands by phase"""
    stages_by_phase = {
        "pre_build": [],
        "build": [],
        "post_build": []
    }
    
    extra_stages = config.get("extra_stages", [])
    
    for stage_config in extra_stages:
        if not stage_config.get("enabled", True):
            continue
            
        stage_name = stage_config.get("name")
        stage_template = get_stage_template(stage_name)
        
        if not stage_template:
            continue
            
        phase = stage_config.get("phase", stage_template.get("phase", "build"))
        commands = stage_template.get("commands", [])
        
        # Replace placeholders in commands with actual config values
        stage_specific_config = stage_config.get("config", {})
        processed_commands = []
        
        for command in commands:
            processed_command = command
            for key, value in stage_specific_config.items():
                processed_command = processed_command.replace(f"{{{key}}}", str(value))
            processed_commands.append(processed_command)
        
        # Add stage commands to the appropriate phase
        if phase in stages_by_phase:
            stages_by_phase[phase].extend([
                f"# {stage_template.get('display_name', stage_name)} Stage"
            ] + processed_commands + [""])
    
    return stages_by_phase


def get_environment_variables(config: Dict[str, Any]) -> list:
    """Get environment variables for all extra stages"""
    env_vars = []
    extra_stages = config.get("extra_stages", [])
    
    for stage_config in extra_stages:
        if not stage_config.get("enabled", True):
            continue
            
        stage_name = stage_config.get("name")
        stage_template = get_stage_template(stage_name)
        
        if not stage_template:
            continue
            
        stage_env_vars = stage_template.get("environment_variables", [])
        env_vars.extend(stage_env_vars)
    
    return env_vars


def detect_repository_info(config: Dict[str, Any]) -> tuple[str, str]:
    """
    Detect repository owner and name from git or config
    """
    project_name = config.get('project_name', 'my-project')
    
    # Try to get from git remote
    try:
        import subprocess
        result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            url = result.stdout.strip()
            if 'github.com' in url:
                # Extract owner/repo from GitHub URL
                if url.startswith('git@github.com:'):
                    path = url.replace('git@github.com:', '').replace('.git', '')
                elif 'github.com/' in url:
                    path = url.split('github.com/')[-1].replace('.git', '')
                else:
                    return "your-username", project_name
                
                parts = path.split('/')
                if len(parts) >= 2:
                    return parts[0], parts[1]
    except Exception:
        pass
    
    return "your-username", project_name


def create_cdk_files(config: Dict[str, Any], output_dir: Path, language: str = 'python') -> bool:
    """Create CDK files based on configuration"""
    
    try:
        print_step("Creating CDK directory structure...")
        
        # Create directories
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / to_snake_case(config['project_name'])).mkdir(exist_ok=True)
        
        # Get repository information
        repo_owner, repo_name = detect_repository_info(config)
        
        # Convert project name for different cases
        project_name_snake = to_snake_case(config['project_name'])
        project_name_pascal = to_pascal_case(config['project_name'])
        
        # Process extra stages
        print_step("Processing extra stages...")
        extra_stage_commands = process_extra_stages(config)
        env_vars = get_environment_variables(config)
        
        # Combine original commands with extra stage commands
        pre_build_commands = (config['pipeline']['build_spec']['commands']['pre_build'] + 
                             extra_stage_commands['pre_build'])
        build_commands = (config['pipeline']['build_spec']['commands']['build'] + 
                         extra_stage_commands['build'])
        post_build_commands = (config['pipeline']['build_spec']['commands']['post_build'] + 
                              extra_stage_commands['post_build'])
        
        # Prepare template variables
        template_vars = {
            'project_name': config['project_name'],
            'project_name_snake': project_name_snake,
            'project_name_pascal': project_name_pascal,
            'aws_region': config['aws_region'],
            'environment': config['environment'],
            'repo_owner': repo_owner,
            'repo_name': repo_name,
            'pre_build_commands': json.dumps(pre_build_commands),
            'build_commands': json.dumps(build_commands),
            'post_build_commands': json.dumps(post_build_commands),
            'artifact_files': json.dumps(config['pipeline']['artifacts']['files']),
            'environment_variables': json.dumps(env_vars)
        }
        
        if language == 'python':
            print_step("Generating Python CDK files...")
            
            # Create app.py
            app_content = CDK_APP_TEMPLATE.format(**template_vars)
            (output_dir / "app.py").write_text(app_content)
            
            # Create pipeline stack
            stack_content = PIPELINE_STACK_TEMPLATE.format(**template_vars)
            stack_dir = output_dir / project_name_snake
            (stack_dir / "__init__.py").write_text("")
            (stack_dir / "pipeline_stack.py").write_text(stack_content)
            
            # Create cdk.json
            cdk_json_content = CDK_JSON_TEMPLATE
            (output_dir / "cdk.json").write_text(cdk_json_content)
            
            # Create requirements.txt
            (output_dir / "requirements.txt").write_text(REQUIREMENTS_TEMPLATE)
            
            # Create README.md
            readme_content = README_TEMPLATE.format(**template_vars)
            (output_dir / "README.md").write_text(readme_content)
            
            print_success(f"Generated Python CDK files in {output_dir}")
            return True
        else:
            print_error(f"Language '{language}' is not supported yet")
            return False
            
    except Exception as e:
        print_error(f"Error creating CDK files: {str(e)}")
        return False


@click.command()
@click.option('--output-dir', '-o', default='./cdk', help='Output directory for CDK files')
@click.option('--language', '-l', default='python', 
              type=click.Choice(['python', 'typescript', 'java', 'csharp']),
              help='CDK language')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing files')
def generate_command(output_dir: str, language: str, force: bool):
    """
    Generate AWS CDK infrastructure files for your pipeline.
    
    This command creates the necessary CDK code and configuration files
    to deploy your CI/CD pipeline to AWS.
    
    Examples:
        pipeline generate                    # Generate Python CDK files
        pipeline generate -l typescript     # Generate TypeScript CDK files  
        pipeline generate -o ./infra        # Custom output directory
        pipeline generate --force           # Overwrite existing files
    """
    print_header("Generate CDK Infrastructure")
    
    # Check if configuration exists
    if not check_config_exists():
        print_error("❌ No pipeline configuration found!")
        print_info("Run 'pipeline init' first to initialize your pipeline configuration.")
        return
    
    # Load configuration
    print_step("Loading configuration...")
    try:
        config = load_config()
        print_info(f"📦 Project: {config['project_name']}")
        print_info(f"🔧 Language: {language}")
        print_info(f"📁 Output: {output_dir}")
    except Exception as e:
        print_error(f"Error loading configuration: {str(e)}")
        return
    
    # Check if output directory exists
    output_path = Path(output_dir)
    if output_path.exists() and not force:
        if output_path.is_dir() and any(output_path.iterdir()):
            print_error(f"❌ Directory {output_dir} already exists and is not empty!")
            print_info("Use --force to overwrite existing files, or choose a different output directory.")
            return
    
    # Validate AWS credentials (optional warning)
    print_step("Checking AWS credentials...")
    if not check_aws_credentials():
        print_warning("⚠️ AWS credentials not found!")
        print_info("You'll need to configure AWS credentials before deploying.")
        print_info("Run: aws configure")
    else:
        account_info = get_aws_account_info()
        if account_info:
            print_info(f"🔐 AWS Account: {account_info['account_id']}")
    
    # Generate CDK files
    print_step("Analyzing configuration...")
    print_step("Planning infrastructure resources...")
    
    if create_cdk_files(config, output_path, language):
        print_success("✅ CDK infrastructure files generated successfully!")
        
        print_info("")
        print_info("📋 Generated files:")
        print_info(f"  • {output_dir}/app.py - CDK application entry point")
        print_info(f"  • {output_dir}/{to_snake_case(config['project_name'])}/pipeline_stack.py - Pipeline stack definition")
        print_info(f"  • {output_dir}/cdk.json - CDK configuration")
        print_info(f"  • {output_dir}/requirements.txt - Python dependencies")
        print_info(f"  • {output_dir}/README.md - Setup instructions")
        
        print_info("")
        print_info("🚀 Next steps:")
        print_info("  1. cd cdk")
        print_info("  2. python -m venv .venv && source .venv/bin/activate")
        print_info("  3. pip install -r requirements.txt")
        print_info("  4. cdk bootstrap  (if not done before)")
        print_info("  5. pipeline deploy")
        
    else:
        print_error("❌ Failed to generate CDK infrastructure files")
        return
        print_error("No pipeline configuration found!")
        print_info("Run 'pipeline init' first to initialize the configuration.")
        return
    
    print_step("Loading configuration...")
    config = load_config()
    project_name = config.get('project_name', 'my-pipeline')
    
    print_info(f"📦 Project: {project_name}")
    print_info(f"🔧 Language: {language}")
    print_info(f"📁 Output: {output_dir}")
    
    # For MVP, just show what would be generated
    print_step("Analyzing configuration...")
    print_step("Planning infrastructure resources...")
    
    print_warning("🚧 CDK generation is coming soon!")
    print_info("This command will generate:")
    print_info("  • CDK app with pipeline stack")
    print_info("  • CodePipeline configuration")
    print_info("  • CodeBuild project")  
    print_info("  • IAM roles and policies")
    print_info("  • S3 bucket for artifacts")
    
    print_info("\nFor now, you can manually set up CDK with:")
    print_info(f"  1. cdk init app --language {language}")
    print_info("  2. Add pipeline resources to your stack")
    print_info("  3. Run 'cdk deploy'")
    
    print_success("Infrastructure planning completed!")
    print_info("Full CDK generation will be available in the next version.")