"""
Tests for the Parameter Replacement System
"""

import pytest
from datetime import datetime
from src.mcps.deep_thinking.templates.parameter_replacer import (
    ParameterReplacer,
    ParameterConfig,
    ReplacementContext,
    ParameterValidationError,
)


class TestParameterReplacer:
    """Test parameter replacement functionality"""

    @pytest.fixture
    def replacer(self):
        """Create a parameter replacer for testing"""
        return ParameterReplacer()

    @pytest.fixture
    def configured_replacer(self):
        """Create a parameter replacer with test configurations"""
        replacer = ParameterReplacer()

        # Register test parameter configurations
        replacer.register_parameter_config(
            ParameterConfig(
                name="required_param",
                required=True,
                formatter=lambda x: str(x).upper(),
                description="A required parameter for testing",
            )
        )

        replacer.register_parameter_config(
            ParameterConfig(
                name="optional_param",
                required=False,
                default_value="default_value",
                description="An optional parameter with default",
            )
        )

        replacer.register_parameter_config(
            ParameterConfig(
                name="formatted_param",
                required=False,
                formatter=lambda x: str(x).upper(),
                description="A parameter with custom formatting",
            )
        )

        replacer.register_parameter_config(
            ParameterConfig(
                name="validated_param",
                required=False,
                validator=lambda x: len(str(x)) >= 3,
                description="A parameter with validation",
            )
        )

        return replacer

    def test_basic_parameter_replacement(self, replacer):
        """Test basic parameter replacement"""
        template = "Hello {name}, welcome to {place}!"
        params = {"name": "Alice", "place": "Wonderland"}

        result = replacer.replace_parameters(template, params)

        assert "Hello Alice, welcome to Wonderland!" == result

    def test_missing_parameter_handling(self, replacer):
        """Test handling of missing parameters"""
        template = "Hello {name}, welcome to {place}!"
        params = {"name": "Alice"}  # Missing 'place'

        result = replacer.replace_parameters(template, params)

        assert "Hello Alice, welcome to [place]!" == result

    def test_none_parameter_handling(self, replacer):
        """Test handling of None parameters"""
        template = "Hello {name}, welcome to {place}!"
        params = {"name": "Alice", "place": None}

        result = replacer.replace_parameters(template, params)

        assert "Hello Alice, welcome to [place]!" == result

    def test_advanced_parameter_syntax(self, replacer):
        """Test advanced parameter syntax with formatters and defaults"""
        template = "Hello {name|upper}, welcome to {place||Wonderland}!"
        params = {"name": "alice"}  # Missing 'place'

        result = replacer.replace_parameters(template, params)

        assert "Hello ALICE, welcome to Wonderland!" == result

    def test_builtin_formatters(self, replacer):
        """Test built-in formatters"""
        template = """
        Upper: {text|upper}
        Lower: {text|lower}
        Title: {text|title}
        List: {items|list}
        JSON: {data|json_compact}
        """

        params = {
            "text": "Hello World",
            "items": ["item1", "item2", "item3"],
            "data": {"key": "value", "number": 42},
        }

        result = replacer.replace_parameters(template, params)

        assert "HELLO WORLD" in result
        assert "hello world" in result
        assert "Hello World" in result
        assert "- item1" in result
        assert "- item2" in result
        assert "- item3" in result
        assert '{"key":"value","number":42}' in result

    def test_context_variables(self, replacer):
        """Test context variable injection"""
        template = "Session: {session_id}, User: {user_id}, Date: {current_date}"
        params = {}
        context = ReplacementContext(session_id="test_session_123", user_id="user_456")

        result = replacer.replace_parameters(template, params, context)

        assert "Session: test_session_123" in result
        assert "User: user_456" in result
        assert "Date:" in result  # Should have current date

    def test_parameter_validation_success(self, configured_replacer):
        """Test successful parameter validation"""
        template = "Required: {required_param}, Validated: {validated_param}"
        params = {"required_param": "test_value", "validated_param": "valid_long_value"}

        result = configured_replacer.replace_parameters(template, params)

        assert "Required: test_value" in result
        assert "Validated: valid_long_value" in result

    def test_parameter_validation_failure(self, configured_replacer):
        """Test parameter validation failure"""
        template = "Required: {required_param}"
        params = {}  # Missing required parameter

        with pytest.raises(ParameterValidationError):
            configured_replacer.replace_parameters(template, params)

    def test_parameter_validation_failure_validator(self, configured_replacer):
        """Test parameter validation failure with custom validator"""
        template = "Validated: {validated_param}"
        params = {"validated_param": "ab"}  # Too short (< 3 chars)

        with pytest.raises(ParameterValidationError):
            configured_replacer.replace_parameters(template, params)

    def test_default_value_usage(self, configured_replacer):
        """Test default value usage"""
        template = "Optional: {optional_param}"
        params = {}  # No optional_param provided

        result = configured_replacer.replace_parameters(template, params)

        assert "Optional: default_value" in result

    def test_custom_formatter_usage(self, configured_replacer):
        """Test custom formatter usage"""
        template = "Formatted: {formatted_param}"
        params = {"formatted_param": "hello world"}

        result = configured_replacer.replace_parameters(template, params)

        assert "Formatted: HELLO WORLD" in result

    def test_parameter_extraction(self, replacer):
        """Test parameter extraction from templates"""
        template = "Hello {name}, welcome to {place|upper||Wonderland}! Today is {current_date}."

        parameters = replacer.extract_parameters(template)

        assert "name" in parameters
        assert "place" in parameters
        assert "current_date" in parameters
        assert len(parameters) == 3

    def test_template_validation(self, configured_replacer):
        """Test template validation"""
        template = "Required: {required_param}, Optional: {optional_param}, Unknown: {unknown_param}"

        analysis = configured_replacer.validate_template(template)

        assert "required_param" in analysis["required_parameters"]
        assert "optional_param" in analysis["optional_parameters"]
        assert "unknown_param" in analysis["unknown_parameters"]
        assert len(analysis["validation_errors"]) > 0

    def test_global_context(self, replacer):
        """Test global context variables"""
        replacer.set_global_context({"global_var": "global_value"})

        template = "Global: {global_var}, Local: {local_var}"
        params = {"local_var": "local_value"}

        result = replacer.replace_parameters(template, params)

        assert "Global: global_value" in result
        assert "Local: local_value" in result

    def test_previous_results_context(self, replacer):
        """Test previous results in context"""
        template = "Previous result: {step1_result}, Current: {current_input}"
        params = {"current_input": "new_data"}
        context = ReplacementContext(
            previous_results={"step1_result": "previous_output"}
        )

        result = replacer.replace_parameters(template, params, context)

        assert "Previous result: previous_output" in result
        assert "Current: new_data" in result

    def test_custom_variables_context(self, replacer):
        """Test custom variables in context"""
        template = "Custom: {custom_var}, Param: {param_var}"
        params = {"param_var": "param_value"}
        context = ReplacementContext(custom_variables={"custom_var": "custom_value"})

        result = replacer.replace_parameters(template, params, context)

        assert "Custom: custom_value" in result
        assert "Param: param_value" in result

    def test_parameter_priority(self, replacer):
        """Test parameter priority (params > custom > previous > global)"""
        replacer.set_global_context({"var": "global"})

        template = "Value: {var}"
        params = {"var": "param"}
        context = ReplacementContext(
            previous_results={"var": "previous"}, custom_variables={"var": "custom"}
        )

        result = replacer.replace_parameters(template, params, context)

        assert "Value: param" in result  # Param should have highest priority

    def test_builtin_validators(self, replacer):
        """Test built-in validators"""
        # Test not_empty validator
        assert replacer.validators["not_empty"]("test") is True
        assert replacer.validators["not_empty"]("") is False
        assert replacer.validators["not_empty"](None) is False

        # Test is_string validator
        assert replacer.validators["is_string"]("test") is True
        assert replacer.validators["is_string"](123) is False

        # Test is_number validator
        assert replacer.validators["is_number"](123) is True
        assert replacer.validators["is_number"](12.34) is True
        assert replacer.validators["is_number"]("123") is False

        # Test is_list validator
        assert replacer.validators["is_list"]([1, 2, 3]) is True
        assert replacer.validators["is_list"]("not a list") is False

        # Test is_dict validator
        assert replacer.validators["is_dict"]({"key": "value"}) is True
        assert replacer.validators["is_dict"]("not a dict") is False

    def test_url_validator(self, replacer):
        """Test URL validator"""
        assert replacer.validators["is_url"]("https://example.com") is True
        assert replacer.validators["is_url"]("http://localhost:8080") is True
        assert replacer.validators["is_url"]("not a url") is False

    def test_email_validator(self, replacer):
        """Test email validator"""
        assert replacer.validators["is_email"]("test@example.com") is True
        assert replacer.validators["is_email"]("user.name+tag@domain.co.uk") is True
        assert replacer.validators["is_email"]("not an email") is False

    def test_json_validator(self, replacer):
        """Test JSON validator"""
        assert replacer.validators["is_json"]('{"key": "value"}') is True
        assert replacer.validators["is_json"]("[1, 2, 3]") is True
        assert replacer.validators["is_json"]("not json") is False

    def test_custom_formatter_registration(self, replacer):
        """Test custom formatter registration"""
        replacer.register_formatter("reverse", lambda x: str(x)[::-1])

        template = "Reversed: {text|reverse}"
        params = {"text": "hello"}

        result = replacer.replace_parameters(template, params)

        assert "Reversed: olleh" in result

    def test_custom_validator_registration(self, replacer):
        """Test custom validator registration"""
        replacer.register_validator(
            "is_even", lambda x: isinstance(x, int) and x % 2 == 0
        )

        config = ParameterConfig(
            name="even_number", validator=replacer.validators["is_even"]
        )
        replacer.register_parameter_config(config)

        template = "Number: {even_number}"

        # Should work with even number
        result = replacer.replace_parameters(template, {"even_number": 4})
        assert "Number: 4" in result

        # Should fail with odd number
        with pytest.raises(ParameterValidationError):
            replacer.replace_parameters(template, {"even_number": 3})

    def test_documentation_generation(self, configured_replacer):
        """Test parameter documentation generation"""
        doc = configured_replacer.create_parameter_documentation()

        assert "required_param" in doc
        assert "optional_param" in doc
        assert "formatted_param" in doc
        assert "validated_param" in doc
        assert "Available Formatters" in doc
        assert "Available Validators" in doc

    def test_complex_template_scenario(self, configured_replacer):
        """Test a complex template scenario"""
        template = """
# Analysis Report

**Topic**: {topic|title}
**Complexity**: {complexity||moderate}
**Generated**: {current_datetime}

## Required Information
- Required Parameter: {required_param}
- Optional Parameter: {optional_param}

## Formatted Data
- Uppercase Text: {text|upper||NO TEXT PROVIDED}
- List Items:
{items|list||No items provided}

## JSON Data
```json
{data|json||{}}
```

## Session Info
- Session ID: {session_id||unknown}
- Step: {step_name||initial}
"""

        params = {
            "topic": "test analysis",
            "required_param": "important_data",
            "text": "sample text",
            "items": ["item1", "item2", "item3"],
            "data": {"result": "success", "count": 42},
        }

        context = ReplacementContext(
            session_id="session_123", step_name="analysis_step"
        )

        result = configured_replacer.replace_parameters(template, params, context)

        # Check various aspects of the result
        assert "Test Analysis" in result  # Title formatting
        assert "moderate" in result  # Default value
        assert "IMPORTANT_DATA" in result  # Required param with formatting
        assert "default_value" in result  # Default from config
        assert "SAMPLE TEXT" in result  # Uppercase formatting
        assert "- item1" in result  # List formatting
        assert "- item2" in result
        assert "- item3" in result
        assert '"result": "success"' in result  # JSON formatting
        assert "session_123" in result  # Context variable
        assert "analysis_step" in result  # Context variable

    def test_error_handling_in_formatters(self, replacer):
        """Test error handling when formatters fail"""
        # Register a formatter that will fail
        replacer.register_formatter(
            "failing_formatter", lambda x: x.nonexistent_method()
        )

        template = "Value: {param|failing_formatter}"
        params = {"param": "test"}

        # Should not raise exception, but use original value
        result = replacer.replace_parameters(template, params)
        assert "Value: test" in result

    def test_nested_parameter_references(self, replacer):
        """Test that nested parameter references are handled correctly"""
        template = "Value: {param1} and {param2}"
        params = {
            "param1": "First: {nested}",  # This should not be processed as a parameter
            "param2": "Second value",
            "nested": "Should not appear",
        }

        result = replacer.replace_parameters(template, params)

        assert "Value: First: {nested} and Second value" in result
        assert "Should not appear" not in result


if __name__ == "__main__":
    pytest.main([__file__])
