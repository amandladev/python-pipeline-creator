"""
Template Inheritance - Support for template extension and composition
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import json

from .template_manager import TemplateManager, Template
from .template_schema import TemplateSchema, TemplateParameter
from ..utils.console import print_error, print_success, print_info


class TemplateInheritance:
    """Handle template inheritance and composition"""
    
    def __init__(self, template_manager: TemplateManager):
        self.template_manager = template_manager
    
    def resolve_template(self, template: Template) -> Template:
        """Resolve template inheritance chain"""
        if not template.schema.extends:
            return template
        
        # Get base template
        base_template = self.template_manager.get_template(template.schema.extends)
        if not base_template:
            print_error(f"❌ Base template '{template.schema.extends}' not found")
            return template
        
        # Recursively resolve base template
        resolved_base = self.resolve_template(base_template)
        
        # Merge templates
        merged_template = self._merge_templates(resolved_base, template)
        return merged_template
    
    def _merge_templates(self, base_template: Template, child_template: Template) -> Template:
        """Merge child template with base template"""
        # Merge schema
        merged_schema = self._merge_schemas(base_template.schema, child_template.schema)
        
        # Merge configurations
        merged_config = self._merge_configs(base_template.config, child_template.config)
        
        return Template(
            schema=merged_schema,
            config=merged_config,
            template_path=child_template.template_path
        )
    
    def _merge_schemas(self, base_schema: TemplateSchema, child_schema: TemplateSchema) -> TemplateSchema:
        """Merge template schemas"""
        # Base parameters
        base_params = {p.name: p for p in base_schema.parameters}
        
        # Child parameters (override base if same name)
        merged_params = base_params.copy()
        for param in child_schema.parameters:
            merged_params[param.name] = param
        
        # Merge other properties
        merged_tags = list(set(base_schema.tags + child_schema.tags))
        merged_requirements = list(set((base_schema.requirements or []) + (child_schema.requirements or [])))
        
        return TemplateSchema(
            name=child_schema.name,
            version=child_schema.version,
            description=child_schema.description,
            category=child_schema.category,
            author=child_schema.author,
            tags=merged_tags,
            parameters=list(merged_params.values()),
            extends=child_schema.extends,
            requirements=merged_requirements
        )
    
    def _merge_configs(self, base_config: Dict[str, Any], child_config: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge configuration objects"""
        def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
            result = base.copy()
            
            for key, value in override.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                elif key in result and isinstance(result[key], list) and isinstance(value, list):
                    # For lists, extend rather than replace
                    result[key] = result[key] + value
                else:
                    result[key] = value
            
            return result
        
        return deep_merge(base_config, child_config)
    
    def create_extended_template(
        self,
        base_template_name: str,
        new_template_name: str,
        description: str,
        author: str,
        additional_config: Optional[Dict[str, Any]] = None,
        additional_parameters: Optional[List[Dict[str, Any]]] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """Create a new template that extends an existing one"""
        try:
            base_template = self.template_manager.get_template(base_template_name)
            if not base_template:
                print_error(f"❌ Base template '{base_template_name}' not found")
                return False
            
            # Create extended template directory
            template_dir = self.template_manager.user_templates_dir / new_template_name
            template_dir.mkdir(exist_ok=True)
            
            # Create schema for extended template
            schema_data = {
                'name': new_template_name,
                'version': '1.0.0',
                'description': description,
                'category': base_template.schema.category.value,
                'author': author,
                'tags': tags or [],
                'extends': base_template_name,
                'parameters': additional_parameters or []
            }
            
            # Save schema
            with open(template_dir / "template.json", 'w') as f:
                json.dump(schema_data, f, indent=2)
            
            # Save additional config (will be merged with base)
            config = additional_config or {}
            with open(template_dir / "config.json", 'w') as f:
                json.dump(config, f, indent=2)
            
            print_success(f"✅ Extended template '{new_template_name}' created successfully!")
            print_info(f"📋 Extends: {base_template_name}")
            
            return True
            
        except Exception as e:
            print_error(f"❌ Failed to create extended template: {str(e)}")
            return False
    
    def get_inheritance_chain(self, template_name: str) -> List[str]:
        """Get the inheritance chain for a template"""
        chain = []
        current_template_name = template_name
        
        while current_template_name:
            chain.append(current_template_name)
            
            template = self.template_manager.get_template(current_template_name)
            if not template or not template.schema.extends:
                break
            
            current_template_name = template.schema.extends
            
            # Prevent infinite loops
            if current_template_name in chain:
                print_error(f"❌ Circular inheritance detected in template '{template_name}'")
                break
        
        return chain
    
    def validate_inheritance(self, template_name: str) -> tuple[bool, List[str]]:
        """Validate template inheritance chain"""
        errors = []
        chain = self.get_inheritance_chain(template_name)
        
        # Check for circular inheritance
        if len(chain) != len(set(chain)):
            errors.append("Circular inheritance detected")
        
        # Check if all base templates exist
        for template_name_in_chain in chain:
            template = self.template_manager.get_template(template_name_in_chain)
            if not template:
                errors.append(f"Template '{template_name_in_chain}' not found in inheritance chain")
        
        return len(errors) == 0, errors