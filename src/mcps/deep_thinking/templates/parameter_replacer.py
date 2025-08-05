"""
Template Parameter Replacement System

Provides dynamic parameter replacement logic with context variable injection,
formatting, validation, and default value handling.
"""

import re
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field


@dataclass
class ParameterConfig:
    """Configuration for a template parameter"""
    name: str
    required: bool = False
    default_value: Optional[Any] = None
    validator: Optional[Callable[[Any], bool]] = None
    formatter: Optional[Callable[[Any], str]] = None
    description: str = ""


@dataclass
class ReplacementContext:
    """Context for parameter replacement"""
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    step_name: Optional[str] = None
    previous_results: Dict[str, Any] = field(default_factory=dict)
    custom_variables: Dict[str, Any] = field(default_factory=dict)


class ParameterValidationError(Exception):
    """Raised when parameter validation fails"""
    pass


class ParameterReplacer:
    """Advanced parameter replacement system for templates"""
    
    def __init__(self):
        self.parameter_configs: Dict[str, ParameterConfig] = {}
        self.global_context: Dict[str, Any] = {}
        self.formatters: Dict[str, Callable[[Any], str]] = {}
        self.validators: Dict[str, Callable[[Any], bool]] = {}
        
        # Register built-in formatters
        self._register_builtin_formatters()
        
        # Register built-in validators
        self._register_builtin_validators()
    
    def _register_builtin_formatters(self):
        """Register built-in formatters"""
        self.formatters.update({
            'upper': lambda x: str(x).upper(),
            'lower': lambda x: str(x).lower(),
            'title': lambda x: str(x).title(),
            'json': lambda x: json.dumps(x, ensure_ascii=False, indent=2) if not isinstance(x, str) else x,
            'json_compact': lambda x: json.dumps(x, ensure_ascii=False, separators=(',', ':')) if not isinstance(x, str) else x,
            'list': lambda x: '\n'.join(f"- {item}" for item in (x if isinstance(x, list) else [x])),
            'numbered_list': lambda x: '\n'.join(f"{i+1}. {item}" for i, item in enumerate(x if isinstance(x, list) else [x])),
            'date': lambda x: x.strftime('%Y-%m-%d') if hasattr(x, 'strftime') else str(x),
            'datetime': lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if hasattr(x, 'strftime') else str(x),
            'truncate': lambda x: str(x)[:100] + '...' if len(str(x)) > 100 else str(x),
            'escape_quotes': lambda x: str(x).replace('"', '\\"').replace("'", "\\'"),
            'markdown_code': lambda x: f"```\n{x}\n```",
            'markdown_quote': lambda x: '\n'.join(f"> {line}" for line in str(x).split('\n')),
        })
    
    def _register_builtin_validators(self):
        """Register built-in validators"""
        self.validators.update({
            'not_empty': lambda x: x is not None and str(x).strip() != '',
            'is_string': lambda x: isinstance(x, str),
            'is_number': lambda x: isinstance(x, (int, float)),
            'is_list': lambda x: isinstance(x, list),
            'is_dict': lambda x: isinstance(x, dict),
            'min_length': lambda x: len(str(x)) >= 3,  # Default minimum length
            'max_length': lambda x: len(str(x)) <= 1000,  # Default maximum length
            'is_json': lambda x: self._is_valid_json(str(x)),
            'is_url': lambda x: self._is_valid_url(str(x)),
            'is_email': lambda x: self._is_valid_email(str(x)),
        })
    
    def _is_valid_json(self, value: str) -> bool:
        """Check if a string is valid JSON"""
        try:
            json.loads(value)
            return True
        except (json.JSONDecodeError, TypeError):
            return False
    
    def _is_valid_url(self, value: str) -> bool:
        """Check if a string is a valid URL"""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(value) is not None
    
    def _is_valid_email(self, value: str) -> bool:
        """Check if a string is a valid email"""
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        return email_pattern.match(value) is not None
    
    def register_parameter_config(self, config: ParameterConfig):
        """Register a parameter configuration"""
        self.parameter_configs[config.name] = config
    
    def register_formatter(self, name: str, formatter: Callable[[Any], str]):
        """Register a custom formatter"""
        self.formatters[name] = formatter
    
    def register_validator(self, name: str, validator: Callable[[Any], bool]):
        """Register a custom validator"""
        self.validators[name] = validator
    
    def set_global_context(self, context: Dict[str, Any]):
        """Set global context variables"""
        self.global_context.update(context)
    
    def replace_parameters(
        self,
        template: str,
        parameters: Dict[str, Any],
        context: Optional[ReplacementContext] = None
    ) -> str:
        """
        Replace parameters in a template with advanced features
        
        Args:
            template: Template string with parameters
            parameters: Parameters to replace
            context: Replacement context
            
        Returns:
            Template with parameters replaced
        """
        if context is None:
            context = ReplacementContext()
        
        # Extract parameters from template for validation
        template_params = self.extract_parameters(template)
        
        # Merge all available variables
        all_variables = self._merge_variables(parameters, context)
        
        # Validate only parameters that are used in the template
        self._validate_parameters(all_variables, template_params)
        
        # Replace parameters with advanced syntax support
        result = self._replace_advanced_parameters(template, all_variables)
        
        # Handle remaining simple parameters
        result = self._replace_simple_parameters(result, all_variables)
        
        # Replace any remaining placeholders with defaults
        result = self._replace_remaining_placeholders(result)
        
        return result
    
    def _merge_variables(
        self,
        parameters: Dict[str, Any],
        context: ReplacementContext
    ) -> Dict[str, Any]:
        """Merge all available variables"""
        all_variables = {}
        
        # Start with global context
        all_variables.update(self.global_context)
        
        # Add context variables
        all_variables.update({
            'session_id': context.session_id,
            'user_id': context.user_id,
            'timestamp': context.timestamp,
            'step_name': context.step_name,
            'current_date': datetime.now().strftime('%Y-%m-%d'),
            'current_time': datetime.now().strftime('%H:%M:%S'),
            'current_datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        })
        
        # Add previous results
        all_variables.update(context.previous_results)
        
        # Add custom variables
        all_variables.update(context.custom_variables)
        
        # Add provided parameters (highest priority)
        all_variables.update(parameters)
        
        return all_variables
    
    def _validate_parameters(self, parameters: Dict[str, Any], template_params: Optional[List[str]] = None):
        """Validate parameters against their configurations"""
        # Only validate parameters that are actually used in the template
        params_to_validate = template_params if template_params else self.parameter_configs.keys()
        
        for param_name in params_to_validate:
            if param_name not in self.parameter_configs:
                continue  # Skip unknown parameters
                
            config = self.parameter_configs[param_name]
            value = parameters.get(param_name)
            
            # Check required parameters
            if config.required and (value is None or str(value).strip() == ''):
                raise ParameterValidationError(f"Required parameter '{param_name}' is missing or empty")
            
            # Skip validation for None values if not required
            if value is None and not config.required:
                continue
            
            # Apply validator if specified
            if config.validator and not config.validator(value):
                raise ParameterValidationError(f"Parameter '{param_name}' failed validation: {config.description}")
    
    def _replace_advanced_parameters(self, template: str, variables: Dict[str, Any]) -> str:
        """Replace parameters with advanced syntax: {param|formatter|default}"""
        # Pattern to match {param|formatter|default} or {param|formatter} or {param||default}
        # This pattern handles the case where default values can contain braces
        pattern = r'\{([^{}|]+)(?:\|([^|]*?))?(?:\|([^}]*))?\}'
        
        def replace_match(match):
            param_name = match.group(1).strip()
            formatter_name = match.group(2).strip() if match.group(2) is not None else None
            default_value = match.group(3) if match.group(3) is not None else None
            
            # Skip if this is a simple parameter (no | characters)
            if formatter_name is None and default_value is None:
                return match.group(0)  # Return unchanged for simple parameters
            
            # Get the parameter value
            value = variables.get(param_name)
            
            # Use default if value is None or empty
            if value is None or str(value).strip() == '':
                if default_value is not None:
                    value = default_value
                elif param_name in self.parameter_configs:
                    config = self.parameter_configs[param_name]
                    if config.default_value is not None:
                        value = config.default_value
                    else:
                        value = f"[{param_name}]"
                else:
                    value = f"[{param_name}]"
            
            # Apply formatter if specified
            if formatter_name and formatter_name in self.formatters:
                try:
                    value = self.formatters[formatter_name](value)
                except Exception as e:
                    # If formatting fails, use the original value
                    print(f"Warning: Formatter '{formatter_name}' failed for parameter '{param_name}': {e}")
            elif formatter_name and param_name in self.parameter_configs:
                # Try parameter-specific formatter
                config = self.parameter_configs[param_name]
                if config.formatter:
                    try:
                        value = config.formatter(value)
                    except Exception as e:
                        print(f"Warning: Parameter formatter failed for '{param_name}': {e}")
            
            return str(value)
        
        return re.sub(pattern, replace_match, template)
    
    def _replace_simple_parameters(self, template: str, variables: Dict[str, Any]) -> str:
        """Replace simple parameters: {param} (only those without | characters)"""
        # Use regex to find simple parameters (no | characters)
        # This pattern ensures we only match parameters that don't contain |
        simple_pattern = r'\{([^{}|]+)\}'
        
        def replace_simple_match(match):
            full_match = match.group(0)
            param_name = match.group(1).strip()
            
            # Skip if this parameter contains | (it should have been handled by advanced replacement)
            if '|' in full_match:
                return full_match
            
            # Skip if the parameter name contains quotes (likely part of JSON or other formatted content)
            if '"' in param_name or "'" in param_name:
                return full_match
            
            # Only replace if this is actually a parameter we know about or have configured
            if param_name not in variables and param_name not in self.parameter_configs:
                return full_match
            
            value = variables.get(param_name)
            
            if value is None:
                # Use configured default or placeholder
                if param_name in self.parameter_configs:
                    config = self.parameter_configs[param_name]
                    if config.default_value is not None:
                        value = config.default_value
                    else:
                        value = f"[{param_name}]"
                else:
                    value = f"[{param_name}]"
            
            # Apply parameter-specific formatter if configured
            if param_name in self.parameter_configs:
                config = self.parameter_configs[param_name]
                if config.formatter:
                    try:
                        value = config.formatter(value)
                    except Exception as e:
                        print(f"Warning: Parameter formatter failed for '{param_name}': {e}")
            
            # Convert to string - no escaping needed here since we'll handle it differently
            return str(value)
        
        return re.sub(simple_pattern, replace_simple_match, template)
    
    def _replace_remaining_placeholders(self, template: str) -> str:
        """Replace any remaining {param} placeholders with [param]"""
        # Only replace placeholders that look like parameter names (alphanumeric, underscore, no quotes/colons)
        # and are not inside already replaced content
        def replace_placeholder(match):
            param_name = match.group(1)
            # Only replace if this looks like a parameter name and is configured
            if param_name in self.parameter_configs:
                return f'[{param_name}]'
            else:
                # Leave unknown parameters as-is to avoid breaking JSON or other content
                return match.group(0)
        
        return re.sub(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}', replace_placeholder, template)
    
    def extract_parameters(self, template: str) -> List[str]:
        """Extract all parameter names from a template"""
        # Find both simple {param} and advanced {param|formatter|default} patterns
        simple_pattern = r'\{([^{}|]+)\}'
        advanced_pattern = r'\{([^{}|]+)(?:\|[^{}|]*)?(?:\|[^{}]*)?\}'
        
        parameters = set()
        
        # Extract simple parameters
        for match in re.finditer(simple_pattern, template):
            param_name = match.group(1).strip()
            if '|' not in param_name:  # Avoid duplicates with advanced pattern
                parameters.add(param_name)
        
        # Extract advanced parameters
        for match in re.finditer(advanced_pattern, template):
            param_name = match.group(1).strip()
            parameters.add(param_name)
        
        return sorted(list(parameters))
    
    def validate_template(self, template: str) -> Dict[str, Any]:
        """Validate a template and return analysis"""
        parameters = self.extract_parameters(template)
        
        analysis = {
            'parameters_found': parameters,
            'required_parameters': [],
            'optional_parameters': [],
            'unknown_parameters': [],
            'validation_errors': [],
            'suggestions': []
        }
        
        for param in parameters:
            if param in self.parameter_configs:
                config = self.parameter_configs[param]
                if config.required:
                    analysis['required_parameters'].append(param)
                else:
                    analysis['optional_parameters'].append(param)
            else:
                analysis['unknown_parameters'].append(param)
                analysis['suggestions'].append(f"Consider registering configuration for parameter '{param}'")
        
        # Check for potential issues
        if not parameters:
            analysis['suggestions'].append("Template contains no parameters - consider if this is intentional")
        
        if len(analysis['unknown_parameters']) > 0:
            analysis['validation_errors'].append(f"Unknown parameters: {', '.join(analysis['unknown_parameters'])}")
        
        return analysis
    
    def create_parameter_documentation(self) -> str:
        """Create documentation for all registered parameters"""
        if not self.parameter_configs:
            return "No parameters are currently registered."
        
        doc_lines = ["# Template Parameters Documentation\n"]
        
        for name, config in sorted(self.parameter_configs.items()):
            doc_lines.append(f"## {name}")
            doc_lines.append(f"- **Required**: {'Yes' if config.required else 'No'}")
            if config.default_value is not None:
                doc_lines.append(f"- **Default**: `{config.default_value}`")
            if config.description:
                doc_lines.append(f"- **Description**: {config.description}")
            if config.validator:
                doc_lines.append(f"- **Validation**: Custom validator applied")
            if config.formatter:
                doc_lines.append(f"- **Formatting**: Custom formatter applied")
            doc_lines.append("")
        
        # Add available formatters
        doc_lines.append("## Available Formatters\n")
        for name in sorted(self.formatters.keys()):
            doc_lines.append(f"- `{name}`")
        doc_lines.append("")
        
        # Add available validators
        doc_lines.append("## Available Validators\n")
        for name in sorted(self.validators.keys()):
            doc_lines.append(f"- `{name}`")
        
        return '\n'.join(doc_lines)