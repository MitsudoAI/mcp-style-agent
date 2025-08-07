"""
Integration tests for template performance optimization
"""

import pytest
import tempfile
import time
from pathlib import Path

from src.mcps.deep_thinking.templates.template_manager import TemplateManager


class TestTemplatePerformanceIntegration:
    """Integration tests for template performance optimization"""
    
    @pytest.fixture
    def temp_templates_dir(self):
        """Create temporary templates directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            templates_dir = Path(temp_dir)
            
            # Create sample template files
            (templates_dir / "test_template.tmpl").write_text("Test template: {param}")
            (templates_dir / "popular_template.tmpl").write_text("Popular template: {value}")
            (templates_dir / "complex_template.tmpl").write_text(
                "Complex template with {param1} and {param2} and {param3}"
            )
            
            yield str(templates_dir)
    
    def test_template_manager_with_performance_optimization(self, temp_templates_dir):
        """Test template manager with performance optimization enabled"""
        # Create template manager with performance optimization
        manager = TemplateManager(temp_templates_dir, enable_performance_optimization=True)
        
        try:
            # Test basic template retrieval
            template = manager.get_template("test_template", {"param": "value"})
            assert template == "Test template: value"
            
            # Test performance metrics
            metrics = manager.get_performance_metrics()
            assert "template_manager_stats" in metrics
            assert "cache_metrics" in metrics
            assert "usage_stats" in metrics
            
            # Test cache hit on second access
            template2 = manager.get_template("test_template", {"param": "value2"})
            assert template2 == "Test template: value2"
            
            # Check that cache hit rate improved
            metrics2 = manager.get_performance_metrics()
            assert metrics2["cache_metrics"]["total_requests"] > metrics["cache_metrics"]["total_requests"]
            
        finally:
            manager.shutdown()
    
    def test_template_manager_without_performance_optimization(self, temp_templates_dir):
        """Test template manager without performance optimization"""
        # Create template manager without performance optimization
        manager = TemplateManager(temp_templates_dir, enable_performance_optimization=False)
        
        try:
            # Test basic template retrieval
            template = manager.get_template("test_template", {"param": "value"})
            assert template == "Test template: value"
            
            # Test performance metrics (should have limited info)
            metrics = manager.get_performance_metrics()
            assert "template_manager_stats" in metrics
            assert "cache_metrics" not in metrics  # No optimizer metrics
            
        finally:
            manager.shutdown()
    
    def test_preload_templates(self, temp_templates_dir):
        """Test template preloading functionality"""
        manager = TemplateManager(temp_templates_dir, enable_performance_optimization=True)
        
        try:
            # Preload specific templates
            results = manager.preload_templates(["test_template", "popular_template"])
            assert "test_template" in results
            assert "popular_template" in results
            assert results["test_template"] is True
            assert results["popular_template"] is True
            
            # Check that templates are now in cache
            metrics = manager.get_performance_metrics()
            assert metrics["cache_metrics"]["cache_size"] >= 2
            
        finally:
            manager.shutdown()
    
    def test_performance_optimization_methods(self, temp_templates_dir):
        """Test performance optimization methods"""
        manager = TemplateManager(temp_templates_dir, enable_performance_optimization=True)
        
        try:
            # Generate some usage patterns
            for _ in range(5):
                manager.get_template("popular_template", {"value": "test"})
            
            # Test optimization
            manager.optimize_performance()
            
            # Test cache clearing
            manager.clear_performance_cache()
            metrics = manager.get_performance_metrics()
            assert metrics["cache_metrics"]["cache_size"] == 0
            
            # Test statistics reset
            manager.reset_performance_statistics()
            metrics = manager.get_performance_metrics()
            assert metrics["cache_metrics"]["total_requests"] == 0
            
        finally:
            manager.shutdown()
    
    def test_performance_under_load(self, temp_templates_dir):
        """Test performance under simulated load"""
        manager = TemplateManager(temp_templates_dir, enable_performance_optimization=True)
        
        try:
            # Simulate load with repeated template access
            start_time = time.time()
            
            for i in range(100):
                template_name = f"template_{i % 3}"  # Rotate between 3 templates
                if template_name == "template_0":
                    template_name = "test_template"
                elif template_name == "template_1":
                    template_name = "popular_template"
                else:
                    template_name = "complex_template"
                
                try:
                    manager.get_template(template_name, {"param1": f"value{i}", "param2": "test", "param3": "data"})
                except Exception:
                    # Some templates might not exist, that's ok for this test
                    pass
            
            total_time = time.time() - start_time
            
            # Check performance metrics
            metrics = manager.get_performance_metrics()
            hit_rate = metrics["cache_metrics"]["hit_rate"]
            
            # Should have reasonable performance
            assert total_time < 5.0  # Should complete within 5 seconds
            assert hit_rate > 0.5    # Should have good cache hit rate
            
        finally:
            manager.shutdown()
    
    def test_memory_monitoring(self, temp_templates_dir):
        """Test memory monitoring functionality"""
        manager = TemplateManager(temp_templates_dir, enable_performance_optimization=True)
        
        try:
            # Generate some activity to trigger memory monitoring
            for i in range(10):
                manager.get_template("test_template", {"param": f"value{i}"})
            
            # Check memory stats
            metrics = manager.get_performance_metrics()
            memory_stats = metrics.get("memory_stats", {})
            
            # Should have memory monitoring data
            assert "current_usage_mb" in memory_stats
            assert "peak_usage_mb" in memory_stats
            assert memory_stats["current_usage_mb"] >= 0
            
        finally:
            manager.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])