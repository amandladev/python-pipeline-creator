"""
Template Management Commands - CLI interface for pipeline templates
"""

import click
from pathlib import Path
from typing import Optional, Dict, Any
import json

from ..templates.template_service import TemplateService
from ..templates.template_schema import TemplateCategory
from ..templates.template_inheritance import TemplateInheritance
from ..utils.console import print_error, print_success, print_info, print_warning


@click.group()
def templates():
    """Manage pipeline templates."""
    pass


@templates.command()
@click.option('--category', '-c', type=click.Choice([cat.value for cat in TemplateCategory]), 
              help='Filter templates by category')
@click.option('--format', '-f', type=click.Choice(['table', 'json']), default='table',
              help='Output format')
def list(category: Optional[str], format: str):
    """List available pipeline templates."""
    service = TemplateService()
    
    # Get templates
    category_filter = TemplateCategory(category) if category else None
    templates = service.get_available_templates(category_filter)
    
    if not templates:
        if category:
            print_info(f"📭 No templates found in category '{category}'")
        else:
            print_info("📭 No templates available")
        return
    
    if format == 'json':
        # JSON output
        templates_data = []
        for template in templates:
            templates_data.append({
                'name': template.schema.name,
                'version': template.schema.version,
                'description': template.schema.description,
                'category': template.schema.category.value,
                'author': template.schema.author,
                'tags': template.schema.tags,
                'parameters': len(template.schema.parameters)
            })
        
        click.echo(json.dumps(templates_data, indent=2))
    else:
        # Table output
        print_info(f"\n📋 Available Templates ({len(templates)})")
        print_info("=" * 80)
        
        for template in templates:
            category_icon = {
                'web-frontend': '🌐',
                'web-backend': '⚙️',
                'api': '🔌',
                'microservice': '🏗️',
                'mobile': '📱',
                'desktop': '💻',
                'data-processing': '📊',
                'ml-ai': '🤖',
                'devops': '🔧',
                'custom': '🎯'
            }.get(template.schema.category.value, '📦')
            
            print_info(f"{category_icon} {template.schema.name} (v{template.schema.version})")
            print_info(f"   📝 {template.schema.description}")
            print_info(f"   👤 {template.schema.author}")
            print_info(f"   🏷️  {', '.join(template.schema.tags)}")
            print_info(f"   ⚙️  {len(template.schema.parameters)} parameters")
            
            if template.schema.extends:
                print_info(f"   🔗 Extends: {template.schema.extends}")
            
            print_info("")


@templates.command()
@click.argument('template_name')
@click.option('--project-path', '-p', type=click.Path(exists=True, path_type=Path), 
              default=Path.cwd(), help='Project path to apply template to')
