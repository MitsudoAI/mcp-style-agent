"""
Integrated Performance Optimization Tests

Tests for the comprehensive performance optimization system that integrates
template optimization, database optimization, and system monitoring.
"""

import pytest
import tempfile
import time
import threading
from pathlib import Path

from src.mcps.deep_thinking.performance.integrated_optimizer import (
    IntegratedPerformanceOptimizer,
)
from src.mcps.deep_thinking.templates.template_manager import TemplateManager
from src.mcps.deep_thinking.data.database import ThinkingDatabase


class TestIntegratedPerformanceOptimizer:
    """Test integrated performance optimization"""

    @pytest.fixture
    def temp_setup(self):
        """Create temporary setup for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            templates_dir = Path(temp_dir) / "templates"
            templates_dir.mkdir()

            # Create sample template
            (templates_dir / "test_template.tmpl").write_text("Test template: {param}")

            # Create temporary database
            db_file = Path(temp_dir) / "test.db"

            yield str(templates_dir), str(db_file)

    def test_optimizer_initialization(self, temp_setup):
        """Test optimizer initialization with all components"""
        templates_dir, db_path = temp_setup

        optimizer = IntegratedPerformanceOptimizer(
            templates_dir=templates_dir,
            db_path=db_path,
            enable_template_optimization=True,
            enable_database_optimization=True,
            enable_system_monitoring=True,
            monitoring_interval=1.0,
        )

        try:
            assert optimizer.template_optimizer is not None
            assert optimizer.database_optimizer is not None
            assert optimizer.system_monitor is not None

        finally:
            optimizer.shutdown()

    def test_optimizer_with_memory_database(self, temp_setup):
        """Test optimizer with in-memory database (database optimization disabled)"""
        templates_dir, _ = temp_setup

        optimizer = IntegratedPerformanceOptimizer(
            templates_dir=templates_dir,
            db_path=":memory:",
            enable_template_optimization=True,
            enable_database_optimization=True,  # Should be disabled automatically
            enable_system_monitoring=True,
        )

        try:
            assert optimizer.template_optimizer is not None
            assert optimizer.database_optimizer is None  # Should be None for memory DB
            assert optimizer.system_monitor is not None

        finally:
            optimizer.shutdown()

    def test_operation_tracking(self, temp_setup):
        """Test operation tracking across the integrated system"""
        templates_dir, db_path = temp_setup

        optimizer = IntegratedPerformanceOptimizer(
            templates_dir=templates_dir, db_path=db_path, monitoring_interval=0.1
        )

        try:
            optimizer.start_monitoring()

            # Track some operations
            with optimizer.track_operation("test_operation_1"):
                time.sleep(0.01)

            with optimizer.track_operation("test_operation_2"):
                time.sleep(0.005)

            # Let monitoring collect data
            time.sleep(0.2)

            # Check metrics
            metrics = optimizer.get_comprehensive_metrics()
            assert "system_performance" in metrics

            if "response_times" in metrics["system_performance"]:
                response_times = metrics["system_performance"]["response_times"]
                assert (
                    "test_operation_1" in response_times
                    or "test_operation_2" in response_times
                )

        finally:
            optimizer.stop_monitoring()
            optimizer.shutdown()

    def test_template_optimization_integration(self, temp_setup):
        """Test template optimization integration"""
        templates_dir, db_path = temp_setup

        optimizer = IntegratedPerformanceOptimizer(
            templates_dir=templates_dir,
            db_path=db_path,
            enable_template_optimization=True,
            enable_database_optimization=False,
            enable_system_monitoring=False,
        )

        try:
            # Mock load function
            def mock_load_func(name):
                template_path = Path(templates_dir) / f"{name}.tmpl"
                if template_path.exists():
                    return template_path.read_text()
                return None

            # Get template through optimizer
            template = optimizer.get_template("test_template", mock_load_func)
            assert template == "Test template: {param}"

            # Second call should hit cache
            template2 = optimizer.get_template("test_template", mock_load_func)
            assert template2 == "Test template: {param}"

            # Check metrics
            metrics = optimizer.get_comprehensive_metrics()
            assert "template_performance" in metrics

        finally:
            optimizer.shutdown()

    def test_comprehensive_optimization(self, temp_setup):
        """Test comprehensive optimization across all systems"""
        templates_dir, db_path = temp_setup

        optimizer = IntegratedPerformanceOptimizer(
            templates_dir=templates_dir, db_path=db_path, monitoring_interval=0.1
        )

        try:
            # Generate some activity first
            with optimizer.track_operation("pre_optimization_test"):
                time.sleep(0.001)

            # Run comprehensive optimization
            result = optimizer.optimize_all_systems()

            assert result is not None
            assert "timestamp" in result
            assert "optimizations_applied" in result
            assert "optimization_time" in result
            assert result["success"] is True

            # Should have applied some optimizations
            assert len(result["optimizations_applied"]) > 0

        finally:
            optimizer.shutdown()

    def test_performance_metrics_collection(self, temp_setup):
        """Test comprehensive performance metrics collection"""
        templates_dir, db_path = temp_setup

        optimizer = IntegratedPerformanceOptimizer(
            templates_dir=templates_dir, db_path=db_path, monitoring_interval=0.1
        )

        try:
            optimizer.start_monitoring()

            # Generate some activity
            for i in range(5):
                with optimizer.track_operation(f"metrics_test_{i}"):
                    time.sleep(0.001)

            # Let monitoring collect data
            time.sleep(0.2)

            # Get comprehensive metrics
            metrics = optimizer.get_comprehensive_metrics()

            assert "timestamp" in metrics
            assert "integrated_optimizer" in metrics

            # Check optimizer status
            optimizer_info = metrics["integrated_optimizer"]
            assert "template_optimizer_enabled" in optimizer_info
            assert "database_optimizer_enabled" in optimizer_info
            assert "system_monitor_enabled" in optimizer_info

            # Should have template performance metrics
            if optimizer_info["template_optimizer_enabled"]:
                assert "template_performance" in metrics

            # Should have database performance metrics
            if optimizer_info["database_optimizer_enabled"]:
                assert "database_performance" in metrics

            # Should have system performance metrics
            if optimizer_info["system_monitor_enabled"]:
                assert "system_performance" in metrics

        finally:
            optimizer.stop_monitoring()
            optimizer.shutdown()

    def test_performance_report_generation(self, temp_setup):
        """Test performance report generation"""
        templates_dir, db_path = temp_setup

        optimizer = IntegratedPerformanceOptimizer(
            templates_dir=templates_dir, db_path=db_path
        )

        try:
            # Generate some activity
            with optimizer.track_operation("report_test"):
                time.sleep(0.001)

            # Generate report
            report = optimizer.generate_performance_report()

            assert isinstance(report, str)
            assert "Integrated Performance Report" in report
            assert "Optimizer Status:" in report
            assert "Template Optimization:" in report
            assert "Database Optimization:" in report
            assert "System Monitoring:" in report

        finally:
            optimizer.shutdown()

    def test_automatic_optimization_trigger(self, temp_setup):
        """Test automatic optimization triggered by performance issues"""
        templates_dir, db_path = temp_setup

        optimizer = IntegratedPerformanceOptimizer(
            templates_dir=templates_dir, db_path=db_path, monitoring_interval=0.1
        )

        try:
            # Simulate performance issue
            bottleneck_result = {
                "severity": "high",
                "total_bottlenecks": 3,
                "resource_bottlenecks": ["High memory usage: 90.0%"],
                "response_bottlenecks": ["Slow operation test: 2.5s average"],
                "recommendations": ["Optimize memory usage", "Profile slow operations"],
            }

            # Trigger automatic optimization
            optimizer._handle_performance_issues(bottleneck_result)

            # Should not raise exception and should log optimization attempts

        finally:
            optimizer.shutdown()

    def test_statistics_reset(self, temp_setup):
        """Test statistics reset across all systems"""
        templates_dir, db_path = temp_setup

        optimizer = IntegratedPerformanceOptimizer(
            templates_dir=templates_dir, db_path=db_path
        )

        try:
            # Generate some activity
            with optimizer.track_operation("reset_test"):
                time.sleep(0.001)

            # Run optimization to create history
            optimizer.optimize_all_systems()

            # Verify data exists
            metrics_before = optimizer.get_comprehensive_metrics()
            optimizer_info_before = metrics_before["integrated_optimizer"]
            assert optimizer_info_before["optimization_count"] > 0

            # Reset statistics
            optimizer.reset_all_statistics()

            # Verify data is cleared
            metrics_after = optimizer.get_comprehensive_metrics()
            optimizer_info_after = metrics_after["integrated_optimizer"]
            assert optimizer_info_after["optimization_count"] == 0

        finally:
            optimizer.shutdown()

    def test_concurrent_operations(self, temp_setup):
        """Test concurrent operations with integrated optimization"""
        templates_dir, db_path = temp_setup

        optimizer = IntegratedPerformanceOptimizer(
            templates_dir=templates_dir, db_path=db_path, monitoring_interval=0.05
        )

        results = []

        def worker_thread(thread_id, iterations=10):
            for i in range(iterations):
                with optimizer.track_operation(f"concurrent_test_{thread_id}"):
                    # Simulate some work
                    time.sleep(0.001)
                results.append(f"{thread_id}_{i}")

        try:
            optimizer.start_monitoring()

            # Start multiple threads
            threads = []
            for i in range(3):
                thread = threading.Thread(target=worker_thread, args=(i, 5))
                threads.append(thread)
                thread.start()

            # Wait for completion
            for thread in threads:
                thread.join()

            # Let monitoring collect data
            time.sleep(0.1)

            # Check results
            assert len(results) == 15  # 3 threads * 5 iterations

            # Check that operations were tracked
            metrics = optimizer.get_comprehensive_metrics()
            if (
                "system_performance" in metrics
                and "response_times" in metrics["system_performance"]
            ):
                response_times = metrics["system_performance"]["response_times"]
                # Should have tracked some concurrent operations
                concurrent_ops = [
                    op
                    for op in response_times.keys()
                    if op.startswith("concurrent_test_")
                ]
                assert len(concurrent_ops) > 0

        finally:
            optimizer.stop_monitoring()
            optimizer.shutdown()


class TestIntegratedPerformanceWithRealComponents:
    """Test integrated performance with real template manager and database"""

    @pytest.fixture
    def real_components_setup(self):
        """Setup with real template manager and database"""
        with tempfile.TemporaryDirectory() as temp_dir:
            templates_dir = Path(temp_dir) / "templates"
            templates_dir.mkdir()

            # Create sample templates
            (templates_dir / "test1.tmpl").write_text("Template 1: {param1}")
            (templates_dir / "test2.tmpl").write_text("Template 2: {param2}")

            db_file = Path(temp_dir) / "test.db"

            yield str(templates_dir), str(db_file)

    def test_integration_with_template_manager(self, real_components_setup):
        """Test integration with real template manager"""
        templates_dir, db_path = real_components_setup

        # Create template manager with performance optimization
        template_manager = TemplateManager(
            templates_dir, enable_performance_optimization=True
        )

        # Create integrated optimizer
        optimizer = IntegratedPerformanceOptimizer(
            templates_dir=templates_dir,
            db_path=db_path,
            enable_template_optimization=True,
            enable_database_optimization=False,
            enable_system_monitoring=True,
        )

        try:
            optimizer.start_monitoring()

            # Use template manager
            template1 = template_manager.get_template("test1", {"param1": "value1"})
            assert template1 == "Template 1: value1"

            template2 = template_manager.get_template("test2", {"param2": "value2"})
            assert template2 == "Template 2: value2"

            # Use optimizer for template access
            def load_func(name):
                return template_manager._load_template_content(name)

            template3 = optimizer.get_template("test1", load_func)
            assert "Template 1:" in template3

            # Check that both systems are working
            tm_metrics = template_manager.get_performance_metrics()
            opt_metrics = optimizer.get_comprehensive_metrics()

            assert "template_manager_stats" in tm_metrics
            assert "template_performance" in opt_metrics

        finally:
            optimizer.stop_monitoring()
            optimizer.shutdown()
            template_manager.shutdown()

    def test_integration_with_database(self, real_components_setup):
        """Test integration with real database"""
        templates_dir, db_path = real_components_setup

        # Create database with performance optimization
        database = ThinkingDatabase(
            db_path,
            enable_performance_optimization=True,
            min_connections=1,
            max_connections=3,
        )

        # Create integrated optimizer
        optimizer = IntegratedPerformanceOptimizer(
            templates_dir=templates_dir,
            db_path=db_path,
            enable_template_optimization=False,
            enable_database_optimization=True,
            enable_system_monitoring=True,
        )

        try:
            optimizer.start_monitoring()

            # Use database
            session_id = "test_session_123"
            success = database.create_session(session_id, "Test topic")
            assert success is True

            session = database.get_session(session_id)
            assert session is not None
            assert session["topic"] == "Test topic"

            # Use optimizer for database queries
            cursor = optimizer.execute_database_query(
                "SELECT COUNT(*) FROM thinking_sessions"
            )
            result = cursor.fetchone()
            assert result is not None

            # Check that both systems are working
            db_metrics = database.get_performance_metrics()
            opt_metrics = optimizer.get_comprehensive_metrics()

            assert "database_info" in db_metrics
            assert "database_performance" in opt_metrics

        finally:
            optimizer.stop_monitoring()
            optimizer.shutdown()
            database.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
