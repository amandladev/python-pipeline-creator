"""
Template Manager - Core template management functionality
"""

import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import uuid

from .template_schema import TemplateSchema, TemplateCategory, TemplateValidationError
from ..utils.console import print_error, print_success, print_info, print_warning


@dataclass
class Template:
    """Template definition with metadata and configuration"""
    schema: TemplateSchema
    config: Dict[str, Any]
    template_path: Path
    
    @property
    def id(self) -> str:
        """Get template unique identifier"""
        return f"{self.schema.name}-{self.schema.version}"
    
    def apply_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Apply parameters to template configuration"""
        # Validate parameters first
        is_valid, errors = self.schema.validate_parameters(parameters)
        if not is_valid:
            raise TemplateValidationError(f"Parameter validation failed: {'; '.join(errors)}")
        
        # Merge with defaults
        final_params = self.schema.get_default_values()
        final_params.update(parameters)
        
        # Replace placeholders in config
        config_str = json.dumps(self.config)
        for param_name, param_value in final_params.items():
            placeholder = f"{{{{ {param_name} }}}}"
            if isinstance(param_value, str):
                config_str = config_str.replace(placeholder, param_value)
            else:
                config_str = config_str.replace(f'"{placeholder}"', json.dumps(param_value))
        
        return json.loads(config_str)


class TemplateManager:
    """Template management system"""
    
    def __init__(self, templates_dir: Optional[Path] = None):
        self.templates_dir = templates_dir or Path.home() / ".pipeline-creator" / "templates"
        self.predefined_dir = Path(__file__).parent / "predefined"
        self.user_templates_dir = self.templates_dir / "user"
        
        # Ensure directories exist
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.user_templates_dir.mkdir(parents=True, exist_ok=True)
    
    def list_templates(self, category: Optional[TemplateCategory] = None) -> List[Template]:
        """List all available templates"""
        templates = []
        
        # Load predefined templates
        if self.predefined_dir.exists():
            templates.extend(self._load_templates_from_dir(self.predefined_dir))
        
        # Load user templates
        templates.extend(self._load_templates_from_dir(self.user_templates_dir))
        
        # Filter by category if specified
        if category:
            templates = [t for t in templates if t.schema.category == category]
        
        return templates
    
    def get_template(self, template_name: str, version: Optional[str] = None) -> Optional[Template]:
        """Get specific template by name and version"""
        templates = self.list_templates()
        
        for template in templates:
            if template.schema.name == template_name:
                if version is None or template.schema.version == version:
                    return template
        
        return None
    
    def create_template(
        self,
        name: str,
        description: str,
        category: TemplateCategory,
        author: str,
        config: Dict[str, Any],
        parameters: Optional[List[Dict[str, Any]]] = None,
        tags: Optional[List[str]] = None,
        extends: Optional[str] = None
    ) -> Template:
        """Create a new template"""
        # Create template directory
        template_dir = self.user_templates_dir / name
        template_dir.mkdir(exist_ok=True)
        
        # Create schema
        schema_data = {
            'name': name,
            'version': '1.0.0',
            'description': description,
            'category': category.value,
            'author': author,
            'tags': tags or [],
            'parameters': parameters or [],
            'extends': extends
        }
        
        schema = TemplateSchema.from_dict(schema_data)
        
        # Save schema file
        schema_file = template_dir / "template.json"
        with open(schema_file, 'w') as f:
            json.dump(schema.to_dict(), f, indent=2)
        
        # Save config file
        config_file = template_dir / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print_success(f"✅ Template '{name}' created successfully!")
        return Template(schema=schema, config=config, template_path=template_dir)
    
    def delete_template(self, template_name: str) -> bool:
        """Delete a user template"""
        template_dir = self.user_templates_dir / template_name
        
        if not template_dir.exists():
            print_error(f"❌ Template '{template_name}' not found")
            return False
        
        # Only allow deletion of user templates, not predefined ones
        try:
            shutil.rmtree(template_dir)
            print_success(f"✅ Template '{template_name}' deleted successfully!")
            return True
        except Exception as e:
            print_error(f"❌ Failed to delete template: {str(e)}")
            return False
    
    def import_template(self, template_file: Path) -> Optional[Template]:
        """Import template from file"""
        try:
            if template_file.is_file() and template_file.suffix == '.json':
                # Single file template
                with open(template_file) as f:
                    template_data = json.load(f)
                
                return self._import_single_template(template_data, template_file.parent)
            
            elif template_file.is_dir():
                # Directory template
                return self._import_directory_template(template_file)
            
            else:
                print_error("❌ Invalid template file or directory")
                return None
                
        except Exception as e:
            print_error(f"❌ Failed to import template: {str(e)}")
            return None
    
    def export_template(self, template_name: str, export_path: Path) -> bool:
        """Export template to file/directory"""
        template = self.get_template(template_name)
        if not template:
            print_error(f"❌ Template '{template_name}' not found")
            return False
        
        try:
            if export_path.suffix == '.json':
                # Export as single file
                export_data = {
                    'schema': template.schema.to_dict(),
                    'config': template.config
                }
                
                with open(export_path, 'w') as f:
                    json.dump(export_data, f, indent=2)
            
            else:
                # Export as directory
                export_path.mkdir(parents=True, exist_ok=True)
                
                # Copy template files
                if template.template_path.exists():
                    shutil.copytree(template.template_path, export_path, dirs_exist_ok=True)
            
            print_success(f"✅ Template '{template_name}' exported to {export_path}")
            return True
            
        except Exception as e:
            print_error(f"❌ Failed to export template: {str(e)}")
            return False
    
    def _load_templates_from_dir(self, templates_dir: Path) -> List[Template]:
        """Load templates from directory"""
        templates = []
        
        if not templates_dir.exists():
            return templates
        
        for template_dir in templates_dir.iterdir():
            if template_dir.is_dir():
                template = self._load_template(template_dir)
                if template:
                    templates.append(template)
        
        return templates
    
    def _load_template(self, template_dir: Path) -> Optional[Template]:
        """Load single template from directory"""
        schema_file = template_dir / "template.json"
        config_file = template_dir / "config.json"
        
        if not (schema_file.exists() and config_file.exists()):
            return None
        
        try:
            # Load schema
            with open(schema_file) as f:
                schema_data = json.load(f)
            schema = TemplateSchema.from_dict(schema_data)
            
            # Load config
            with open(config_file) as f:
                config = json.load(f)
            
            return Template(schema=schema, config=config, template_path=template_dir)
            
        except Exception as e:
            print_warning(f"⚠️ Failed to load template from {template_dir}: {str(e)}")
            return None
    
    def _import_single_template(self, template_data: Dict[str, Any], source_dir: Path) -> Template:
        """Import single file template"""
        schema = TemplateSchema.from_dict(template_data['schema'])
        config = template_data['config']
        
        # Create template directory
        template_dir = self.user_templates_dir / schema.name
        template_dir.mkdir(exist_ok=True)
        
        # Save files
        with open(template_dir / "template.json", 'w') as f:
            json.dump(schema.to_dict(), f, indent=2)
        
        with open(template_dir / "config.json", 'w') as f:
            json.dump(config, f, indent=2)
        
        print_success(f"✅ Template '{schema.name}' imported successfully!")
        return Template(schema=schema, config=config, template_path=template_dir)
    
    def _import_directory_template(self, source_dir: Path) -> Template:
        """Import directory template"""
        template = self._load_template(source_dir)
        if not template:
            raise TemplateValidationError("Invalid template directory structure")
        
        # Copy to user templates
        target_dir = self.user_templates_dir / template.schema.name
        if target_dir.exists():
            shutil.rmtree(target_dir)
        
        shutil.copytree(source_dir, target_dir)
        
        print_success(f"✅ Template '{template.schema.name}' imported successfully!")
        return Template(schema=template.schema, config=template.config, template_path=target_dir)