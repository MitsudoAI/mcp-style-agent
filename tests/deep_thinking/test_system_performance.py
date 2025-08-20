"""
System Performance Tests

Tests for system resource monitoring, performance bottleneck detection,
response time statistics, and comprehensive system performance testing.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch

from src.mcps.deep_thinking.performance.system_monitor import (
    SystemPerformanceMonitor,
    SystemResourceMonitor,
    ResponseTimeTracker,
    PerformanceBottleneckDetector,
    SystemResourceStats,
    ResponseTimeStats,
    PerformanceMetric,
)


class TestResponseTimeTracker:
    """Test response time tracking functionality"""

    def test_basic_tracking(self):
        """Test basic response time tracking"""
        tracker = ResponseTimeTracker()

        # Track an operation
        with tracker.track_operation("test_operation"):
            time.sleep(0.01)  # 10ms

        stats = tracker.get_stats()
        assert "test_operation" in stats

        op_stats = stats["test_operation"]
        assert op_stats["total_calls"] == 1
        assert op_stats["average_time"] > 0.005  # Should be at least 5ms
        assert op_stats["error_count"] == 0
        assert op_stats["error_rate"] == 0.0

    def test_multiple_operations(self):
        """Test tracking multiple operations"""
        tracker = ResponseTimeTracker()

        # Track multiple operations
        for i in range(5):
            with tracker.track_operation("test_op"):
                time.sleep(0.001)  # 1ms

        stats = tracker.get_stats()
        op_stats = stats["test_op"]

        assert op_stats["total_calls"] == 5
        assert op_stats["min_time"] > 0
        assert op_stats["max_time"] >= op_stats["min_time"]
        assert op_stats["average_time"] > 0

    def test_error_tracking(self):
        """Test error tracking in operations"""
        tracker = ResponseTimeTracker()

        # Track successful operation
        with tracker.track_operation("success_op"):
            pass

        # Track failed operation
        try:
            with tracker.track_operation("error_op"):
                raise ValueError("Test error")
        except ValueError:
            pass

        stats = tracker.get_stats()

        success_stats = stats["success_op"]
        assert success_stats["error_count"] == 0
        assert success_stats["error_rate"] == 0.0

        error_stats = stats["error_op"]
        assert error_stats["error_count"] == 1
        assert error_stats["error_rate"] == 1.0

    def test_percentile_calculation(self):
        """Test percentile calculation for response times"""
        tracker = ResponseTimeTracker()

        # Generate operations with varying response times
        times = [0.001, 0.002, 0.003, 0.004, 0.005, 0.010, 0.020, 0.050, 0.100, 0.200]

        for t in times:
            tracker.record_response_time("perf_test", t, True)

        stats = tracker.get_stats()
        perf_stats = stats["perf_test"]

        assert perf_stats["total_calls"] == len(times)
        assert perf_stats["p95_time"] > perf_stats["average_time"]
        assert perf_stats["p99_time"] >= perf_stats["p95_time"]

    def test_stats_reset(self):
        """Test statistics reset"""
        tracker = ResponseTimeTracker()

        # Generate some data
        with tracker.track_operation("test_op"):
            time.sleep(0.001)

        assert len(tracker.get_stats()) == 1

        # Reset and verify
        tracker.reset_stats()
        assert len(tracker.get_stats()) == 0


class TestSystemResourceMonitor:
    """Test system resource monitoring"""

    def test_resource_stats_collection(self):
        """Test collection of system resource statistics"""
        monitor = SystemResourceMonitor()

        stats = monitor.get_current_stats()
        assert stats is not None
        assert stats.cpu_percent >= 0
        assert stats.memory_percent >= 0
        assert stats.process_memory_mb >= 0
        assert stats.thread_count > 0

    def test_monitoring_start_stop(self):
        """Test starting and stopping monitoring"""
        monitor = SystemResourceMonitor(monitoring_interval=0.1)

        assert not monitor.monitoring_active

        monitor.start_monitoring()
        assert monitor.monitoring_active

        # Let it run briefly
        time.sleep(0.2)

        monitor.stop_monitoring()
        assert not monitor.monitoring_active

    def test_callback_registration(self):
        """Test callback registration and execution"""
        monitor = SystemResourceMonitor(monitoring_interval=0.1)
        callback_called = False
        received_stats = None

        def test_callback(stats):
            nonlocal callback_called, received_stats
            callback_called = True
            received_stats = stats

        monitor.add_callback(test_callback)
        monitor.start_monitoring()

        try:
            # Wait for callback to be called
            time.sleep(0.3)

            assert callback_called
            assert received_stats is not None
            assert isinstance(received_stats, SystemResourceStats)

        finally:
            monitor.stop_monitoring()

    def test_historical_stats(self):
        """Test historical statistics collection"""
        monitor = SystemResourceMonitor(monitoring_interval=0.05)

        monitor.start_monitoring()

        try:
            # Let it collect some data
            time.sleep(0.2)

            # Get historical stats
            historical = monitor.get_historical_stats(minutes=1)
            assert len(historical) > 0

            # All stats should be recent
            for stats in historical:
                assert isinstance(stats, SystemResourceStats)
                assert stats.timestamp is not None

        finally:
            monitor.stop_monitoring()


class TestPerformanceBottleneckDetector:
    """Test performance bottleneck detection"""

    def test_cpu_bottleneck_detection(self):
        """Test CPU bottleneck detection"""
        detector = PerformanceBottleneckDetector()

        # Create high CPU usage stats
        high_cpu_stats = SystemResourceStats(
            cpu_percent=90.0, memory_percent=50.0, disk_usage_percent=30.0
        )

        bottlenecks = detector.analyze_system_resources(high_cpu_stats)
        assert len(bottlenecks) > 0
        assert any("CPU usage" in b for b in bottlenecks)

    def test_memory_bottleneck_detection(self):
        """Test memory bottleneck detection"""
        detector = PerformanceBottleneckDetector()

        # Create high memory usage stats
        high_memory_stats = SystemResourceStats(
            cpu_percent=30.0, memory_percent=90.0, disk_usage_percent=30.0
        )

        bottlenecks = detector.analyze_system_resources(high_memory_stats)
        assert len(bottlenecks) > 0
        assert any("memory usage" in b for b in bottlenecks)

    def test_response_time_bottleneck_detection(self):
        """Test response time bottleneck detection"""
        detector = PerformanceBottleneckDetector()

        # Create slow response time stats
        slow_stats = ResponseTimeStats(
            operation_name="slow_op",
            total_calls=100,
            average_time=3.0,  # 3 seconds - very slow
            error_count=0,
        )

        response_stats = {"slow_op": slow_stats}
        bottlenecks = detector.analyze_response_times(response_stats)

        assert len(bottlenecks) > 0
        assert any("Slow operation" in b for b in bottlenecks)

    def test_error_rate_bottleneck_detection(self):
        """Test error rate bottleneck detection"""
        detector = PerformanceBottleneckDetector()

        # Create high error rate stats
        error_stats = ResponseTimeStats(
            operation_name="error_op",
            total_calls=100,
            average_time=0.1,
            error_count=10,  # 10% error rate
        )

        response_stats = {"error_op": error_stats}
        bottlenecks = detector.analyze_response_times(response_stats)

        assert len(bottlenecks) > 0
        assert any("error rate" in b for b in bottlenecks)

    def test_comprehensive_bottleneck_detection(self):
        """Test comprehensive bottleneck detection"""
        detector = PerformanceBottleneckDetector()

        # Create problematic system stats
        system_stats = SystemResourceStats(
            cpu_percent=85.0, memory_percent=90.0, disk_usage_percent=95.0
        )

        # Create problematic response stats
        response_stats = {
            "slow_op": ResponseTimeStats(
                operation_name="slow_op",
                total_calls=50,
                average_time=2.5,
                error_count=5,
            )
        }

        result = detector.detect_bottlenecks(system_stats, response_stats)

        assert result["total_bottlenecks"] > 0
        assert result["severity"] in ["low", "medium", "high"]
        assert len(result["recommendations"]) > 0
        assert "timestamp" in result


class TestSystemPerformanceMonitor:
    """Test main system performance monitor"""

    def test_monitor_initialization(self):
        """Test monitor initialization"""
        monitor = SystemPerformanceMonitor(monitoring_interval=0.1)

        assert monitor.resource_monitor is not None
        assert monitor.response_tracker is not None
        assert monitor.bottleneck_detector is not None

    def test_operation_tracking(self):
        """Test operation tracking through monitor"""
        monitor = SystemPerformanceMonitor()

        # Track an operation
        with monitor.track_operation("test_operation"):
            time.sleep(0.01)

        summary = monitor.get_performance_summary()
        assert "response_times" in summary
        assert "test_operation" in summary["response_times"]

    def test_performance_summary(self):
        """Test performance summary generation"""
        monitor = SystemPerformanceMonitor()

        # Generate some activity
        with monitor.track_operation("summary_test"):
            time.sleep(0.001)

        summary = monitor.get_performance_summary()

        assert "timestamp" in summary
        assert "system_resources" in summary
        assert "response_times" in summary
        assert "recent_bottlenecks" in summary
        assert "performance_trends" in summary

        # Check system resources structure
        resources = summary["system_resources"]
        assert "cpu_percent" in resources
        assert "memory_percent" in resources
        assert "process_memory_mb" in resources

    def test_monitoring_lifecycle(self):
        """Test monitoring start/stop lifecycle"""
        monitor = SystemPerformanceMonitor(monitoring_interval=0.1)

        # Start monitoring
        monitor.start_monitoring()

        # Generate some activity
        with monitor.track_operation("lifecycle_test"):
            time.sleep(0.01)

        # Let monitoring run briefly
        time.sleep(0.2)

        # Stop monitoring
        monitor.stop_monitoring()

        # Should still be able to get summary
        summary = monitor.get_performance_summary()
        assert summary is not None

    def test_optimization_callback(self):
        """Test optimization callback functionality"""
        monitor = SystemPerformanceMonitor()
        callback_called = False
        received_result = None

        def optimization_callback(bottleneck_result):
            nonlocal callback_called, received_result
            callback_called = True
            received_result = bottleneck_result

        monitor.add_optimization_callback(optimization_callback)

        # Simulate high resource usage to trigger callback
        high_usage_stats = SystemResourceStats(cpu_percent=90.0, memory_percent=85.0)

        # Manually trigger bottleneck check
        monitor._check_for_bottlenecks(high_usage_stats)

        # Callback should have been called due to high resource usage
        assert callback_called
        assert received_result is not None
        assert received_result["total_bottlenecks"] > 0

    def test_performance_report_generation(self):
        """Test performance report generation"""
        monitor = SystemPerformanceMonitor()

        # Generate some activity
        with monitor.track_operation("report_test"):
            time.sleep(0.001)

        report = monitor.generate_performance_report()

        assert isinstance(report, str)
        assert "System Performance Report" in report
        assert "System Resources:" in report
        assert "CPU Usage:" in report
        assert "Memory Usage:" in report

    def test_statistics_reset(self):
        """Test statistics reset functionality"""
        monitor = SystemPerformanceMonitor()

        # Generate some activity
        with monitor.track_operation("reset_test"):
            time.sleep(0.001)

        # Verify data exists
        summary_before = monitor.get_performance_summary()
        assert len(summary_before["response_times"]) > 0

        # Reset statistics
        monitor.reset_statistics()

        # Verify data is cleared
        summary_after = monitor.get_performance_summary()
        assert len(summary_after["response_times"]) == 0

    def test_system_optimization(self):
        """Test system optimization functionality"""
        monitor = SystemPerformanceMonitor()

        # Should not raise exception
        monitor.optimize_system_performance()


class TestPerformanceBenchmarks:
    """Performance benchmark tests"""

    def test_concurrent_operation_tracking(self):
        """Test concurrent operation tracking performance"""
        monitor = SystemPerformanceMonitor()
        results = []

        def worker_thread(thread_id, iterations=50):
            for i in range(iterations):
                with monitor.track_operation(f"concurrent_op_{thread_id}"):
                    # Simulate some work
                    time.sleep(0.001)
                results.append(f"{thread_id}_{i}")

        # Start multiple threads
        threads = []
        start_time = time.time()

        for i in range(5):
            thread = threading.Thread(target=worker_thread, args=(i, 20))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        total_time = time.time() - start_time

        # Check results
        assert len(results) == 100  # 5 threads * 20 iterations
        assert total_time < 10.0  # Should complete within 10 seconds

        # Check tracking worked
        summary = monitor.get_performance_summary()
        response_times = summary["response_times"]

        # Should have tracked operations for each thread
        tracked_ops = [
            op for op in response_times.keys() if op.startswith("concurrent_op_")
        ]
        assert len(tracked_ops) == 5

    def test_resource_monitoring_overhead(self):
        """Test resource monitoring overhead"""
        monitor = SystemPerformanceMonitor(monitoring_interval=0.01)  # Very frequent

        # Measure overhead of monitoring
        start_time = time.time()
        monitor.start_monitoring()

        try:
            # Do some work while monitoring
            for i in range(100):
                with monitor.track_operation("overhead_test"):
                    # Minimal work
                    pass

            # Let monitoring run
            time.sleep(0.1)

        finally:
            monitor.stop_monitoring()

        total_time = time.time() - start_time

        # Should complete quickly despite monitoring
        assert total_time < 5.0

        # Should have collected some data
        summary = monitor.get_performance_summary()
        assert "overhead_test" in summary["response_times"]
        assert summary["response_times"]["overhead_test"]["total_calls"] == 100

    def test_memory_usage_tracking(self):
        """Test memory usage tracking accuracy"""
        monitor = SystemPerformanceMonitor()

        # Get initial memory usage
        initial_summary = monitor.get_performance_summary()
        initial_memory = initial_summary["system_resources"]["process_memory_mb"]

        # Allocate some memory
        large_data = []
        for i in range(1000):
            large_data.append("x" * 1000)  # 1KB each = 1MB total

        # Get memory usage after allocation
        after_summary = monitor.get_performance_summary()
        after_memory = after_summary["system_resources"]["process_memory_mb"]

        # Memory usage should have increased
        memory_increase = after_memory - initial_memory
        assert memory_increase > 0  # Should show some increase

        # Clean up
        del large_data
        import gc

        gc.collect()

    def test_bottleneck_detection_accuracy(self):
        """Test bottleneck detection accuracy under load"""
        monitor = SystemPerformanceMonitor()

        # Create operations with different performance characteristics
        operations = [
            ("fast_op", 0.001, 0),  # Fast, no errors
            ("slow_op", 0.1, 0),  # Slow, no errors
            ("error_op", 0.01, 0.1),  # Fast, but 10% error rate
        ]

        # Simulate operations
        for op_name, base_time, error_rate in operations:
            for i in range(50):
                try:
                    with monitor.track_operation(op_name) as tracker:
                        time.sleep(base_time)
                        # Simulate errors
                        if i < 50 * error_rate:
                            tracker.mark_error()
                            raise ValueError("Simulated error")
                except ValueError:
                    pass  # Expected for error simulation

        # Analyze results
        summary = monitor.get_performance_summary()
        response_times = summary["response_times"]

        # Verify tracking worked correctly
        assert "fast_op" in response_times
        assert "slow_op" in response_times
        assert "error_op" in response_times

        # Fast operation should have low average time
        assert response_times["fast_op"]["average_time"] < 0.01

        # Slow operation should have higher average time
        assert response_times["slow_op"]["average_time"] > 0.05

        # Error operation should have error rate
        assert response_times["error_op"]["error_rate"] > 0.05


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
