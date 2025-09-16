"""
Template Service - Integration between templates and pipeline creation
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import json

from .template_manager import TemplateManager, Template
from .template_schema import TemplateCategory, TemplateValidationError
from ..utils.console import print_error, print_success, print_info, print_warning


class TemplateService:
    """Service for applying templates to pipeline creation"""
    
    def __init__(self):
        self.template_manager = TemplateManager()
    
    def get_available_templates(self, category: Optional[TemplateCategory] = None) -> List[Template]:
        """Get all available templates"""
        return self.template_manager.list_templates(category)
    
    def apply_template(
        self,
        template_name: str,
        project_path: Path,
        parameters: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Apply template to create pipeline configuration"""
        try:
            # Get template
            template = self.template_manager.get_template(template_name)
            if not template:
                print_error(f"❌ Template '{template_name}' not found")
                return False
            
            print_info(f"🔄 Applying template '{template_name}'...")
            
            # Apply parameters to template
            parameters = parameters or {}
            config = template.apply_parameters(parameters)
            
            # Create pipeline.json with template configuration
            pipeline_config_file = project_path / "pipeline.json"
            
            # Merge with existing config if it exists
            if pipeline_config_file.exists():
                with open(pipeline_config_file) as f:
                    existing_config = json.load(f)
                
                # Merge configurations (template config takes precedence)
                merged_config = self._merge_configs(existing_config, config)
            else:
                merged_config = config
            
            # Add template metadata
            merged_config['template'] = {
                'name': template.schema.name,
                'version': template.schema.version,
                'applied_at': None,  # Will be set during actual pipeline creation
                'parameters': parameters
            }
            
            # Save configuration
            with open(pipeline_config_file, 'w') as f:
                json.dump(merged_config, f, indent=2)
            
            print_success(f"✅ Template '{template_name}' applied successfully!")
            print_info(f"📄 Pipeline configuration saved to: {pipeline_config_file}")
            
            return True
            
        except TemplateValidationError as e:
            print_error(f"❌ Template validation error: {str(e)}")
            return False
        except Exception as e:
            print_error(f"❌ Failed to apply template: {str(e)}")
            return False
    
    def create_template_from_project(
        self,
        project_path: Path,
        template_name: str,
        description: str,
        category: TemplateCategory,
        author: str,
        parameters: Optional[List[Dict[str, Any]]] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """Create template from existing project configuration"""
        try:
            pipeline_config_file = project_path / "pipeline.json"
            
            if not pipeline_config_file.exists():
                print_error("❌ No pipeline.json found in project")
                return False
            
            # Load existing configuration
            with open(pipeline_config_file) as f:
                config = json.load(f)
            
            # Remove template metadata if it exists
            if 'template' in config:
                del config['template']
            
            # Replace values with parameter placeholders
            if parameters:
                config = self._parameterize_config(config, parameters)
            
            # Create template
            template = self.template_manager.create_template(
                name=template_name,
                description=description,
                category=category,
                author=author,
                config=config,
                parameters=parameters,
                tags=tags
            )
            
            return True
            
        except Exception as e:
            print_error(f"❌ Failed to create template: {str(e)}")
            return False
    
    def get_template_info(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a template"""
        template = self.template_manager.get_template(template_name)
        if not template:
            return None
        
        return {
            'schema': template.schema.to_dict(),
            'parameter_count': len(template.schema.parameters),
            'required_parameters': [
                p.name for p in template.schema.parameters if p.required
            ],
            'optional_parameters': [
                p.name for p in template.schema.parameters if not p.required
            ],
            'extends': template.schema.extends,
            'requirements': template.schema.requirements or []
        }
    
    def validate_template_parameters(
        self,
        template_name: str,
        parameters: Dict[str, Any]
    ) -> tuple[bool, List[str]]:
        """Validate parameters for a template"""
        template = self.template_manager.get_template(template_name)
        if not template:
            return False, [f"Template '{template_name}' not found"]
        
        return template.schema.validate_parameters(parameters)
    
    def get_categories(self) -> List[Dict[str, str]]:
        """Get all available template categories"""
        return [
            {
                'value': category.value,
                'name': category.value.replace('-', ' ').title()
            }
            for category in TemplateCategory
        ]
    
    def _merge_configs(self, base_config: Dict[str, Any], template_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two configurations with template config taking precedence"""
        merged = base_config.copy()
        
        for key, value in template_config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                merged[key] = self._merge_configs(merged[key], value)
            else:
                # Template value takes precedence
                merged[key] = value
        
        return merged
    
    def _parameterize_config(
        self,
        config: Dict[str, Any],
        parameters: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Replace configuration values with parameter placeholders"""
        param_map = {p['name']: f"{{{{ {p['name']} }}}}" for p in parameters}
        
        def replace_values(obj):
            if isinstance(obj, dict):
                return {key: replace_values(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [replace_values(item) for item in obj]
            elif isinstance(obj, str):
                # Replace with parameter placeholders if value matches parameter name
                for param_name, placeholder in param_map.items():
                    if obj == param_name or param_name.lower() in obj.lower():
                        return placeholder
                return obj
            else:
                return obj
        
        return replace_values(config)