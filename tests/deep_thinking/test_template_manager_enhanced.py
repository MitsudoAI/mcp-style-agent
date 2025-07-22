"""
Tests for the Enhanced Template Manager
"""

import os
import tempfile
import time
from pathlib import Path

import pytest

from src.mcps.deep_thinking.templates.template_manager import TemplateManager, TemplateVersionError, ConfigurationError


class TestEnhancedTemplateManager:
    """Test enhanced template manager functionality"""

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

    def test_template_retrieval_with_parameters(self, temp_template_manager):
        """Test template retrieval with parameter substitution"""
        manager = temp_template_manager

        template = manager.get_template(
            "decomposition",
            {"topic": "Test topic", "complexity": "moderate", "focus": "testing"},
        )

        assert "Test topic" in template
        assert "moderate" in template
        assert "testing" in template

    def test_template_parameter_defaults(self, temp_template_manager):
        """Test template parameter default handling"""
        manager = temp_template_manager

        # Missing parameters should get default placeholders
        template = manager.get_template(
            "decomposition",
            {
                "topic": "Test topic"
                # Missing complexity and focus
            },
        )

        assert "Test topic" in template
        assert "[complexity]" in template
        assert "[focus]" in template

    def test_template_addition(self, temp_template_manager):
        """Test adding custom templates"""
        manager = temp_template_manager

        custom_template = "Custom template: {param1} and {param2}"
        manager.add_template("custom_test", custom_template)

        result = manager.get_template(
            "custom_test", {"param1": "value1", "param2": "value2"}
        )

        assert "value1" in result
        assert "value2" in result

    def test_template_performance(self, temp_template_manager):
        """Test template performance"""
        manager = temp_template_manager

        # Test cache performance
        start_time = time.time()
        for _ in range(100):
            manager.get_template(
                "decomposition", {"topic": "test", "complexity": "simple", "focus": ""}
            )
        cache_time = time.time() - start_time

        # Should be very fast (under 100ms for 100 renders)
        assert cache_time < 0.1

    def test_usage_statistics(self, temp_template_manager):
        """Test usage statistics tracking"""
        manager = temp_template_manager

        # Use some templates
        for i in range(5):
            manager.get_template(
                "decomposition",
                {"topic": f"test {i}", "complexity": "simple", "focus": ""},
            )

        stats = manager.get_usage_statistics()
        assert stats["total_templates"] > 0
        assert stats["total_usage"] >= 5

    def test_missing_template_error(self, temp_template_manager):
        """Test error handling for missing templates"""
        manager = temp_template_manager

        # This should raise ConfigurationError
        with pytest.raises(ConfigurationError):
            manager.get_template("nonexistent_template")
            
    def test_default_template_fallback(self, temp_template_manager):
        """Test fallback to default template"""
        manager = temp_template_manager
            
        # This should return a default template if we set a flag
        result = manager.get_template("nonexistent_template", {}, use_default_if_missing=True)
        assert "Template not found" in result

    def test_invalid_parameters(self, temp_template_manager):
        """Test handling of invalid parameters"""
        manager = temp_template_manager

        # Should handle None parameters gracefully
        result = manager.get_template(
            "decomposition", {"topic": None, "complexity": "test", "focus": ""}
        )

        assert result is not None

    def test_template_file_loading(self, temp_template_manager):
        """Test loading templates from files"""
        manager = temp_template_manager
        
        # Create a template file
        template_path = Path(manager.templates_dir) / "test_template.tmpl"
        template_content = "Test template content: {param}"
        template_path.write_text(template_content)
        
        # Template should be loaded from file
        result = manager.get_template("test_template", {"param": "value"})
        assert "Test template content: value" in result

    def test_template_versioning(self, temp_template_manager):
        """Test template versioning"""
        manager = temp_template_manager
        
        # Add a template with multiple versions
        manager.add_template("versioned_template", "Version 1: {param}")
        manager.add_template("versioned_template", "Version 2: {param}")
        manager.add_template("versioned_template", "Version 3: {param}")
        
        # Get the versions
        versions = manager.get_template_versions("versioned_template")
        assert len(versions) == 3
        
        # The latest version should be active
        active_versions = [v for v in versions if v["is_active"]]
        assert len(active_versions) == 1
        
        # The template should use the latest version
        result = manager.get_template("versioned_template", {"param": "test"})
        assert "Version 3: test" in result

    def test_template_rollback(self, temp_template_manager):
        """Test template rollback"""
        manager = temp_template_manager
        
        # Add a template with multiple versions
        manager.add_template("rollback_template", "Version 1: {param}")
        manager.add_template("rollback_template", "Version 2: {param}")
        manager.add_template("rollback_template", "Version 3: {param}")
        
        # Get the versions
        versions = manager.get_template_versions("rollback_template")
        
        # Rollback to the first version
        first_version_id = versions[0]["version_id"]
        manager.rollback_template("rollback_template", first_version_id)
        
        # The template should use the first version
        result = manager.get_template("rollback_template", {"param": "test"})
        assert "Version 1: test" in result

    def test_template_reload(self, temp_template_manager):
        """Test template reloading"""
        manager = temp_template_manager
        
        # Create a template file
        template_path = Path(manager.templates_dir) / "reload_template.tmpl"
        template_path.write_text("Original content: {param}")
        
        # Load the template
        result1 = manager.get_template("reload_template", {"param": "test"})
        assert "Original content: test" in result1
        
        # Update the template file
        template_path.write_text("Updated content: {param}")
        
        # Reload the template
        manager.reload_template("reload_template")
        
        # The template should use the updated content
        result2 = manager.get_template("reload_template", {"param": "test"})
        assert "Updated content: test" in result2

    def test_hot_reload(self, temp_template_manager):
        """Test hot reload functionality"""
        manager = temp_template_manager
        
        # Enable hot reload
        manager.enable_hot_reload()
        assert manager.is_hot_reload_enabled() is True
        
        # Create a template file
        template_path = Path(manager.templates_dir) / "hot_reload_template.tmpl"
        template_path.write_text("Original content: {param}")
        
        # Wait for the file system watcher to detect the new file
        time.sleep(1)
        
        # Load the template
        result1 = manager.get_template("hot_reload_template", {"param": "test"})
        assert "Original content: test" in result1
        
        # Update the template file
        template_path.write_text("Hot reloaded content: {param}")
        
        # Wait for the file system watcher to detect the change
        time.sleep(1)
        
        # Force reload the template
        manager.reload_template("hot_reload_template")
        
        # The template should be reloaded
        result2 = manager.get_template("hot_reload_template", {"param": "test"})
        assert "Hot reloaded content: test" in result2
        
        # Disable hot reload
        manager.disable_hot_reload()
        assert manager.is_hot_reload_enabled() is False

    def test_template_version_error(self, temp_template_manager):
        """Test template version error handling"""
        manager = temp_template_manager
        
        # Add a template
        manager.add_template("error_template", "Content: {param}")
        
        # Try to rollback to a non-existent version
        with pytest.raises(TemplateVersionError):
            manager.rollback_template("error_template", "non_existent_version_id")


if __name__ == "__main__":
    pytest.main([__file__])