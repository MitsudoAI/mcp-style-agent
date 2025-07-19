"""
Tests for the Template Manager
"""

import pytest
import tempfile
import time
from pathlib import Path

from src.mcps.deep_thinking.templates.template_manager import TemplateManager
from src.mcps.deep_thinking.config.exceptions import ConfigurationError


class TestTemplateManager:
    """Test template manager functionality"""
    
    @pytest.fixture
    def temp_template_manager(self):
        """Create a temporary template manager for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TemplateManager(temp_dir)
            yield manager
    
    def test_template_manager_initialization(self, temp_template_manager):
        """Test template manager initialization"""
        manager = temp_template_manager
        
        # Should have built-in templates
        templates = manager.list_templates()
        assert len(templates) > 0
        assert "decomposition" in templates
        assert "evidence_collection" in templates
        assert "critical_evaluation" in templates
    
    def test_template_retrieval_with_parameters(self, temp_template_manager):
        """Test template retrieval with parameter substitution"""
        manager = temp_template_manager
        
        template = manager.get_template("decomposition", {
            "topic": "Test topic",
            "complexity": "moderate",
            "focus": "testing"
        })
        
        assert "Test topic" in template
        assert "moderate" in template
        assert "testing" in template
    
    def test_template_parameter_defaults(self, temp_template_manager):
        """Test template parameter default handling"""
        manager = temp_template_manager
        
        # Missing parameters should get default placeholders
        template = manager.get_template("decomposition", {
            "topic": "Test topic"
            # Missing complexity and focus
        })
        
        assert "Test topic" in template
        assert "[complexity]" in template
        assert "[focus]" in template
    
    def test_template_addition(self, temp_template_manager):
        """Test adding custom templates"""
        manager = temp_template_manager
        
        custom_template = "Custom template: {param1} and {param2}"
        manager.add_template("custom_test", custom_template)
        
        result = manager.get_template("custom_test", {
            "param1": "value1",
            "param2": "value2"
        })
        
        assert "value1" in result
        assert "value2" in result
    
    def test_template_performance(self, temp_template_manager):
        """Test template performance"""
        manager = temp_template_manager
        
        # Test cache performance
        start_time = time.time()
        for _ in range(100):
            manager.get_template("decomposition", {
                "topic": "test",
                "complexity": "simple",
                "focus": ""
            })
        cache_time = time.time() - start_time
        
        # Should be very fast (under 100ms for 100 renders)
        assert cache_time < 0.1
    
    def test_usage_statistics(self, temp_template_manager):
        """Test usage statistics tracking"""
        manager = temp_template_manager
        
        # Use some templates
        for i in range(5):
            manager.get_template("decomposition", {"topic": f"test {i}", "complexity": "simple", "focus": ""})
        
        stats = manager.get_usage_statistics()
        assert stats['total_templates'] > 0
        assert stats['total_usage'] >= 5
    
    def test_missing_template_error(self, temp_template_manager):
        """Test error handling for missing templates"""
        manager = temp_template_manager
        
        with pytest.raises(ConfigurationError):
            manager.get_template("nonexistent_template")
    
    def test_invalid_parameters(self, temp_template_manager):
        """Test handling of invalid parameters"""
        manager = temp_template_manager
        
        # Should handle None parameters gracefully
        result = manager.get_template("decomposition", {
            "topic": None,
            "complexity": "test",
            "focus": ""
        })
        
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__])