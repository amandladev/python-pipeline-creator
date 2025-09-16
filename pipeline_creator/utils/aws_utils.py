"""
AWS utility functions for Pipeline Creator CLI

This module provides utility functions for AWS operations and validations.
"""

import boto3
import subprocess
import json
import os
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional, Dict, Any, Tuple
from pathlib import Path


def check_aws_credentials() -> bool:
    """
    Check if AWS credentials are configured
    
    Returns:
        True if credentials are available, False otherwise
    """
    try:
        # Try to create a session and get caller identity
        session = boto3.Session()
        sts = session.client('sts')
        sts.get_caller_identity()
        return True
    except (NoCredentialsError, ClientError):
        return False


def get_aws_account_info() -> Optional[Dict[str, str]]:
    """
    Get AWS account information
    
    Returns:
        Dictionary with account ID and user info, or None if not available
    """
    try:
        session = boto3.Session()
        sts = session.client('sts')
        response = sts.get_caller_identity()
        
        return {
            'account_id': response.get('Account'),
            'user_id': response.get('UserId'),
            'arn': response.get('Arn')
        }
    except (NoCredentialsError, ClientError):
        return None


def check_cdk_installed() -> bool:
    """
    Check if AWS CDK CLI is installed
    
    Returns:
        True if CDK is installed, False otherwise
    """
    try:
        result = subprocess.run(['cdk', '--version'], 
                              capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        return False


def get_cdk_version() -> Optional[str]:
    """
    Get AWS CDK CLI version
    
    Returns:
        CDK version string or None if not available
    """
    try:
        result = subprocess.run(['cdk', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        return None


def check_cdk_bootstrap(region: str) -> Tuple[bool, Optional[str]]:
    """
    Check if CDK is bootstrapped in the specified region
    
    Args:
        region: AWS region to check
        
    Returns:
        Tuple of (is_bootstrapped, error_message)
    """
    try:
        session = boto3.Session()
        cloudformation = session.client('cloudformation', region_name=region)
        
        # Check for CDK bootstrap stack
        try:
            response = cloudformation.describe_stacks(StackName='CDKToolkit')
            stack = response['Stacks'][0]
            if stack['StackStatus'] in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
                return True, None
            else:
                return False, f"CDK bootstrap stack is in status: {stack['StackStatus']}"
        except ClientError as e:
            if e.response['Error']['Code'] == 'ValidationError':
                return False, "CDK is not bootstrapped in this region"
            return False, str(e)
            
    except Exception as e:
        return False, f"Error checking CDK bootstrap status: {str(e)}"


def bootstrap_cdk(region: str) -> Tuple[bool, Optional[str]]:
    """
    Bootstrap CDK in the specified region
    
    Args:
        region: AWS region to bootstrap
        
    Returns:
        Tuple of (success, error_message)
    """
    try:
        result = subprocess.run([
            'cdk', 'bootstrap', 
            f'aws://unknown-account/{region}'
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            return True, None
        else:
            return False, result.stderr or result.stdout
            
    except subprocess.TimeoutExpired:
        return False, "CDK bootstrap timed out after 5 minutes"
    except Exception as e:
        return False, f"Error during CDK bootstrap: {str(e)}"


def validate_aws_region(region: str) -> bool:
    """
    Validate AWS region name
    
    Args:
        region: AWS region name
        
    Returns:
        True if valid region, False otherwise
    """
    try:
        session = boto3.Session()
        ec2 = session.client('ec2', region_name=region)
        ec2.describe_regions(RegionNames=[region])
        return True
    except (ClientError, NoCredentialsError):
        return False


def get_available_regions() -> list:
    """
    Get list of available AWS regions
    
    Returns:
        List of region names
    """
    try:
        session = boto3.Session()
        ec2 = session.client('ec2')
        response = ec2.describe_regions()
        return [region['RegionName'] for region in response['Regions']]
    except (ClientError, NoCredentialsError):
        # Return common regions if unable to fetch
        return [
            'us-east-1', 'us-west-1', 'us-west-2', 
            'eu-west-1', 'eu-central-1', 'ap-southeast-1'
        ]


def check_cdk_bootstrap_status(region: str) -> bool:
    """
    Check if CDK is bootstrapped in the given region
    
    Args:
        region: AWS region to check
        
    Returns:
        True if bootstrapped, False otherwise
    """
    try:
        session = boto3.Session()
        cfn = session.client('cloudformation', region_name=region)
        
        # Check for CDK bootstrap stack
        response = cfn.describe_stacks(StackName='CDKToolkit')
        stack = response['Stacks'][0]
        return stack['StackStatus'] in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']
    except ClientError:
        return False


def get_s3_bucket_exists(bucket_name: str) -> bool:
    """
    Check if S3 bucket exists and is accessible
    
    Args:
        bucket_name: S3 bucket name
        
    Returns:
        True if bucket exists and accessible, False otherwise
    """
    try:
        session = boto3.Session()
        s3 = session.client('s3')
        s3.head_bucket(Bucket=bucket_name)
        return True
    except ClientError:
        return False