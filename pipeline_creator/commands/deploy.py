"""
Deploy command for Pipeline Creator CLI

This module handles the deployment of the CI/CD pipeline to AWS.
"""

import click
import json
import subprocess
import os
from pathlib import Path

from ..utils.console import (
    print_success, print_error, print_info, print_warning, 
    print_step, print_header, confirm
)
from ..utils.aws_utils import (
    check_aws_credentials, get_aws_account_info, check_cdk_installed,
    get_cdk_version, check_cdk_bootstrap, bootstrap_cdk
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


def check_cdk_files_exist(cdk_dir: Path) -> bool:
    """Check if CDK files exist"""
    required_files = ['app.py', 'cdk.json']
    return all((cdk_dir / file).exists() for file in required_files)


def run_cdk_command(command: list[str], cwd: Path, timeout: int = 600) -> tuple[bool, str]:
    """
    Run CDK command and return success status and output
    
    Args:
        command: CDK command as list of strings
        cwd: Working directory
        timeout: Command timeout in seconds
        
    Returns:
        Tuple of (success, output/error_message)
    """
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr or result.stdout
            
    except subprocess.TimeoutExpired:
        return False, f"Command timed out after {timeout} seconds"
    except Exception as e:
        return False, f"Error running command: {str(e)}"


def install_cdk_dependencies(cdk_dir: Path) -> bool:
    """Install CDK Python dependencies"""
    try:
        print_step("Installing CDK dependencies...")
        
        # Check if virtual environment exists
        venv_path = cdk_dir / ".venv"
        if not venv_path.exists():
            print_info("Creating Python virtual environment...")
            result = subprocess.run([
                "python", "-m", "venv", str(venv_path)
            ], cwd=cdk_dir, capture_output=True, text=True)
            
            if result.returncode != 0:
                print_error(f"Failed to create virtual environment: {result.stderr}")
                return False
        
        # Determine pip path
        if os.name == 'nt':  # Windows
            pip_path = venv_path / "Scripts" / "pip"
        else:  # Unix/Linux/macOS
            pip_path = venv_path / "bin" / "pip"
        
        # Install dependencies
        print_step("Installing Python packages...")
        result = subprocess.run([
            str(pip_path), "install", "-r", "requirements.txt"
        ], cwd=cdk_dir, capture_output=True, text=True, timeout=180)
        
        if result.returncode == 0:
            print_success("Dependencies installed successfully")
            return True
        else:
            print_error(f"Failed to install dependencies: {result.stderr}")
            return False
            
    except Exception as e:
        print_error(f"Error installing dependencies: {str(e)}")
        return False


@click.command()
@click.option('--environment', '-e', help='Environment to deploy to (overrides config)')
@click.option('--region', '-r', help='AWS region (overrides config)')
@click.option('--auto-approve', '-y', is_flag=True, help='Skip confirmation prompts')
@click.option('--cdk-dir', default='./cdk', help='CDK directory path')
def deploy_command(environment: str, region: str, auto_approve: bool, cdk_dir: str):
    """
    Deploy the CI/CD pipeline to AWS using CDK.
    
    This command deploys your pipeline infrastructure to AWS and sets up
    the complete CI/CD workflow for your project.
    
    Examples:
        pipeline deploy                    # Deploy with default settings
        pipeline deploy -e prod            # Deploy to production environment
        pipeline deploy -r us-west-2       # Deploy to specific region
        pipeline deploy -y                 # Skip confirmation prompts
    """
    print_header("Deploy Pipeline to AWS")
    
    # Check if configuration exists
    if not check_config_exists():
        print_error("❌ No pipeline configuration found!")
        print_info("Run 'pipeline init' first to initialize your pipeline configuration.")
        return
    
    # Load configuration
    print_step("Loading configuration...")
    try:
        config = load_config()
        
        # Override config values if provided
        deploy_env = environment or config['environment']
        deploy_region = region or config['aws_region']
        
        print_info(f"📦 Project: {config['project_name']}")
        print_info(f"🌍 Environment: {deploy_env}")
        print_info(f"🗺️ Region: {deploy_region}")
    except Exception as e:
        print_error(f"Error loading configuration: {str(e)}")
        return
    
    # Check AWS credentials
    print_step("Validating AWS credentials...")
    if not check_aws_credentials():
        print_error("❌ AWS credentials not configured!")
        print_info("Please configure your AWS credentials:")
        print_info("  1. aws configure")
        print_info("  2. Or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
        return
    
    account_info = get_aws_account_info()
    if account_info:
        print_success(f"✅ AWS Account: {account_info['account_id']}")
    
    # Check CDK CLI
    print_step("Checking CDK installation...")
    if not check_cdk_installed():
        print_error("❌ AWS CDK CLI is not installed!")
        print_info("Please install CDK CLI:")
        print_info("  npm install -g aws-cdk")
        return
    
    cdk_version = get_cdk_version()
    if cdk_version:
        print_success(f"✅ CDK CLI: {cdk_version}")
    
    # Check CDK files
    cdk_path = Path(cdk_dir)
    print_step("Checking CDK files...")
    if not cdk_path.exists():
        print_error(f"❌ CDK directory '{cdk_dir}' not found!")
        print_info("Run 'pipeline generate' first to create CDK infrastructure files.")
        return
    
    if not check_cdk_files_exist(cdk_path):
        print_error("❌ CDK files not found!")
        print_info("Run 'pipeline generate' to create the necessary CDK files.")
        return
    
    print_success("✅ CDK files found")
    
    # Install dependencies
    if not install_cdk_dependencies(cdk_path):
        print_error("❌ Failed to install CDK dependencies")
        return
    
    # Check CDK bootstrap status
    print_step("Checking CDK bootstrap status...")
    is_bootstrapped, bootstrap_error = check_cdk_bootstrap(deploy_region)
    
    if not is_bootstrapped:
        print_warning(f"⚠️ CDK not bootstrapped in region {deploy_region}")
        print_info(bootstrap_error or "CDK bootstrap is required for deployment")
        
        if not auto_approve:
            if not confirm("Do you want to bootstrap CDK now?"):
                print_info("Deployment cancelled. Please bootstrap CDK manually:")
                print_info(f"  cdk bootstrap aws://unknown-account/{deploy_region}")
                return
        
        print_step("Bootstrapping CDK...")
        success, error = bootstrap_cdk(deploy_region)
        if not success:
            print_error(f"❌ CDK bootstrap failed: {error}")
            return
        
        print_success("✅ CDK bootstrapped successfully")
    else:
        print_success("✅ CDK already bootstrapped")
    
    # Deployment confirmation
    if not auto_approve:
        print_info("")
        print_info("🚀 Ready to deploy pipeline infrastructure:")
        print_info(f"   Project: {config['project_name']}")
        print_info(f"   Environment: {deploy_env}")
        print_info(f"   Region: {deploy_region}")
        print_info("")
        
        if not confirm("Proceed with deployment?"):
            print_info("Deployment cancelled")
            return
    
    # CDK diff (show changes)
    print_step("Checking deployment changes...")
    success, diff_output = run_cdk_command(['cdk', 'diff'], cdk_path, timeout=120)
    if success and diff_output.strip():
        print_info("📋 Infrastructure changes:")
        print_info(diff_output[:1000] + "..." if len(diff_output) > 1000 else diff_output)
    
    # Deploy CDK stack
    print_step("Deploying CDK stack...")
    print_info("This may take several minutes...")
    
    deploy_cmd = ['cdk', 'deploy']
    if auto_approve:
        deploy_cmd.append('--require-approval=never')
    
    success, deploy_output = run_cdk_command(deploy_cmd, cdk_path, timeout=1800)  # 30 minutes
    
    if success:
        print_success("✅ Pipeline deployed successfully!")
        print_info("")
        print_info("🎉 Your CI/CD pipeline is now active!")
        print_info("📊 You can monitor it using:")
        print_info("  • AWS Console > CodePipeline")
        print_info("  • pipeline status")
        print_info("  • pipeline logs")
        
        # Show deployment outputs if available
        if "Outputs:" in deploy_output:
            print_info("")
            print_info("📋 Stack outputs:")
            outputs_section = deploy_output.split("Outputs:")[-1]
            print_info(outputs_section[:500])
    else:
        print_error("❌ Deployment failed!")
        print_error("Error details:")
        print_error(deploy_output[:1000] if deploy_output else "Unknown error")
        print_info("")
        print_info("💡 Troubleshooting tips:")
        print_info("  • Check AWS credentials and permissions")
        print_info("  • Verify CDK bootstrap in the target region")
        print_info("  • Review error messages above")
        print_info("  • Check AWS CloudFormation console for more details")
        print_error("No pipeline configuration found!")
        print_info("Run 'pipeline init' first to initialize the configuration.")
        return
    
    print_step("Loading configuration...")
    config = load_config()
    
    project_name = config.get('project_name', 'my-pipeline')
    deploy_env = environment or config.get('environment', 'dev')
    deploy_region = region or config.get('aws_region', 'us-east-1')
    
    print_info(f"📦 Project: {project_name}")
    print_info(f"🌍 Environment: {deploy_env}")
    print_info(f"🗺️ Region: {deploy_region}")
    
    # For MVP, show what would be deployed
    print_step("Validating AWS credentials...")
    print_step("Checking CDK bootstrap status...")
    print_step("Planning deployment...")
    
    print_warning("🚧 Deployment is coming soon!")
    print_info("This command will deploy:")
    print_info("  • CodePipeline for CI/CD")
    print_info("  • CodeBuild project for builds")
    print_info("  • S3 bucket for artifacts")
    print_info("  • IAM roles and policies")
    print_info("  • CloudWatch logs and monitoring")
    
    print_info("\nFor now, you can manually deploy with:")
    print_info("  1. Ensure AWS CDK is installed: npm install -g aws-cdk")
    print_info("  2. Bootstrap CDK: cdk bootstrap")
    print_info("  3. Deploy stack: cdk deploy")
    
    print_success("Deployment planning completed!")
    print_info("Full deployment will be available in the next version.")
    
    # Show next steps
    print_info("\nRecommended next steps:")
    print_info("  • Review generated CDK code")
    print_info("  • Test the pipeline with a sample commit")
    print_info("  • Configure notifications and monitoring")