@click.option('--parameter', '-P', multiple=True, help='Template parameter (key=value)')
@click.option('--interactive', '-i', is_flag=True, help='Interactive parameter configuration')
def use(template_name: str, project_path: Path, parameter: tuple, interactive: bool):
    """Apply a template to create pipeline configuration."""
    service = TemplateService()
    
    # Get template info
    template_info = service.get_template_info(template_name)
    if not template_info:
        print_error(f"❌ Template '{template_name}' not found")
        click.echo("Use 'pipeline templates list' to see available templates")
        return
    
    print_info(f"🔄 Applying template '{template_name}'...")
    print_info(f"📝 {template_info['schema']['description']}")
    
    # Parse command line parameters
    parameters = {}
    for param_str in parameter:
        if '=' not in param_str:
            print_error(f"❌ Invalid parameter format: {param_str}")
            print_info("Use format: --parameter key=value")
            return
        
        key, value = param_str.split('=', 1)
        # Try to parse as JSON for complex values
        try:
            parameters[key] = json.loads(value)
        except json.JSONDecodeError:
            parameters[key] = value
    
    # Interactive parameter collection
    if interactive or not parameters:
        print_info("\n⚙️ Template Parameters:")
        template = service.template_manager.get_template(template_name)
        
        for param in template.schema.parameters:
            current_value = parameters.get(param.name)
            
            if current_value is not None:
                print_info(f"✓ {param.name}: {current_value} (from command line)")
                continue
            
            # Interactive prompt
            prompt_text = f"{param.name}"
            if param.description:
                prompt_text += f" ({param.description})"
            
            if param.default is not None:
                prompt_text += f" [{param.default}]"
            
            if param.options:
                prompt_text += f" (options: {', '.join(param.options)})"
            
            if param.required:
                while True:
                    value = click.prompt(prompt_text, default=param.default, show_default=False)
                    if value or not param.required:
                        break
                    print_error("This parameter is required")
            else:
                value = click.prompt(prompt_text, default=param.default, show_default=False)
            
            # Type conversion
            if param.type.value == 'boolean':
                value = str(value).lower() in ['true', '1', 'yes', 'y']
            elif param.type.value == 'integer':
                try:
                    value = int(value)
                except ValueError:
                    print_error(f"Invalid integer value: {value}")
                    return
            
            parameters[param.name] = value
    
    # Validate parameters
    is_valid, errors = service.validate_template_parameters(template_name, parameters)
    if not is_valid:
        print_error("❌ Parameter validation failed:")
        for error in errors:
            print_error(f"   • {error}")
        return
    
    # Apply template
    if service.apply_template(template_name, project_path, parameters):
        print_success("🎉 Template applied successfully!")
        print_info("Next steps:")
        print_info("  1. Review the generated pipeline.json")
        print_info("  2. Run 'pipeline generate' to create AWS infrastructure")
        print_info("  3. Run 'pipeline deploy' to deploy your pipeline")
    else:
        print_error("❌ Failed to apply template")


@templates.command()
@click.argument('template_name')
def info(template_name: str):
    """Show detailed information about a template."""
    service = TemplateService()
    template_info = service.get_template_info(template_name)
    
    if not template_info:
        print_error(f"❌ Template '{template_name}' not found")
        return
    
    schema = template_info['schema']
    
    print_info(f"\n📋 Template: {schema['name']} (v{schema['version']})")
    print_info("=" * 60)
    print_info(f"📝 Description: {schema['description']}")
    print_info(f"🏷️  Category: {schema['category']}")
    print_info(f"👤 Author: {schema['author']}")
    print_info(f"🏷️  Tags: {', '.join(schema['tags'])}")
    
    if schema.get('extends'):
        print_info(f"🔗 Extends: {schema['extends']}")
    
    if schema.get('requirements'):
        print_info(f"📦 Requirements:")
        for req in schema['requirements']:
            print_info(f"   • {req}")
    
    # Parameters
    if template_info['parameter_count'] > 0:
        print_info(f"\n⚙️ Parameters ({template_info['parameter_count']}):")
        
        template = service.template_manager.get_template(template_name)
        for param in template.schema.parameters:
            status = "required" if param.required else "optional"
            print_info(f"   • {param.name} ({param.type.value}, {status})")
            print_info(f"     {param.description}")
            
            if param.default is not None:
                print_info(f"     Default: {param.default}")
            
            if param.options:
                print_info(f"     Options: {', '.join(param.options)}")
            
            print_info("")
    else:
        print_info("\n⚙️ No parameters required")


@templates.command()
@click.argument('template_name')
@click.option('--project-path', '-p', type=click.Path(exists=True, path_type=Path),
              default=Path.cwd(), help='Project path to create template from')
@click.option('--description', '-d', required=True, help='Template description')
@click.option('--category', '-c', type=click.Choice([cat.value for cat in TemplateCategory]),
              required=True, help='Template category')
