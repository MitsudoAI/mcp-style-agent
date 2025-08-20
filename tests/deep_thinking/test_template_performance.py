"""
Template Performance Optimization Tests

Tests for template preloading, caching strategies, memory monitoring,
and performance optimization features.
"""

import pytest
import tempfile
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch

from src.mcps.deep_thinking.templates.performance_optimizer import (
    TemplatePerformanceOptimizer,
    LRUCache,
    TemplatePreloader,
    MemoryMonitor,
    TemplateUsageStats,
    CacheMetrics,
)


class TestLRUCache:
    """Test LRU cache implementation"""

    def test_basic_operations(self):
        """Test basic cache operations"""
        cache = LRUCache(max_size=3, max_memory_mb=1)

        # Test put and get
        assert cache.put("key1", "value1") is True
        assert cache.get("key1") == "value1"
        assert cache.get("nonexistent") is None

        # Test size tracking
        assert cache.size() == 1
        assert cache.memory_size() > 0

    def test_lru_eviction(self):
        """Test LRU eviction policy"""
        cache = LRUCache(max_size=2, max_memory_mb=1)

        # Fill cache
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        assert cache.size() == 2

        # Access key1 to make it recently used
        cache.get("key1")

        # Add key3, should evict key2 (least recently used)
        cache.put("key3", "value3")
        assert cache.size() == 2
        assert cache.get("key1") == "value1"  # Still there
        assert cache.get("key2") is None  # Evicted
        assert cache.get("key3") == "value3"  # New item

    def test_memory_limit_eviction(self):
        """Test eviction based on memory limits"""
        # Very small memory limit to force eviction
        cache = LRUCache(max_size=10, max_memory_mb=0.001)  # 1KB limit

        # Add large content that exceeds memory limit
        large_content = "x" * 2000  # 2KB content
        cache.put("large", large_content)

        # Should still work but may evict other items
        assert cache.get("large") == large_content

    def test_update_existing_key(self):
        """Test updating existing cache key"""
        cache = LRUCache(max_size=3, max_memory_mb=1)

        cache.put("key1", "value1")
        original_memory = cache.memory_size()

        # Update with different value
        cache.put("key1", "updated_value")
        assert cache.get("key1") == "updated_value"
        assert cache.size() == 1

        # Memory usage should be updated
        new_memory = cache.memory_size()
        assert new_memory != original_memory

    def test_clear_cache(self):
        """Test cache clearing"""
        cache = LRUCache(max_size=3, max_memory_mb=1)

        cache.put("key1", "value1")
        cache.put("key2", "value2")
        assert cache.size() == 2

        cache.clear()
        assert cache.size() == 0
        assert cache.memory_size() == 0
        assert cache.get("key1") is None


