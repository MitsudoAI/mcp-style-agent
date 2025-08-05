"""
Tests for Template Manager Parameter Replacement Integration
"""

import tempfile
import pytest
from datetime import datetime

from src.mcps.deep_thinking.templates.template_manager import TemplateManager
from src.mcps.deep_thinking.templates.parameter_replacer import (
    ParameterConfig, 
    ReplacementContext,
    ParameterValidationError
)
from src.mcps.deep_thinking.config.exceptions import ConfigurationError


class TestTemplateManagerParameterReplacement:
    """Test template manager parameter replacement integration"""

    @pytest.fixture
    def temp_template_manager(self):
        """Create a temporary template manager for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TemplateManager(temp_dir)
            yield manager

    def test_basic_parameter_replacement_integration(self, temp_template_manager):
        """Test basic parameter replacement through template manager"""
        manager = temp_template_manager
        
        # Add a test template
        test_template = "Hello {name}, welcome to {place|upper||WONDERLAND}!"
        manager.add_template("greeting", test_template)
        
        # Test with parameters
        result = manager.get_template("greeting", {"name": "Alice", "place": "wonderland"})
        assert "Hello Alice, welcome to WONDERLAND!" == result
        
        # Test with missing parameter
        result = manager.get_template("greeting", {"name": "Bob"})
        assert "Hello Bob, welcome to WONDERLAND!" == result

    def test_context_integration(self, temp_template_manager):
        """Test context integration with template manager"""
        manager = temp_template_manager
        
        # Add a test template with context variables
        test_template = "Session: {session_id}, User: {user_id}, Topic: {topic}, Date: {current_date}"
        manager.add_template("context_test", test_template)
        
        # Create context
        context = ReplacementContext(
            session_id="test_session_123",
            user_id="user_456"
        )
        
        # Test with context
        result = manager.get_template(
            "context_test", 
            {"topic": "AI Research"}, 
            context=context
        )
        
        assert "Session: test_session_123" in result
        assert "User: user_456" in result
        assert "Topic: AI Research" in result
        assert "Date:" in result  # Should have current date

    def test_parameter_config_registration(self, temp_template_manager):
        """Test parameter configuration registration"""
        manager = temp_template_manager
        
        # Register a custom parameter config
        config = ParameterConfig(
            name="custom_param",
            required=True,
            validator=lambda x: len(str(x)) >= 5,
            formatter=lambda x: f"CUSTOM: {str(x).upper()}",
            description="A custom parameter for testing"
        )
        manager.register_parameter_config(config)
        
        # Add a template using the custom parameter
        test_template = "Value: {custom_param}"
        manager.add_template("custom_test", test_template)
        
        # Test with valid parameter
        result = manager.get_template("custom_test", {"custom_param": "valid_value"})
        assert "Value: CUSTOM: VALID_VALUE" in result
        
        # Test with invalid parameter (should fall back to basic replacement)
        result = manager.get_template("custom_test", {"custom_param": "bad"})
        # Should still work but might show validation warning
        assert "Value:" in result

    def test_custom_formatter_registration(self, temp_template_manager):
        """Test custom formatter registration"""
        manager = temp_template_manager
        
        # Register a custom formatter
        manager.register_formatter("reverse", lambda x: str(x)[::-1])
        
        # Add a template using the custom formatter
        test_template = "Original: {text}, Reversed: {text|reverse}"
        manager.add_template("formatter_test", test_template)
        
        # Test the formatter
        result = manager.get_template("formatter_test", {"text": "hello"})
        assert "Original: hello, Reversed: olleh" in result

    def test_custom_validator_registration(self, temp_template_manager):
        """Test custom validator registration"""
        manager = temp_template_manager
        
        # Register a custom validator
        manager.register_validator("is_positive", lambda x: isinstance(x, (int, float)) and x > 0)
        
        # Register parameter config with custom validator
        config = ParameterConfig(
            name="positive_number",
            validator=manager.parameter_replacer.validators['is_positive']
        )
        manager.register_parameter_config(config)
        
        # Add a template
        test_template = "Number: {positive_number}"
        manager.add_template("validator_test", test_template)
        
        # Test with valid value
        result = manager.get_template("validator_test", {"positive_number": 42})
        assert "Number: 42" in result
        
        # Test with invalid value (should fall back gracefully)
        result = manager.get_template("validator_test", {"positive_number": -5})
        assert "Number:" in result

    def test_global_context_setting(self, temp_template_manager):
        """Test global context setting"""
        manager = temp_template_manager
        
        # Set global context
        manager.set_global_context({
            "app_name": "Deep Thinking Engine",
            "version": "1.0.0"
        })
        
        # Add a template using global context
        test_template = "Welcome to {app_name} v{version}! Topic: {topic}"
        manager.add_template("global_test", test_template)
        
        # Test global context usage
        result = manager.get_template("global_test", {"topic": "Testing"})
        assert "Welcome to Deep Thinking Engine v1.0.0! Topic: Testing" in result

    def test_parameter_extraction(self, temp_template_manager):
        """Test parameter extraction from templates"""
        manager = temp_template_manager
        
        # Add a template with various parameters
        test_template = "Hello {name}, welcome to {place|upper||DEFAULT}! Today is {current_date}."
        manager.add_template("extraction_test", test_template)
        
        # Extract parameters
        parameters = manager.extract_template_parameters("extraction_test")
        
        assert "name" in parameters
        assert "place" in parameters
        assert "current_date" in parameters
        assert len(parameters) == 3

    def test_template_validation(self, temp_template_manager):
        """Test template validation"""
        manager = temp_template_manager
        
        # Add a template with various parameter types
        test_template = "Required: {topic}, Optional: {complexity}, Unknown: {mystery_param}"
        manager.add_template("validation_test", test_template)
        
        # Validate the template
        analysis = manager.validate_template("validation_test")
        
        assert "topic" in analysis['required_parameters']
        assert "complexity" in analysis['optional_parameters']
        assert "mystery_param" in analysis['unknown_parameters']
        assert len(analysis['validation_errors']) > 0

    def test_parameter_replacement_testing(self, temp_template_manager):
        """Test parameter replacement testing functionality"""
        manager = temp_template_manager
        
        # Add a test template
        test_template = "Topic: {topic}, Complexity: {complexity||moderate}, Focus: {focus}"
        manager.add_template("replacement_test", test_template)
        
        # Test parameter replacement
        test_result = manager.test_parameter_replacement(
            "replacement_test",
            {"topic": "AI Ethics", "focus": "bias detection"}
        )
        
        assert test_result['template_name'] == "replacement_test"
        assert "topic" in test_result['template_parameters']
        assert "complexity" in test_result['template_parameters']
        assert "focus" in test_result['template_parameters']
        assert "topic" in test_result['provided_parameters']
        assert "focus" in test_result['provided_parameters']
        assert "complexity" not in test_result['missing_parameters']  # Has default
        assert test_result['replacement_success'] is True
        assert "AI Ethics" in test_result['result']
        assert "moderate" in test_result['result']  # Default value
        assert "bias detection" in test_result['result']

    def test_parameter_documentation_generation(self, temp_template_manager):
        """Test parameter documentation generation"""
        manager = temp_template_manager
        
        # Get parameter documentation
        doc = manager.get_parameter_documentation()
        
        # Should contain built-in parameters
        assert "topic" in doc
        assert "complexity" in doc
        assert "focus" in doc
        assert "Available Formatters" in doc
        assert "Available Validators" in doc

    def test_builtin_template_parameter_replacement(self, temp_template_manager):
        """Test parameter replacement with built-in templates"""
        manager = temp_template_manager
        
        # Test decomposition template
        result = manager.get_template(
            "decomposition",
            {
                "topic": "Climate Change Solutions",
                "complexity": "high",
                "focus": "renewable energy",
                "domain_context": "environmental science"
            }
        )
        
        assert "Climate Change Solutions" in result
        assert "high" in result
        assert "renewable energy" in result
        assert "environmental science" in result

    def test_evidence_collection_template_parameters(self, temp_template_manager):
        """Test evidence collection template parameter replacement"""
        manager = temp_template_manager
        
        # Test evidence collection template
        result = manager.get_template(
            "evidence_collection",
            {
                "sub_question": "What are the most effective renewable energy sources?",
                "keywords": ["solar power", "wind energy", "hydroelectric"],
                "complexity": "moderate"
            }
        )
        
        assert "What are the most effective renewable energy sources?" in result
        assert "solar power, wind energy, hydroelectric" in result
        assert "moderate" in result

    def test_context_with_previous_results(self, temp_template_manager):
        """Test context with previous results"""
        manager = temp_template_manager
        
        # Add a template that uses previous results
        test_template = """
