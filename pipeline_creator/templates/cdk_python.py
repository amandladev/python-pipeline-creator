"""
CDK Python App template for Pipeline Creator
"""

CDK_APP_TEMPLATE = '''#!/usr/bin/env python3
import os
import aws_cdk as cdk
from {project_name_snake}.pipeline_stack import PipelineStack

app = cdk.App()

# Environment configuration
env = cdk.Environment(
    account=os.getenv('CDK_DEFAULT_ACCOUNT'),
    region="{aws_region}"
)

PipelineStack(
    app, 
    "{project_name_pascal}PipelineStack",
    project_name="{project_name}",
    environment="{environment}",
    env=env
)

app.synth()
'''

PIPELINE_STACK_TEMPLATE = '''import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_codebuild as codebuild,
    aws_s3 as s3,
    aws_iam as iam,
    RemovalPolicy
)
from constructs import Construct

class PipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, project_name: str, environment: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.project_name = project_name
        self.environment = environment
        
        # Create S3 bucket for artifacts
        self.artifacts_bucket = s3.Bucket(
            self, "ArtifactsBucket",
            bucket_name=f"{{project_name}}-{{environment}}-artifacts-{{cdk.Aws.ACCOUNT_ID}}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            versioned=True
        )
        
        # Create CodeBuild project
        self.build_project = self._create_build_project()
        
        # Create CodePipeline
        self.pipeline = self._create_pipeline()
    
    def _create_build_project(self) -> codebuild.Project:
        """Create CodeBuild project for the pipeline"""
        
        # Create CodeBuild service role
        build_role = iam.Role(
            self, "CodeBuildRole",
            assumed_by=iam.ServicePrincipal("codebuild.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchLogsFullAccess")
            ]
        )
        
        # Add additional permissions
        build_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject"
                ],
                resources=[
                    self.artifacts_bucket.bucket_arn,
                    f"{{self.artifacts_bucket.bucket_arn}}/*"
                ]
            )
        )
        
        return codebuild.Project(
            self, "BuildProject",
            project_name=f"{{self.project_name}}-{{self.environment}}-build",
            description=f"Build project for {{self.project_name}} ({{self.environment}})",
            source=codebuild.Source.git_hub(
                owner="{repo_owner}",
                repo="{repo_name}",
                webhook=True,
                webhook_filters=[
                    codebuild.FilterGroup.in_event_of(
                        codebuild.EventAction.PUSH
                    ).and_branch_is("main")
                ]
            ),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                compute_type=codebuild.ComputeType.SMALL,
                privileged=True
            ),
            build_spec=codebuild.BuildSpec.from_object({{
                "version": "0.2",
                "phases": {{
                    "pre_build": {{
                        "commands": {pre_build_commands}
                    }},
                    "build": {{
                        "commands": {build_commands}
                    }},
                    "post_build": {{
                        "commands": {post_build_commands}
                    }}
                }},
                "artifacts": {{
                    "files": {artifact_files}
                }}
            }}),
            artifacts=codebuild.Artifacts.s3(
                bucket=self.artifacts_bucket,
                include_build_id=True,
                name="BuildArtifacts"
            ),
            role=build_role
        )
    
    def _create_pipeline(self) -> codepipeline.Pipeline:
        """Create CodePipeline"""
        
        # Source output artifact
        source_output = codepipeline.Artifact("SourceOutput")
        
        # Build output artifact  
        build_output = codepipeline.Artifact("BuildOutput")
        
        # Create pipeline
        pipeline = codepipeline.Pipeline(
            self, "Pipeline",
            pipeline_name=f"{{self.project_name}}-{{self.environment}}-pipeline",
            artifact_bucket=self.artifacts_bucket,
            stages=[
                # Source stage
                codepipeline.StageProps(
                    stage_name="Source",
                    actions=[
                        codepipeline_actions.GitHubSourceAction(
                            action_name="GitHub_Source",
                            owner="{repo_owner}",
                            repo="{repo_name}",
                            branch="main",
                            oauth_token=cdk.SecretValue.secrets_manager("github-token"),
                            output=source_output
                        )
                    ]
                ),
                # Build stage
                codepipeline.StageProps(
                    stage_name="Build",
                    actions=[
                        codepipeline_actions.CodeBuildAction(
                            action_name="Build",
                            project=self.build_project,
                            input=source_output,
                            outputs=[build_output]
                        )
                    ]
                )
            ]
        )
        
        return pipeline
'''

CDK_JSON_TEMPLATE = '''{{
  "app": "python3 app.py",
  "watch": {{
    "include": [
      "**"
    ],
    "exclude": [
      "README.md",
      "cdk*.json",
      "requirements*.txt",
      "source.bat",
      "**/__pycache__",
      "**/*.pyc"
    ]
  }},
  "context": {{
    "@aws-cdk/aws-lambda:recognizeLayerVersion": true,
    "@aws-cdk/core:checkSecretUsage": true,
    "@aws-cdk/core:target=aws-cdk-lib": true,
    "@aws-cdk/core:enableStackNameDuplicates": true,
    "aws-cdk:enableDiffNoFail": true,
    "@aws-cdk/core:stackRelativeExports": true,
    "@aws-cdk/aws-ecr-assets:dockerIgnoreSupport": true,
    "@aws-cdk/aws-secretsmanager:useAttachedSecretResourcePolicyForSecretTargetAttachments": true,
    "@aws-cdk/aws-redshift:columnId": true,
    "@aws-cdk/aws-stepfunctions-tasks:enableLogging": true
  }}
}}'''

REQUIREMENTS_TEMPLATE = '''aws-cdk-lib==2.100.0
constructs>=10.0.0
'''

README_TEMPLATE = '''# {project_name} CDK Infrastructure

This directory contains the AWS CDK code for deploying the CI/CD pipeline for {project_name}.

## Prerequisites

- Python 3.8+
- AWS CLI configured
- AWS CDK CLI installed (`npm install -g aws-cdk`)

## Installation

```bash
cd cdk
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## Deployment

```bash
# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy the pipeline stack
cdk deploy

# View the diff before deployment
cdk diff

# Destroy the stack (when no longer needed)
cdk destroy
```

## Architecture

The pipeline includes:

- **S3 Bucket**: Stores build artifacts
- **CodeBuild Project**: Builds and tests the application
- **CodePipeline**: Orchestrates the CI/CD workflow
- **IAM Roles**: Proper permissions for services

## Configuration

The pipeline is configured based on `.pipeline/config.json` in your project root.

Environment: {environment}
Region: {aws_region}
'''