class TestTemplatePreloader:
    """Test template preloading functionality"""

    @pytest.fixture
    def temp_templates_dir(self):
        """Create temporary templates directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            templates_dir = Path(temp_dir)

            # Create sample template files
            (templates_dir / "template1.tmpl").write_text("Template 1 content")
            (templates_dir / "template2.tmpl").write_text("Template 2 content")
            (templates_dir / "template3.tmpl").write_text("Template 3 content")

            yield templates_dir

    def test_discover_templates(self, temp_templates_dir):
        """Test template discovery"""
        cache = LRUCache(max_size=10, max_memory_mb=1)
        preloader = TemplatePreloader(temp_templates_dir, cache)

        templates = preloader._discover_templates()
        assert len(templates) == 3
        assert "template1" in templates
        assert "template2" in templates
        assert "template3" in templates

    def test_preload_single_template(self, temp_templates_dir):
        """Test preloading a single template"""
        cache = LRUCache(max_size=10, max_memory_mb=1)
        preloader = TemplatePreloader(temp_templates_dir, cache)

        # Preload single template
        success = preloader._preload_single_template("template1")
        assert success is True

        # Check if template is in cache
        assert cache.get("template1") == "Template 1 content"

    def test_preload_all_templates(self, temp_templates_dir):
        """Test preloading all templates"""
        cache = LRUCache(max_size=10, max_memory_mb=1)
        preloader = TemplatePreloader(temp_templates_dir, cache)

        # Preload all templates
        results = preloader.preload_templates()

        assert len(results) == 3
        assert all(results.values())  # All should succeed

        # Check cache contents
        assert cache.get("template1") == "Template 1 content"
        assert cache.get("template2") == "Template 2 content"
        assert cache.get("template3") == "Template 3 content"

    def test_preload_specific_templates(self, temp_templates_dir):
        """Test preloading specific templates"""
        cache = LRUCache(max_size=10, max_memory_mb=1)
        preloader = TemplatePreloader(temp_templates_dir, cache)

        # Preload specific templates
        results = preloader.preload_templates(["template1", "template3"])

        assert len(results) == 2
        assert results["template1"] is True
        assert results["template3"] is True

        # Check cache contents
        assert cache.get("template1") == "Template 1 content"
        assert cache.get("template2") is None  # Not preloaded
        assert cache.get("template3") == "Template 3 content"

    def test_preload_nonexistent_template(self, temp_templates_dir):
        """Test preloading nonexistent template"""
        cache = LRUCache(max_size=10, max_memory_mb=1)
        preloader = TemplatePreloader(temp_templates_dir, cache)

        success = preloader._preload_single_template("nonexistent")
        assert success is False

    def test_preload_stats(self, temp_templates_dir):
        """Test preload statistics tracking"""
        cache = LRUCache(max_size=10, max_memory_mb=1)
        preloader = TemplatePreloader(temp_templates_dir, cache)

        # Initial stats should be empty
        stats = preloader.get_preload_stats()
        assert stats == {}

        # Preload templates
        preloader.preload_templates(["template1", "template2"])

        # Check stats
        stats = preloader.get_preload_stats()
        assert "last_preload_time" in stats
        assert "preload_duration" in stats
        assert stats["templates_attempted"] == 2
        assert stats["templates_successful"] == 2
        assert stats["success_rate"] == 1.0


class TestMemoryMonitor:
    """Test memory monitoring functionality"""

    def test_memory_stats_initialization(self):
        """Test memory stats initialization"""
        monitor = MemoryMonitor()

        stats = monitor.get_memory_stats()
        assert "peak_usage" in stats
        assert "current_usage" in stats
        assert "cleanup_count" in stats
        assert stats["cleanup_count"] == 0

    def test_cleanup_callback_registration(self):
        """Test cleanup callback registration"""
        monitor = MemoryMonitor()
        callback_called = False

        def test_callback(aggressive):
            nonlocal callback_called
            callback_called = True

        monitor.add_cleanup_callback(test_callback)
        monitor._trigger_cleanup()

        assert callback_called is True

    def test_memory_usage_tracking(self):
        """Test memory usage tracking"""
        monitor = MemoryMonitor()

        # Get initial memory usage
        usage = monitor._get_memory_usage()
        assert usage >= 0  # Should be non-negative

    @patch("psutil.Process")
    def test_memory_monitoring_with_mock(self, mock_process):
        """Test memory monitoring with mocked psutil"""
        # Mock memory info
        mock_memory_info = Mock()
        mock_memory_info.rss = 50 * 1024 * 1024  # 50MB
        mock_process.return_value.memory_info.return_value = mock_memory_info

        monitor = MemoryMonitor(warning_threshold_mb=40, critical_threshold_mb=60)

        # Test memory usage retrieval
        usage = monitor._get_memory_usage()
        assert usage == 50 * 1024 * 1024

    def test_cleanup_trigger(self):
        """Test cleanup triggering"""
        monitor = MemoryMonitor()
        cleanup_calls = []

        def test_callback(aggressive):
            cleanup_calls.append(aggressive)

        monitor.add_cleanup_callback(test_callback)

        # Trigger normal cleanup
        monitor._trigger_cleanup(aggressive=False)
        assert len(cleanup_calls) == 1
        assert cleanup_calls[0] is False

        # Trigger aggressive cleanup
        monitor._trigger_cleanup(aggressive=True)
        assert len(cleanup_calls) == 2
        assert cleanup_calls[1] is True

        # Check stats
        stats = monitor.get_memory_stats()
        assert stats["cleanup_count"] == 2


class TestTemplatePerformanceOptimizer:
    """Test main performance optimizer"""

    @pytest.fixture
    def temp_templates_dir(self):
        """Create temporary templates directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            templates_dir = Path(temp_dir)

            # Create sample template files
            (templates_dir / "template1.tmpl").write_text("Template 1: {param1}")
            (templates_dir / "template2.tmpl").write_text("Template 2: {param2}")
            (templates_dir / "high_priority.tmpl").write_text("High priority template")

            yield templates_dir

    def test_optimizer_initialization(self, temp_templates_dir):
        """Test optimizer initialization"""
        optimizer = TemplatePerformanceOptimizer(temp_templates_dir)

        assert optimizer.templates_dir == temp_templates_dir
        assert optimizer.cache is not None
        assert optimizer.preloader is not None
        assert optimizer.memory_monitor is not None

        # Cleanup
        optimizer.shutdown()

    def test_get_template_with_cache_hit(self, temp_templates_dir):
        """Test template retrieval with cache hit"""
        optimizer = TemplatePerformanceOptimizer(temp_templates_dir)

        # Mock load function
        def mock_load_func(name):
            return f"Loaded template: {name}"

        # First call - cache miss
        content1 = optimizer.get_template("test_template", mock_load_func)
        assert content1 == "Loaded template: test_template"

        # Second call - cache hit
        content2 = optimizer.get_template("test_template", mock_load_func)
        assert content2 == "Loaded template: test_template"

        # Check metrics
        metrics = optimizer.get_performance_metrics()
        assert metrics["cache_metrics"]["total_requests"] == 2
        assert metrics["cache_metrics"]["cache_hits"] == 1
        assert metrics["cache_metrics"]["cache_misses"] == 1
        assert metrics["cache_metrics"]["hit_rate"] == 0.5

        # Cleanup
        optimizer.shutdown()

    def test_usage_statistics_tracking(self, temp_templates_dir):
        """Test usage statistics tracking"""
        optimizer = TemplatePerformanceOptimizer(temp_templates_dir)

        def mock_load_func(name):
            return f"Content for {name}"

        # Access template multiple times
        for _ in range(3):
            optimizer.get_template("popular_template", mock_load_func)

        # Check usage stats
        metrics = optimizer.get_performance_metrics()
        usage_stats = metrics["usage_stats"]

        assert "popular_template" in usage_stats
        stats = usage_stats["popular_template"]
        assert stats["access_count"] == 3
        assert stats["cache_hits"] == 2  # First miss, then 2 hits
        assert stats["cache_misses"] == 1
        assert stats["priority_score"] > 0

        # Cleanup
        optimizer.shutdown()

    def test_priority_score_calculation(self, temp_templates_dir):
        """Test priority score calculation"""
        optimizer = TemplatePerformanceOptimizer(temp_templates_dir)

        # Create usage stats
        stats = TemplateUsageStats("test_template")
        stats.access_count = 10
        stats.cache_hits = 8
        stats.cache_misses = 2

        # Calculate priority score
        priority = optimizer._calculate_priority_score(stats)
        assert 0 <= priority <= 1
        assert priority > 0  # Should have some priority

    def test_cache_optimization(self, temp_templates_dir):
        """Test cache optimization"""
        optimizer = TemplatePerformanceOptimizer(temp_templates_dir, cache_size=2)

        def mock_load_func(name):
            return f"Content for {name}"

        # Fill cache and create usage patterns
        optimizer.get_template("high_usage", mock_load_func)
        optimizer.get_template("low_usage", mock_load_func)

        # Simulate different usage patterns
        for _ in range(10):
            optimizer.get_template("high_usage", mock_load_func)

        # Only access low_usage once (already done above)

        # Run optimization
        optimizer.optimize_cache()

        # High usage template should still be in cache
        assert optimizer.cache.get("high_usage") is not None

        # Cleanup
        optimizer.shutdown()

    def test_preload_high_priority_templates(self, temp_templates_dir):
        """Test preloading high-priority templates"""
        optimizer = TemplatePerformanceOptimizer(temp_templates_dir)

        def mock_load_func(name):
            return (temp_templates_dir / f"{name}.tmpl").read_text()

        # Create usage patterns
        for _ in range(5):
            optimizer.get_template("high_priority", mock_load_func)

        # Preload high priority templates
        results = optimizer.preload_high_priority_templates(max_templates=2)

        # Should include high_priority template
        assert "high_priority" in results
        assert results["high_priority"] is True

        # Cleanup
        optimizer.shutdown()

    def test_memory_cleanup_callback(self, temp_templates_dir):
        """Test memory cleanup callback"""
        optimizer = TemplatePerformanceOptimizer(temp_templates_dir, cache_size=4)

        def mock_load_func(name):
            return f"Content for {name}"

        # Fill cache with templates
        for i in range(4):
            optimizer.get_template(f"template_{i}", mock_load_func)

        initial_size = optimizer.cache.size()
        assert initial_size == 4

        # Trigger aggressive cleanup
        optimizer._memory_cleanup_callback(aggressive=True)

        # Cache should be smaller
        final_size = optimizer.cache.size()
        assert final_size < initial_size

        # Cleanup
        optimizer.shutdown()

    def test_performance_metrics(self, temp_templates_dir):
        """Test comprehensive performance metrics"""
        optimizer = TemplatePerformanceOptimizer(temp_templates_dir)

        def mock_load_func(name):
            return f"Content for {name}"

        # Generate some activity
        optimizer.get_template("test1", mock_load_func)
        optimizer.get_template("test2", mock_load_func)
        optimizer.get_template("test1", mock_load_func)  # Cache hit

        # Get metrics
        metrics = optimizer.get_performance_metrics()

        # Check structure
        assert "cache_metrics" in metrics
        assert "usage_stats" in metrics
        assert "memory_stats" in metrics
        assert "preload_stats" in metrics

        # Check cache metrics
        cache_metrics = metrics["cache_metrics"]
        assert cache_metrics["total_requests"] == 3
        assert cache_metrics["cache_hits"] == 1
        assert cache_metrics["cache_misses"] == 2
        assert cache_metrics["hit_rate"] == 1 / 3

        # Check usage stats
        usage_stats = metrics["usage_stats"]
        assert "test1" in usage_stats
        assert "test2" in usage_stats

        # Cleanup
        optimizer.shutdown()

    def test_statistics_reset(self, temp_templates_dir):
        """Test statistics reset"""
        optimizer = TemplatePerformanceOptimizer(temp_templates_dir)

        def mock_load_func(name):
            return f"Content for {name}"

        # Generate activity
        optimizer.get_template("test", mock_load_func)

        # Check initial metrics
        metrics = optimizer.get_performance_metrics()
        assert metrics["cache_metrics"]["total_requests"] > 0

        # Reset statistics
        optimizer.reset_statistics()

        # Check reset metrics
        metrics = optimizer.get_performance_metrics()
        assert metrics["cache_metrics"]["total_requests"] == 0
        assert len(metrics["usage_stats"]) == 0

        # Cleanup
        optimizer.shutdown()