Based on previous analysis: {step1_result}
Current question: {current_question}
Session: {session_id}
"""
        manager.add_template("context_previous", test_template)
        
        # Create context with previous results
        context = ReplacementContext(
            session_id="session_789",
            previous_results={
                "step1_result": "Initial analysis shows promising results"
            }
        )
        
        # Test with context
        result = manager.get_template(
            "context_previous",
            {"current_question": "What are the next steps?"},
            context=context
        )
        
        assert "Initial analysis shows promising results" in result
        assert "What are the next steps?" in result
        assert "session_789" in result

    def test_complex_formatting_scenario(self, temp_template_manager):
        """Test complex formatting scenario"""
        manager = temp_template_manager
        
        # Add a template with complex formatting
        test_template = """
# {title|title}

## Data Summary
- Items: {items|numbered_list}
- JSON Data: {data|json}
- Truncated Text: {long_text|truncate}

## Metadata
- Generated: {current_datetime}
- Session: {session_id||unknown}
"""
        manager.add_template("complex_format", test_template)
        
        # Test with complex data
        params = {
            "title": "analysis report",
            "items": ["Finding 1", "Finding 2", "Finding 3"],
            "data": {"status": "complete", "score": 85.5},
            "long_text": "This is a very long text that should be truncated because it exceeds the maximum length limit set by the truncate formatter and will show ellipsis at the end."
        }
        
        context = ReplacementContext(session_id="complex_session")
        
        result = manager.get_template("complex_format", params, context)
        
        assert "Analysis Report" in result  # Title case
        assert "1. Finding 1" in result  # Numbered list
        assert "2. Finding 2" in result
        assert "3. Finding 3" in result
        assert '"status": "complete"' in result  # JSON formatting
        assert '"score": 85.5' in result
        assert "..." in result  # Truncated text
        assert "complex_session" in result

    def test_error_handling_with_validation_errors(self, temp_template_manager):
        """Test error handling when validation fails"""
        manager = temp_template_manager
        
        # Register a strict parameter config
        config = ParameterConfig(
            name="strict_param",
            required=True,
            validator=lambda x: len(str(x)) >= 10,
            description="A parameter that requires at least 10 characters"
        )
        manager.register_parameter_config(config)
        
        # Add a template
        test_template = "Strict: {strict_param}"
        manager.add_template("strict_test", test_template)
        
        # Test with invalid parameter (should fall back gracefully)
        result = manager.get_template("strict_test", {"strict_param": "short"})
        
        # Should still return a result (fallback to basic replacement)
        assert "Strict: short" in result

    def test_missing_template_with_parameter_replacement(self, temp_template_manager):
        """Test missing template handling with parameter replacement"""
        manager = temp_template_manager
        
        # Test missing template with default fallback
        result = manager.get_template(
            "nonexistent_template",
            {"param": "value"},
            use_default_if_missing=True
        )
        
        assert "Template not found: nonexistent_template" in result
        
        # Test missing template without fallback
        with pytest.raises(ConfigurationError):
            manager.get_template("nonexistent_template", {"param": "value"})


if __name__ == "__main__":
    pytest.main([__file__])