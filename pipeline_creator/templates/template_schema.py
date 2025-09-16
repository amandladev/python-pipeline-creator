"""
Template Schema Definition - Structure and validation for pipeline templates
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import json
from pathlib import Path


class TemplateCategory(Enum):
    """Template categories for organization"""
    WEB_FRONTEND = "web-frontend"
    WEB_BACKEND = "web-backend"
    API = "api"
    MICROSERVICE = "microservice"
    MOBILE = "mobile"
    DESKTOP = "desktop"
    DATA_PROCESSING = "data-processing"
    ML_AI = "ml-ai"
    DEVOPS = "devops"
    CUSTOM = "custom"


class ParameterType(Enum):
    """Parameter types for template configuration"""
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    SELECT = "select"


@dataclass
class TemplateParameter:
    """Template parameter definition"""
    name: str
    type: ParameterType
    description: str
    default: Any = None
    required: bool = True
    options: Optional[List[str]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None
    
    def validate(self, value: Any) -> tuple[bool, str]:
        """Validate parameter value"""
        if value is None:
            if self.required:
                return False, f"Parameter '{self.name}' is required"
            return True, ""
        
        # Type validation
        if self.type == ParameterType.STRING and not isinstance(value, str):
            return False, f"Parameter '{self.name}' must be a string"
        elif self.type == ParameterType.INTEGER and not isinstance(value, int):
            return False, f"Parameter '{self.name}' must be an integer"
        elif self.type == ParameterType.BOOLEAN and not isinstance(value, bool):
            return False, f"Parameter '{self.name}' must be a boolean"
        elif self.type == ParameterType.ARRAY and not isinstance(value, list):
            return False, f"Parameter '{self.name}' must be an array"
        elif self.type == ParameterType.OBJECT and not isinstance(value, dict):
            return False, f"Parameter '{self.name}' must be an object"
        elif self.type == ParameterType.SELECT and value not in (self.options or []):
            return False, f"Parameter '{self.name}' must be one of: {', '.join(self.options or [])}"
        
        # Range validation
        if self.type in [ParameterType.INTEGER] and isinstance(value, (int, float)):
            if self.min_value is not None and value < self.min_value:
                return False, f"Parameter '{self.name}' must be >= {self.min_value}"
            if self.max_value is not None and value > self.max_value:
                return False, f"Parameter '{self.name}' must be <= {self.max_value}"
        
        return True, ""


@dataclass
class TemplateSchema:
    """Template schema definition"""
    name: str
    version: str
    description: str
    category: TemplateCategory
    author: str
    tags: List[str]
    parameters: List[TemplateParameter]
    extends: Optional[str] = None  # Base template to extend
    requirements: Optional[List[str]] = None  # Required tools/services
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemplateSchema':
        """Create schema from dictionary"""
        parameters = [
            TemplateParameter(
                name=p['name'],
                type=ParameterType(p['type']),
                description=p['description'],
                default=p.get('default'),
                required=p.get('required', True),
                options=p.get('options'),
                min_value=p.get('min_value'),
                max_value=p.get('max_value'),
                pattern=p.get('pattern')
            )
            for p in data.get('parameters', [])
        ]
        
        return cls(
            name=data['name'],
            version=data['version'],
            description=data['description'],
            category=TemplateCategory(data['category']),
            author=data['author'],
            tags=data.get('tags', []),
            parameters=parameters,
            extends=data.get('extends'),
            requirements=data.get('requirements')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert schema to dictionary"""
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'category': self.category.value,
            'author': self.author,
            'tags': self.tags,
            'extends': self.extends,
            'requirements': self.requirements,
            'parameters': [
                {
                    'name': p.name,
                    'type': p.type.value,
                    'description': p.description,
                    'default': p.default,
                    'required': p.required,
                    'options': p.options,
                    'min_value': p.min_value,
                    'max_value': p.max_value,
                    'pattern': p.pattern
                }
                for p in self.parameters
            ]
        }
    
    def validate_parameters(self, values: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate parameter values against schema"""
        errors = []
        
        for param in self.parameters:
            value = values.get(param.name)
            is_valid, error_msg = param.validate(value)
            if not is_valid:
                errors.append(error_msg)
        
        return len(errors) == 0, errors
    
    def get_default_values(self) -> Dict[str, Any]:
        """Get default parameter values"""
        return {
            param.name: param.default 
            for param in self.parameters 
            if param.default is not None
        }


class TemplateValidationError(Exception):
    """Exception raised when template validation fails"""
    pass