class TestPerformanceBenchmarks:
    """Performance benchmark tests"""

    @pytest.fixture
    def large_templates_dir(self):
        """Create directory with many templates for benchmarking"""
        with tempfile.TemporaryDirectory() as temp_dir:
            templates_dir = Path(temp_dir)

            # Create many template files
            for i in range(50):
                content = f"Template {i} content: " + "x" * 1000  # 1KB each
                (templates_dir / f"template_{i:03d}.tmpl").write_text(content)

            yield templates_dir

    def test_preload_performance(self, large_templates_dir):
        """Test preloading performance with many templates"""
        optimizer = TemplatePerformanceOptimizer(large_templates_dir)

        start_time = time.time()
        results = optimizer.preloader.preload_templates()
        preload_time = time.time() - start_time

        # Should complete within reasonable time
        assert preload_time < 10.0  # 10 seconds max
        assert len(results) == 50
        assert all(results.values())  # All should succeed

        # Check cache is populated
        assert optimizer.cache.size() > 0

        # Cleanup
        optimizer.shutdown()

    def test_cache_performance_under_load(self, large_templates_dir):
        """Test cache performance under concurrent load"""
        optimizer = TemplatePerformanceOptimizer(large_templates_dir, cache_size=20)

        def mock_load_func(name):
            # Simulate file loading time
            time.sleep(0.001)  # 1ms
            return f"Content for {name}"

        def worker_thread(thread_id):
            """Worker thread for concurrent access"""
            for i in range(10):
                template_name = f"template_{(thread_id * 10 + i) % 50:03d}"
                optimizer.get_template(template_name, mock_load_func)

        # Start multiple threads
        threads = []
        start_time = time.time()

        for i in range(5):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        total_time = time.time() - start_time

        # Check performance
        metrics = optimizer.get_performance_metrics()
        total_requests = metrics["cache_metrics"]["total_requests"]
        hit_rate = metrics["cache_metrics"]["hit_rate"]

        assert total_requests == 50  # 5 threads * 10 requests each
        assert hit_rate > 0  # Should have some cache hits
        assert total_time < 5.0  # Should complete quickly due to caching

        # Cleanup
        optimizer.shutdown()

    def test_memory_usage_scaling(self, large_templates_dir):
        """Test memory usage with increasing cache size"""
        # Test with small cache
        small_optimizer = TemplatePerformanceOptimizer(
            large_templates_dir, cache_size=10, cache_memory_mb=1
        )

        def mock_load_func(name):
            return "x" * 1000  # 1KB content

        # Fill small cache
        for i in range(10):
            small_optimizer.get_template(f"template_{i:03d}", mock_load_func)

        small_metrics = small_optimizer.get_performance_metrics()
        small_memory = small_metrics["cache_metrics"]["cache_memory_usage"]

        # Test with large cache
        large_optimizer = TemplatePerformanceOptimizer(
            large_templates_dir, cache_size=30, cache_memory_mb=5
        )

        # Fill large cache
        for i in range(30):
            large_optimizer.get_template(f"template_{i:03d}", mock_load_func)

        large_metrics = large_optimizer.get_performance_metrics()
        large_memory = large_metrics["cache_metrics"]["cache_memory_usage"]

        # Large cache should use more memory
        assert large_memory > small_memory

        # But should be within reasonable bounds
        assert large_memory < 10 * 1024 * 1024  # Less than 10MB

        # Cleanup
        small_optimizer.shutdown()
        large_optimizer.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