@click.option('--author', '-a', required=True, help='Template author')
@click.option('--tag', '-t', multiple=True, help='Template tags')
def create(template_name: str, project_path: Path, description: str, 
          category: str, author: str, tag: tuple):
    """Create a new template from existing project."""
    service = TemplateService()
    
    # Check if pipeline.json exists
    pipeline_config = project_path / "pipeline.json"
    if not pipeline_config.exists():
        print_error("❌ No pipeline.json found in project")
        print_info("Run 'pipeline init' first to create a pipeline configuration")
        return
    
    # Interactive parameter definition
    print_info("\n⚙️ Define template parameters:")
    print_info("Enter parameter definitions (press Enter with empty name to finish):")
    
    parameters = []
    while True:
        param_name = click.prompt("Parameter name", default="", show_default=False)
        if not param_name:
            break
        
        param_type = click.prompt(
            "Parameter type",
            type=click.Choice(['string', 'integer', 'boolean', 'select']),
            default='string'
        )
        
        param_desc = click.prompt("Parameter description")
        param_required = click.confirm("Required parameter?", default=True)
        param_default = click.prompt("Default value", default="", show_default=False) or None
        
        param_options = None
        if param_type == 'select':
            options_str = click.prompt("Options (comma-separated)")
            param_options = [opt.strip() for opt in options_str.split(',')]
        
        parameters.append({
            'name': param_name,
            'type': param_type,
            'description': param_desc,
            'required': param_required,
            'default': param_default,
            'options': param_options
        })
    
    # Create template
    if service.create_template_from_project(
        project_path=project_path,
        template_name=template_name,
        description=description,
        category=TemplateCategory(category),
        author=author,
        parameters=parameters,
        tags=list(tag)
    ):
        print_success(f"✅ Template '{template_name}' created successfully!")
        print_info("You can now share this template with others using 'pipeline templates export'")


@templates.command()
@click.argument('template_name')
@click.confirmation_option(prompt='Are you sure you want to delete this template?')
def delete(template_name: str):
    """Delete a user template."""
    service = TemplateService()
    
    if service.template_manager.delete_template(template_name):
        print_success(f"✅ Template '{template_name}' deleted successfully!")


@templates.command()
@click.argument('template_file', type=click.Path(exists=True, path_type=Path))
def import_template(template_file: Path):
    """Import a template from file or directory."""
    service = TemplateService()
    
    template = service.template_manager.import_template(template_file)
    if template:
        print_success(f"✅ Template '{template.schema.name}' imported successfully!")
    else:
        print_error("❌ Failed to import template")


@templates.command() 
@click.argument('template_name')
@click.argument('output_path', type=click.Path(path_type=Path))
def export(template_name: str, output_path: Path):
    """Export a template to file or directory."""
    service = TemplateService()
    
    if service.template_manager.export_template(template_name, output_path):
        print_success(f"✅ Template '{template_name}' exported to {output_path}")


@templates.command()
@click.argument('base_template')
@click.argument('new_template_name')
@click.option('--description', '-d', required=True, help='New template description')
@click.option('--author', '-a', required=True, help='Template author')
@click.option('--tag', '-t', multiple=True, help='Additional tags')
def extend(base_template: str, new_template_name: str, description: str, author: str, tag: tuple):
    """Create a new template that extends an existing one."""
    service = TemplateService()
    inheritance = TemplateInheritance(service.template_manager)
    
    print_info(f"🔄 Creating extended template '{new_template_name}' based on '{base_template}'...")
    
    # Collect additional configuration
    print_info("\n⚙️ Additional configuration (JSON format, or press Enter to skip):")
    additional_config_str = click.prompt("Additional config", default="", show_default=False)
    
    additional_config = {}
    if additional_config_str:
        try:
            additional_config = json.loads(additional_config_str)
        except json.JSONDecodeError:
            print_error("❌ Invalid JSON format")
            return
    
    # Create extended template
    if inheritance.create_extended_template(
        base_template_name=base_template,
        new_template_name=new_template_name,
        description=description,
        author=author,
        additional_config=additional_config if additional_config else None,
        tags=list(tag)
    ):
        print_success(f"✅ Extended template '{new_template_name}' created successfully!")


# Add to main CLI
def add_templates_command(main_group):
    """Add templates command to main CLI group"""
    main_group.add_command(templates)