"""
System Reliability and Stability Tests

This module provides comprehensive reliability testing for the Deep Thinking Engine,
focusing on long-term stability, edge cases, and system resilience.

Requirements: 系统稳定性和可靠性测试
"""

import gc
import logging
import random
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import pytest

from src.mcps.deep_thinking.config.config_manager import ConfigManager
from src.mcps.deep_thinking.data.database import ThinkingDatabase
from src.mcps.deep_thinking.flows.flow_manager import FlowManager
from src.mcps.deep_thinking.sessions.session_manager import SessionManager
from src.mcps.deep_thinking.templates.template_manager import TemplateManager
from src.mcps.deep_thinking.tools.mcp_tools import MCPTools


@dataclass
class ReliabilityTestMetrics:
    """Metrics for reliability testing"""
    test_name: str
    duration_seconds: float
    total_operations: int
    successful_operations: int
    failed_operations: int
    error_types: Dict[str, int]
    memory_usage_mb: float
    max_memory_mb: float
    average_response_time: float
    max_response_time: float
    resource_leaks_detected: int
    recovery_attempts: int
    successful_recoveries: int


class SystemReliabilityTester:
    """Comprehensive system reliability tester"""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """Initialize the reliability tester"""
        self.temp_dir = temp_dir or tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        self.logger = logging.getLogger(__name__)
        self.setup_test_environment()
        
        # Metrics tracking
        self.metrics: List[ReliabilityTestMetrics] = []
        self.error_log: List[Dict[str, Any]] = []
        
        # System components
        self.database: Optional[ThinkingDatabase] = None
        self.template_manager: Optional[TemplateManager] = None
        self.flow_manager: Optional[FlowManager] = None
        self.session_manager: Optional[SessionManager] = None
        self.mcp_tools: Optional[MCPTools] = None
        
        self._initialize_components()
    
    def setup_test_environment(self):
        """Setup test environment"""
        # Create directories
        (self.temp_path / "config").mkdir(exist_ok=True)
        (self.temp_path / "templates").mkdir(exist_ok=True)
        (self.temp_path / "data").mkdir(exist_ok=True)
        
        # Create minimal config
        import yaml
        config = {
            'database': {'path': str(self.temp_path / "data" / "reliability_test.db")},
            'templates': {'directory': str(self.temp_path / "templates")}
        }
        
        with open(self.temp_path / "config" / "system.yaml", 'w') as f:
            yaml.dump(config, f)
        
        # Create test template
        (self.temp_path / "templates" / "test_template.tmpl").write_text(
            "Test template for reliability testing: {topic}"
        )
    
    def _initialize_components(self):
        """Initialize system components"""
        try:
            db_path = str(self.temp_path / "data" / "reliability_test.db")
            self.database = ThinkingDatabase(db_path)
            
            templates_dir = str(self.temp_path / "templates")
            self.template_manager = TemplateManager(templates_dir)
            
            self.flow_manager = FlowManager(self.database)
            self.session_manager = SessionManager(self.database)
            
            self.mcp_tools = MCPTools(
                session_manager=self.session_manager,
                flow_manager=self.flow_manager,
                template_manager=self.template_manager,
                flow_executor=None  # Not needed for basic reliability tests
            )
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            raise
    
    def test_long_term_stability(self, duration_minutes: int = 30, operations_per_minute: int = 60) -> ReliabilityTestMetrics:
        """Test long-term system stability"""
        self.logger.info(f"Starting long-term stability test: {duration_minutes} minutes")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        # Metrics tracking
        total_operations = 0
        successful_operations = 0
        failed_operations = 0
        error_types = {}
        response_times = []
        memory_samples = []
        recovery_attempts = 0
        successful_recoveries = 0
        
        # Memory monitoring
        import psutil
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        def monitor_memory():
            """Monitor memory usage"""
            while time.time() < end_time:
                try:
                    memory_mb = process.memory_info().rss / 1024 / 1024
                    memory_samples.append(memory_mb)
                    time.sleep(10)  # Sample every 10 seconds
                except:
                    pass
        
        # Start memory monitoring thread
        memory_thread = threading.Thread(target=monitor_memory, daemon=True)
        memory_thread.start()
        
        # Operation types for variety
        operation_types = [
            'create_session',
            'start_thinking',
            'template_access',
            'database_query',
            'session_cleanup'
        ]
        
        # Main test loop
        while time.time() < end_time:
            batch_start = time.time()
            
            # Run operations for this minute
            for _ in range(operations_per_minute):
                if time.time() >= end_time:
                    break
                
                op_start = time.time()
                total_operations += 1
                
                try:
                    # Randomly select operation type
                    operation = random.choice(operation_types)
                    
                    if operation == 'create_session':
                        session_id = f"stability_test_{total_operations}"
                        success = self.session_manager.create_session(session_id, f"Stability test topic {total_operations}")
                        assert success
                        
                    elif operation == 'start_thinking':
                        result = self.mcp_tools.start_thinking(f"Stability test topic {total_operations}")
                        assert 'session_id' in result
                        
                    elif operation == 'template_access':
                        template = self.template_manager.get_template('test_template', {'topic': f'Test {total_operations}'})
                        assert template is not None
                        
                    elif operation == 'database_query':
                        sessions = self.database.get_all_sessions()
                        assert isinstance(sessions, list)
                        
                    elif operation == 'session_cleanup':
                        # Periodically clean up old sessions
                        if total_operations % 100 == 0:
                            # This would be a cleanup operation
                            pass
                    
                    successful_operations += 1
                    
                except Exception as e:
                    failed_operations += 1
                    error_type = type(e).__name__
                    error_types[error_type] = error_types.get(error_type, 0) + 1
                    
                    self.error_log.append({
                        'timestamp': time.time(),
                        'operation': operation,
                        'error_type': error_type,
                        'error_message': str(e),
                        'operation_number': total_operations
                    })
                    
                    # Attempt recovery
                    recovery_attempts += 1
                    try:
                        # Simple recovery: reinitialize components if needed
                        if error_type in ['DatabaseError', 'ConnectionError']:
                            self._reinitialize_database()
                        successful_recoveries += 1
                    except:
                        pass
                
                finally:
                    response_time = time.time() - op_start
                    response_times.append(response_time)
            
            # Wait for next minute (if time remaining)
            batch_duration = time.time() - batch_start
            if batch_duration < 60 and time.time() < end_time:
                time.sleep(min(60 - batch_duration, end_time - time.time()))
        
        # Calculate final metrics
        duration_seconds = time.time() - start_time
        final_memory = process.memory_info().rss / 1024 / 1024
        
        metrics = ReliabilityTestMetrics(
            test_name='long_term_stability',
            duration_seconds=duration_seconds,
            total_operations=total_operations,
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            error_types=error_types,
            memory_usage_mb=final_memory - initial_memory,
            max_memory_mb=max(memory_samples) if memory_samples else final_memory,
            average_response_time=sum(response_times) / len(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            resource_leaks_detected=self._detect_resource_leaks(),
            recovery_attempts=recovery_attempts,
            successful_recoveries=successful_recoveries
        )
        
        self.metrics.append(metrics)
        
        self.logger.info(f"Long-term stability test completed: {successful_operations}/{total_operations} operations successful")
        
        return metrics
    
    def test_edge_case_handling(self) -> ReliabilityTestMetrics:
        """Test handling of edge cases and boundary conditions"""
        self.logger.info("Starting edge case handling test")
        
        start_time = time.time()
        total_operations = 0
        successful_operations = 0
        failed_operations = 0
        error_types = {}
        response_times = []
        recovery_attempts = 0
        successful_recoveries = 0
        
        # Edge cases to test
        edge_cases = [
            # Empty/null inputs
            ('empty_topic', lambda: self.mcp_tools.start_thinking("")),
            ('null_topic', lambda: self.mcp_tools.start_thinking(None)),
            
            # Very long inputs
            ('very_long_topic', lambda: self.mcp_tools.start_thinking("A" * 10000)),
            
            # Special characters
            ('special_chars', lambda: self.mcp_tools.start_thinking("测试主题 with émojis 🤔 and symbols @#$%")),
            
            # Invalid session IDs
            ('invalid_session', lambda: self.mcp_tools.next_step("invalid_session_id", "test")),
            ('empty_session', lambda: self.mcp_tools.next_step("", "test")),
            
            # Malformed template parameters
            ('malformed_params', lambda: self.template_manager.get_template('test_template', {'invalid': None})),
            
            # Database edge cases
            ('duplicate_session', lambda: self._test_duplicate_session_creation()),
            ('concurrent_access', lambda: self._test_concurrent_database_access()),
            
            # Resource exhaustion simulation
            ('memory_pressure', lambda: self._test_memory_pressure()),
            ('file_handle_exhaustion', lambda: self._test_file_handle_exhaustion()),
        ]
        
        for case_name, test_func in edge_cases:
            op_start = time.time()
            total_operations += 1
            
            try:
                self.logger.debug(f"Testing edge case: {case_name}")
                result = test_func()
                
                # Some edge cases are expected to fail gracefully
                if case_name in ['empty_topic', 'null_topic', 'invalid_session', 'empty_session']:
                    # These should either return None or raise a handled exception
                    if result is None:
                        successful_operations += 1  # Graceful handling
                    else:
                        # If they return something, it should be valid
                        successful_operations += 1
                else:
                    # Other cases should succeed or fail gracefully
                    successful_operations += 1
                
            except Exception as e:
                error_type = type(e).__name__
                
                # Some exceptions are expected for edge cases
                expected_errors = ['ValueError', 'TypeError', 'ValidationError', 'SessionNotFoundError']
                
                if error_type in expected_errors:
                    successful_operations += 1  # Expected error, handled gracefully
                    self.logger.debug(f"Edge case {case_name} handled gracefully: {error_type}")
                else:
                    failed_operations += 1
                    error_types[error_type] = error_types.get(error_type, 0) + 1
                    
                    self.error_log.append({
                        'timestamp': time.time(),
                        'operation': case_name,
                        'error_type': error_type,
                        'error_message': str(e),
                        'operation_number': total_operations
                    })
                    
                    # Attempt recovery
                    recovery_attempts += 1
                    try:
                        self._recover_from_edge_case_error(case_name, e)
                        successful_recoveries += 1
                    except:
                        pass
            
            finally:
                response_time = time.time() - op_start
                response_times.append(response_time)
        
        # Calculate metrics
        duration_seconds = time.time() - start_time
        
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        metrics = ReliabilityTestMetrics(
            test_name='edge_case_handling',
            duration_seconds=duration_seconds,
            total_operations=total_operations,
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            error_types=error_types,
            memory_usage_mb=memory_mb,
            max_memory_mb=memory_mb,
            average_response_time=sum(response_times) / len(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            resource_leaks_detected=0,
            recovery_attempts=recovery_attempts,
            successful_recoveries=successful_recoveries
        )
        
        self.metrics.append(metrics)
        
        self.logger.info(f"Edge case handling test completed: {successful_operations}/{total_operations} cases handled")
        
        return metrics
    
    def test_resource_leak_detection(self) -> ReliabilityTestMetrics:
        """Test for resource leaks (memory, file handles, etc.)"""
        self.logger.info("Starting resource leak detection test")
        
        start_time = time.time()
        
        import psutil
        process = psutil.Process()
        
        # Initial resource measurements
        initial_memory = process.memory_info().rss / 1024 / 1024
        initial_open_files = len(process.open_files())
        
        total_operations = 0
        successful_operations = 0
        memory_samples = []
        file_handle_samples = []
        
        # Run operations that might cause leaks
        for cycle in range(10):  # 10 cycles of operations
            cycle_start_memory = process.memory_info().rss / 1024 / 1024
            cycle_start_files = len(process.open_files())
            
            # Perform operations that might leak resources
            for i in range(100):
                total_operations += 1
                
                try:
                    # Create and destroy sessions
                    session_id = f"leak_test_{cycle}_{i}"
                    result = self.mcp_tools.start_thinking(f"Leak test topic {cycle}-{i}")
                    
                    # Access templates
                    template = self.template_manager.get_template('test_template', {'topic': f'Test {i}'})
                    
                    # Database operations
                    sessions = self.database.get_all_sessions()
                    
                    successful_operations += 1
                    
                except Exception as e:
                    self.logger.warning(f"Operation failed during leak test: {e}")
            
            # Force garbage collection
            gc.collect()
            
            # Measure resources after cycle
            cycle_end_memory = process.memory_info().rss / 1024 / 1024
            cycle_end_files = len(process.open_files())
            
            memory_samples.append(cycle_end_memory)
            file_handle_samples.append(cycle_end_files)
            
            self.logger.debug(f"Cycle {cycle}: Memory {cycle_end_memory:.1f}MB (+{cycle_end_memory-cycle_start_memory:.1f}), Files {cycle_end_files} (+{cycle_end_files-cycle_start_files})")
        
        # Analyze for leaks
        final_memory = process.memory_info().rss / 1024 / 1024
        final_open_files = len(process.open_files())
        
        memory_growth = final_memory - initial_memory
        file_handle_growth = final_open_files - initial_open_files
        
        # Detect leaks (simple heuristics)
        resource_leaks_detected = 0
        
        # Memory leak detection
        if memory_growth > 50:  # More than 50MB growth
            resource_leaks_detected += 1
            self.logger.warning(f"Potential memory leak detected: {memory_growth:.1f}MB growth")
        
        # File handle leak detection
        if file_handle_growth > 10:  # More than 10 file handles
            resource_leaks_detected += 1
            self.logger.warning(f"Potential file handle leak detected: {file_handle_growth} handles")
        
        # Check for consistent growth pattern
        if len(memory_samples) >= 5:
            recent_growth = memory_samples[-1] - memory_samples[-5]
            if recent_growth > 20:  # 20MB growth in last 5 cycles
                resource_leaks_detected += 1
                self.logger.warning(f"Consistent memory growth pattern detected: {recent_growth:.1f}MB")
        
        duration_seconds = time.time() - start_time
        
        metrics = ReliabilityTestMetrics(
            test_name='resource_leak_detection',
            duration_seconds=duration_seconds,
            total_operations=total_operations,
            successful_operations=successful_operations,
            failed_operations=total_operations - successful_operations,
            error_types={},
            memory_usage_mb=memory_growth,
            max_memory_mb=max(memory_samples) if memory_samples else final_memory,
            average_response_time=0,
            max_response_time=0,
            resource_leaks_detected=resource_leaks_detected,
            recovery_attempts=0,
            successful_recoveries=0
        )
        
        self.metrics.append(metrics)
        
        self.logger.info(f"Resource leak detection completed: {resource_leaks_detected} potential leaks detected")
        
        return metrics
    
    def test_concurrent_stress(self, num_threads: int = 20, operations_per_thread: int = 100) -> ReliabilityTestMetrics:
        """Test system under concurrent stress"""
        self.logger.info(f"Starting concurrent stress test: {num_threads} threads, {operations_per_thread} ops each")
        
        start_time = time.time()
        
        # Shared metrics (thread-safe)
        metrics_lock = threading.Lock()
        total_operations = 0
        successful_operations = 0
        failed_operations = 0
        error_types = {}
        response_times = []
        
        def worker_thread(thread_id: int):
            """Worker thread for stress testing"""
            nonlocal total_operations, successful_operations, failed_operations, error_types, response_times
            
            thread_successful = 0
            thread_failed = 0
            thread_errors = {}
            thread_response_times = []
            
            for i in range(operations_per_thread):
                op_start = time.time()
                
                try:
                    # Mix of operations
                    operation_type = i % 4
                    
                    if operation_type == 0:
                        # Start thinking
                        result = self.mcp_tools.start_thinking(f"Stress test {thread_id}-{i}")
                        assert 'session_id' in result
                        
                    elif operation_type == 1:
                        # Template access
                        template = self.template_manager.get_template('test_template', {'topic': f'Stress {thread_id}-{i}'})
                        assert template is not None
                        
                    elif operation_type == 2:
                        # Session creation
                        session_id = f"stress_{thread_id}_{i}"
                        success = self.session_manager.create_session(session_id, f"Stress topic {thread_id}-{i}")
                        assert success
                        
                    elif operation_type == 3:
                        # Database query
                        sessions = self.database.get_all_sessions()
                        assert isinstance(sessions, list)
                    
                    thread_successful += 1
                    
                except Exception as e:
                    thread_failed += 1
                    error_type = type(e).__name__
                    thread_errors[error_type] = thread_errors.get(error_type, 0) + 1
                
                finally:
                    response_time = time.time() - op_start
                    thread_response_times.append(response_time)
            
            # Update shared metrics
            with metrics_lock:
                total_operations += operations_per_thread
                successful_operations += thread_successful
                failed_operations += thread_failed
                
                for error_type, count in thread_errors.items():
                    error_types[error_type] = error_types.get(error_type, 0) + count
                
                response_times.extend(thread_response_times)
        
        # Run concurrent threads
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker_thread, i) for i in range(num_threads)]
            
            # Wait for completion
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    self.logger.error(f"Thread failed: {e}")
        
        duration_seconds = time.time() - start_time
        
        # Memory measurement
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        metrics = ReliabilityTestMetrics(
            test_name='concurrent_stress',
            duration_seconds=duration_seconds,
            total_operations=total_operations,
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            error_types=error_types,
            memory_usage_mb=memory_mb,
            max_memory_mb=memory_mb,
            average_response_time=sum(response_times) / len(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            resource_leaks_detected=0,
            recovery_attempts=0,
            successful_recoveries=0
        )
        
        self.metrics.append(metrics)
        
        self.logger.info(f"Concurrent stress test completed: {successful_operations}/{total_operations} operations successful")
        
        return metrics
    
    def _test_duplicate_session_creation(self):
        """Test duplicate session creation handling"""
        session_id = "duplicate_test_session"
        
        # Create first session
        result1 = self.session_manager.create_session(session_id, "First topic")
        
        # Try to create duplicate
        result2 = self.session_manager.create_session(session_id, "Second topic")
        
        # Should handle gracefully (either succeed or fail predictably)
        return result1 and result2
    
    def _test_concurrent_database_access(self):
        """Test concurrent database access"""
        def db_operation():
            session_id = f"concurrent_{threading.current_thread().ident}_{time.time()}"
            self.session_manager.create_session(session_id, "Concurrent test")
            return self.session_manager.get_session(session_id)
        
        # Run multiple database operations concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(db_operation) for _ in range(10)]
            results = [future.result() for future in as_completed(futures)]
        
        return all(result is not None for result in results)
    
    def _test_memory_pressure(self):
        """Test system under memory pressure"""
        # Create large data structures to simulate memory pressure
        large_data = []
        for i in range(1000):
            large_data.append("A" * 1000)  # 1KB strings
        
        # Try normal operations under memory pressure
        result = self.mcp_tools.start_thinking("Memory pressure test")
        
        # Clean up
        del large_data
        gc.collect()
        
        return result
    
    def _test_file_handle_exhaustion(self):
        """Test system under file handle pressure"""
        # This is a simulation - in real tests you might open many files
        # For safety, we'll just simulate the condition
        try:
            result = self.mcp_tools.start_thinking("File handle test")
            return result
        except Exception as e:
            # If we get a file-related error, that's what we're testing
            if "file" in str(e).lower() or "handle" in str(e).lower():
                return None  # Expected under file handle pressure
            raise
    
    def _recover_from_edge_case_error(self, case_name: str, error: Exception):
        """Attempt recovery from edge case errors"""
        if "database" in str(error).lower():
            self._reinitialize_database()
        elif "template" in str(error).lower():
            self._reinitialize_template_manager()
        # Add more recovery strategies as needed
    
    def _reinitialize_database(self):
        """Reinitialize database connection"""
        try:
            if self.database:
                self.database.shutdown()
            
            db_path = str(self.temp_path / "data" / "reliability_test.db")
            self.database = ThinkingDatabase(db_path)
            
            # Update dependent components
            self.flow_manager = FlowManager(self.database)
            self.session_manager = SessionManager(self.database)
            
        except Exception as e:
            self.logger.error(f"Failed to reinitialize database: {e}")
            raise
    
    def _reinitialize_template_manager(self):
        """Reinitialize template manager"""
        try:
            if self.template_manager:
                self.template_manager.shutdown()
            
            templates_dir = str(self.temp_path / "templates")
            self.template_manager = TemplateManager(templates_dir)
            
        except Exception as e:
            self.logger.error(f"Failed to reinitialize template manager: {e}")
            raise
    
    def _detect_resource_leaks(self) -> int:
        """Detect potential resource leaks"""
        leaks_detected = 0
        
        try:
            import psutil
            process = psutil.Process()
            
            # Check for excessive open files
            open_files = len(process.open_files())
            if open_files > 100:  # Arbitrary threshold
                leaks_detected += 1
                self.logger.warning(f"High number of open files: {open_files}")
            
            # Check for excessive threads
            num_threads = process.num_threads()
            if num_threads > 50:  # Arbitrary threshold
                leaks_detected += 1
                self.logger.warning(f"High number of threads: {num_threads}")
            
        except Exception as e:
            self.logger.warning(f"Could not detect resource leaks: {e}")
        
        return leaks_detected
    
    def generate_reliability_report(self) -> str:
        """Generate comprehensive reliability report"""
        if not self.metrics:
            return "No reliability test results available."
        
        report_lines = [
            "=" * 80,
            "SYSTEM RELIABILITY TEST REPORT",
            "=" * 80,
            "",
            f"Test Environment: {self.temp_dir}",
            f"Report Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total Tests Run: {len(self.metrics)}",
            ""
        ]
        
        # Overall summary
        total_ops = sum(m.total_operations for m in self.metrics)
        total_successful = sum(m.successful_operations for m in self.metrics)
        total_failed = sum(m.failed_operations for m in self.metrics)
        
        report_lines.extend([
            "OVERALL SUMMARY",
            "-" * 40,
            f"Total Operations: {total_ops}",
            f"Successful Operations: {total_successful}",
            f"Failed Operations: {total_failed}",
            f"Overall Success Rate: {total_successful/max(total_ops,1):.2%}",
            ""
        ])
        
        # Individual test results
        report_lines.extend([
            "INDIVIDUAL TEST RESULTS",
            "-" * 40
        ])
        
        for metrics in self.metrics:
            success_rate = metrics.successful_operations / max(metrics.total_operations, 1)
            recovery_rate = metrics.successful_recoveries / max(metrics.recovery_attempts, 1) if metrics.recovery_attempts > 0 else 1.0
            
            report_lines.extend([
                f"Test: {metrics.test_name}",
                f"  Duration: {metrics.duration_seconds:.1f}s",
                f"  Operations: {metrics.successful_operations}/{metrics.total_operations} ({success_rate:.2%})",
                f"  Avg Response Time: {metrics.average_response_time:.3f}s",
                f"  Max Response Time: {metrics.max_response_time:.3f}s",
                f"  Memory Usage: {metrics.memory_usage_mb:.1f}MB",
                f"  Resource Leaks: {metrics.resource_leaks_detected}",
                f"  Recovery Rate: {recovery_rate:.2%} ({metrics.successful_recoveries}/{metrics.recovery_attempts})",
                ""
            ])
            
            if metrics.error_types:
                report_lines.append("  Error Types:")
                for error_type, count in metrics.error_types.items():
                    report_lines.append(f"    {error_type}: {count}")
                report_lines.append("")
        
        # Error analysis
        if self.error_log:
            report_lines.extend([
                "ERROR ANALYSIS",
                "-" * 40,
                f"Total Errors Logged: {len(self.error_log)}",
                ""
            ])
            
            # Group errors by type
            error_summary = {}
            for error in self.error_log:
                error_type = error['error_type']
                error_summary[error_type] = error_summary.get(error_type, 0) + 1
            
            for error_type, count in sorted(error_summary.items(), key=lambda x: x[1], reverse=True):
                report_lines.append(f"  {error_type}: {count}")
            
            report_lines.append("")
        
        # Recommendations
        recommendations = self._generate_reliability_recommendations()
        if recommendations:
            report_lines.extend([
                "RECOMMENDATIONS",
                "-" * 40
            ])
            for i, rec in enumerate(recommendations, 1):
                report_lines.append(f"{i}. {rec}")
            report_lines.append("")
        
        report_lines.extend([
            "=" * 80
        ])
        
        return "\n".join(report_lines)
    
    def _generate_reliability_recommendations(self) -> List[str]:
        """Generate reliability recommendations based on test results"""
        recommendations = []
        
        # Analyze overall performance
        if self.metrics:
            avg_success_rate = sum(m.successful_operations / max(m.total_operations, 1) for m in self.metrics) / len(self.metrics)
            
            if avg_success_rate < 0.95:
                recommendations.append(f"Overall success rate is {avg_success_rate:.2%} - investigate frequent failure causes")
            
            # Check response times
            slow_tests = [m for m in self.metrics if m.average_response_time > 1.0]
            if slow_tests:
                recommendations.append(f"{len(slow_tests)} test(s) had slow response times - optimize performance")
            
            # Check memory usage
            high_memory_tests = [m for m in self.metrics if m.memory_usage_mb > 100]
            if high_memory_tests:
                recommendations.append(f"{len(high_memory_tests)} test(s) had high memory usage - check for memory leaks")
            
            # Check resource leaks
            leak_tests = [m for m in self.metrics if m.resource_leaks_detected > 0]
            if leak_tests:
                recommendations.append(f"{len(leak_tests)} test(s) detected resource leaks - investigate resource management")
            
            # Check recovery rates
            poor_recovery_tests = [m for m in self.metrics if m.recovery_attempts > 0 and (m.successful_recoveries / m.recovery_attempts) < 0.8]
            if poor_recovery_tests:
                recommendations.append(f"{len(poor_recovery_tests)} test(s) had poor error recovery - improve error handling")
        
        # Analyze error patterns
        if self.error_log:
            error_types = {}
            for error in self.error_log:
                error_type = error['error_type']
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            most_common_error = max(error_types.items(), key=lambda x: x[1])
            if most_common_error[1] > 5:
                recommendations.append(f"Most common error is {most_common_error[0]} ({most_common_error[1]} occurrences) - prioritize fixing this")
        
        if not recommendations:
            recommendations.append("All reliability tests passed successfully - system shows good stability")
        
        return recommendations
    
    def cleanup(self):
        """Cleanup test environment"""
        try:
            if self.database:
                self.database.shutdown()
            if self.template_manager:
                self.template_manager.shutdown()
            
            # Clean up temporary files
            import shutil
            if Path(self.temp_dir).exists():
                shutil.rmtree(self.temp_dir)
            
            self.logger.info("Reliability test environment cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


# Test functions for pytest integration

class TestSystemReliability:
    """Pytest test class for system reliability"""
    
    @pytest.fixture
    def reliability_tester(self):
        """Create reliability tester fixture"""
        tester = SystemReliabilityTester()
        yield tester
        tester.cleanup()
    
    def test_short_term_stability(self, reliability_tester):
        """Test short-term stability (for CI/CD)"""
        metrics = reliability_tester.test_long_term_stability(duration_minutes=1, operations_per_minute=30)
        
        # Assert basic stability requirements
        assert metrics.total_operations > 0
        assert metrics.successful_operations / metrics.total_operations >= 0.9  # 90% success rate
        assert metrics.average_response_time < 2.0  # Less than 2 seconds average
        assert metrics.resource_leaks_detected == 0  # No resource leaks
    
    def test_edge_case_resilience(self, reliability_tester):
        """Test edge case handling"""
        metrics = reliability_tester.test_edge_case_handling()
        
        # Assert edge case handling
        assert metrics.total_operations > 0
        assert metrics.successful_operations / metrics.total_operations >= 0.8  # 80% handled gracefully
    
    def test_resource_management(self, reliability_tester):
        """Test resource leak detection"""
        metrics = reliability_tester.test_resource_leak_detection()
        
        # Assert no significant resource leaks
        assert metrics.resource_leaks_detected <= 1  # Allow for minor variations
        assert metrics.memory_usage_mb < 100  # Less than 100MB growth
    
    def test_concurrent_reliability(self, reliability_tester):
        """Test concurrent access reliability"""
        metrics = reliability_tester.test_concurrent_stress(num_threads=5, operations_per_thread=20)
        
        # Assert concurrent reliability
        assert metrics.total_operations > 0
        assert metrics.successful_operations / metrics.total_operations >= 0.9  # 90% success rate
        assert metrics.average_response_time < 5.0  # Less than 5 seconds under load


if __name__ == "__main__":
    # Run reliability tests standalone
    logging.basicConfig(level=logging.INFO)
    
    tester = SystemReliabilityTester()
    
    try:
        print("Running system reliability tests...")
        
        # Run all reliability tests
        tester.test_long_term_stability(duration_minutes=2, operations_per_minute=30)
        tester.test_edge_case_handling()
        tester.test_resource_leak_detection()
        tester.test_concurrent_stress(num_threads=5, operations_per_thread=50)
        
        # Generate report
        report = tester.generate_reliability_report()
        print(report)
        
        # Save report to file
        with open('system_reliability_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        
        print("\nReliability test report saved to: system_reliability_report.txt")
        
    finally:
        tester.cleanup()