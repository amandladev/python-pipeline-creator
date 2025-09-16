"""
Tests for the init command

This module contains unit tests for the pipeline init command functionality.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from click.testing import CliRunner

from pipeline_creator.commands.init import init_command, get_default_config, validate_project_directory


class TestInitCommand:
    """Test class for init command functionality"""
    
    def setup_method(self):
        """Set up test environment before each test"""
        self.runner = CliRunner()
    
    def test_get_default_config(self):
        """Test that default configuration is properly structured"""
        config = get_default_config()
        
        # Check required top-level keys
        assert "version" in config
        assert "project_name" in config
        assert "aws_region" in config
        assert "environment" in config
        assert "pipeline" in config
        assert "deployment" in config
        assert "notifications" in config
        
        # Check pipeline structure
        pipeline = config["pipeline"]
        assert "type" in pipeline
        assert "build_spec" in pipeline
        assert "artifacts" in pipeline
        
        # Check build_spec structure
        build_spec = pipeline["build_spec"]
        assert "runtime" in build_spec
        assert "version" in build_spec
        assert "commands" in build_spec
        
        # Check commands structure
        commands = build_spec["commands"]
        assert "pre_build" in commands
        assert "build" in commands
        assert "post_build" in commands
        assert isinstance(commands["pre_build"], list)
        assert isinstance(commands["build"], list)
        assert isinstance(commands["post_build"], list)
    
    def test_init_command_basic(self):
        """Test init command with basic parameters"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Create a simple project file to make it look like a project
            with open("README.md", "w") as f:
                f.write("# Test Project")
            
            # Run init command
            result = self.runner.invoke(init_command, [
                '-n', 'test-project',
                '-r', 'us-east-1',
                '-e', 'dev'
            ])
            
            assert result.exit_code == 0
            assert "Pipeline configuration initialized successfully!" in result.output
            
            # Check that config file was created
            config_path = Path(temp_dir) / ".pipeline" / "config.json"
            assert config_path.exists()
            
            # Verify config content
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            assert config["project_name"] == "test-project"
            assert config["aws_region"] == "us-east-1"
            assert config["environment"] == "dev"
    
    def test_init_command_force_overwrite(self):
        """Test init command with force flag to overwrite existing config"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Create a simple project file
            with open("requirements.txt", "w") as f:
                f.write("click>=8.0.0")
            
            # Create .pipeline directory and config file
            pipeline_dir = Path(temp_dir) / ".pipeline"
            pipeline_dir.mkdir()
            config_path = pipeline_dir / "config.json"
            
            initial_config = {"version": "0.5", "project_name": "old-project"}
            with open(config_path, 'w') as f:
                json.dump(initial_config, f)
            
            # Run init command with force flag
            result = self.runner.invoke(init_command, [
                '-n', 'new-project',
                '-r', 'us-west-2',
                '--force'
            ])
            
            assert result.exit_code == 0
            assert "Pipeline configuration initialized successfully!" in result.output
            
            # Verify config was overwritten
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            assert config["project_name"] == "new-project"
            assert config["aws_region"] == "us-west-2"
            assert config["version"] == "1.0"  # Should be new default version
    
    def test_init_command_without_force_existing_config(self):
        """Test init command behavior when config exists without force flag"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Create a simple project file
            with open("package.json", "w") as f:
                f.write('{"name": "test"}')
            
            # Create existing config
            pipeline_dir = Path(temp_dir) / ".pipeline"
            pipeline_dir.mkdir()
            config_path = pipeline_dir / "config.json"
            
            initial_config = {"version": "0.5", "project_name": "existing-project"}
            with open(config_path, 'w') as f:
                json.dump(initial_config, f)
            
            # Run init command without force, but provide "n" response to overwrite prompt
            result = self.runner.invoke(init_command, [
                '-n', 'new-project'
            ], input='n\n')
            
            # Command should exit without overwriting
            assert "Pipeline configuration already exists!" in result.output
            
            # Verify config was not overwritten
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            assert config["project_name"] == "existing-project"
    
    def test_validate_project_directory_with_project_files(self):
        """Test project directory validation with project files present"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Create some project files
            with open("requirements.txt", "w") as f:
                f.write("click>=8.0.0")
            
            # Should validate successfully
            assert validate_project_directory() == True
    
    def test_validate_project_directory_empty(self):
        """Test project directory validation with empty directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Mock user input to decline continuing
            with pytest.MonkeyPatch().context() as m:
                m.setattr('builtins.input', lambda _: 'n')
                result = validate_project_directory()
                assert result == False
    
    def test_project_name_validation(self):
        """Test init command with various project name formats"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Create a project file
            with open("README.md", "w") as f:
                f.write("# Test")
            
            # Test valid project names
            valid_names = ["my-project", "my_project", "project123", "Project-Name"]
            
            for name in valid_names:
                result = self.runner.invoke(init_command, [
                    '-n', name,
                    '--force'
                ])
                
                assert result.exit_code == 0, f"Failed for project name: {name}"
                
                # Verify config was created with correct name
                config_path = Path(temp_dir) / ".pipeline" / "config.json"
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                assert config["project_name"] == name


if __name__ == "__main__":
    pytest.main([__file__])