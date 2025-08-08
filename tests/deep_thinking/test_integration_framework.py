"""
Integration Testing Framework for Deep Thinking Engine

This comprehensive integration testing framework provides:
1. End-to-end workflow testing
2. Multi-scenario integration test cases
3. System stability and reliability testing
4. Automated test execution and reporting

Requirements: 集成测试，系统验证
"""

import asyncio
import json
import logging
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from unittest.mock import MagicMock, patch
import pytest

from src.mcps.deep_thinking.config.config_manager import ConfigManager
from src.mcps.deep_thinking.data.database import ThinkingDatabase
from src.mcps.deep_thinking.flows.flow_executor import FlowExecutor
from src.mcps.deep_thinking.flows.flow_manager import FlowManager
from src.mcps.deep_thinking.sessions.session_manager import SessionManager
from src.mcps.deep_thinking.templates.template_manager import TemplateManager
from src.mcps.deep_thinking.tools.mcp_tools import MCPTools


@dataclass
class IntegrationTestResult:
    """Result of an integration test"""
    test_name: str
    success: bool
    execution_time: float
    error_message: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class SystemStabilityMetrics:
    """System stability metrics"""
    total_operations: int
    successful_operations: int
    failed_operations: int
    average_response_time: float
    max_response_time: float
    min_response_time: float
    memory_usage_mb: float
    error_rate: float
    uptime_seconds: float


class IntegrationTestFramework:
    """Comprehensive integration testing framework"""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """Initialize the integration test framework"""
        self.temp_dir = temp_dir or tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Test results storage
        self.test_results: List[IntegrationTestResult] = []
        self.stability_metrics: Optional[SystemStabilityMetrics] = None
        
        # System components
        self.config_manager: Optional[ConfigManager] = None
        self.database: Optional[ThinkingDatabase] = None
        self.template_manager: Optional[TemplateManager] = None
        self.flow_manager: Optional[FlowManager] = None
        self.flow_executor: Optional[FlowExecutor] = None
        self.session_manager: Optional[SessionManager] = None
        self.mcp_tools: Optional[MCPTools] = None
        
        # Test configuration
        self.logger = logging.getLogger(__name__)
        self.setup_test_environment()
    
    def setup_test_environment(self):
        """Setup the test environment with all necessary components"""
        try:
            # Create test directories
            (self.temp_path / "config").mkdir(exist_ok=True)
            (self.temp_path / "templates").mkdir(exist_ok=True)
            (self.temp_path / "data").mkdir(exist_ok=True)
            
            # Create test configuration files
            self._create_test_config_files()
            self._create_test_templates()
            
            # Initialize components
            self._initialize_components()
            
            self.logger.info(f"Integration test environment setup complete: {self.temp_dir}")
            
        except Exception as e:
            self.logger.error(f"Failed to setup test environment: {e}")
            raise
    
    def _create_test_config_files(self):
        """Create test configuration files"""
        # System config
        system_config = {
            'database': {
                'path': str(self.temp_path / "data" / "test.db"),
                'enable_wal': True,
                'connection_timeout': 30
            },
            'templates': {
                'directory': str(self.temp_path / "templates"),
                'cache_size': 100,
                'hot_reload': True
            },
            'performance': {
                'enable_optimization': True,
                'monitoring_interval': 1.0
            }
        }
        
        with open(self.temp_path / "config" / "system.yaml", 'w') as f:
            import yaml
            yaml.dump(system_config, f)
        
        # Flow config
        flow_config = {
            'flows': {
                'test_comprehensive': {
                    'name': 'Test Comprehensive Analysis',
                    'description': 'Test flow for integration testing',
                    'steps': [
                        {
                            'step': 'decompose_problem',
                            'template': 'decomposition',
                            'required': True
                        },
                        {
                            'step': 'collect_evidence',
                            'template': 'evidence_collection',
                            'depends_on': ['decompose_problem']
                        },
                        {
                            'step': 'critical_evaluation',
                            'template': 'critical_evaluation',
                            'depends_on': ['collect_evidence']
                        }
                    ]
                },
                'test_simple': {
                    'name': 'Test Simple Analysis',
                    'description': 'Simple test flow',
                    'steps': [
                        {
                            'step': 'basic_analysis',
                            'template': 'basic_template',
                            'required': True
                        }
                    ]
                }
            }
        }
        
        with open(self.temp_path / "config" / "flows.yaml", 'w') as f:
            import yaml
            yaml.dump(flow_config, f)
    
    def _create_test_templates(self):
        """Create test templates"""
        templates = {
            'decomposition.tmpl': '''# 问题分解模板

请分解以下问题：{topic}

## 分解要求
1. 分解为3-5个子问题
2. 确保逻辑清晰
3. 标注优先级

请开始分解：
''',
            'evidence_collection.tmpl': '''# 证据收集模板

为以下问题收集证据：{topic}

## 收集要求
1. 多源证据
2. 权威来源
3. 时效性强

请开始收集：
''',
            'critical_evaluation.tmpl': '''# 批判性评估模板

评估以下内容：{content}

## 评估标准
1. 准确性
2. 逻辑性
3. 完整性

请开始评估：
''',
            'basic_template.tmpl': '''# 基础分析模板

分析主题：{topic}

请进行基础分析。
'''
        }
        
        for filename, content in templates.items():
            (self.temp_path / "templates" / filename).write_text(content, encoding='utf-8')
    
    def _initialize_components(self):
        """Initialize all system components"""
        # Config manager
        self.config_manager = ConfigManager(str(self.temp_path / "config"))
        
        # Database
        db_path = str(self.temp_path / "data" / "test.db")
        self.database = ThinkingDatabase(db_path)
        
        # Template manager
        templates_dir = str(self.temp_path / "templates")
        self.template_manager = TemplateManager(templates_dir)
        
        # Flow manager
        self.flow_manager = FlowManager(self.database)
        
        # Flow executor
        self.flow_executor = FlowExecutor(
            flow_manager=self.flow_manager,
            template_manager=self.template_manager,
            db=self.database
        )
        
        # Session manager
        self.session_manager = SessionManager(self.database)
        
        # MCP tools
        self.mcp_tools = MCPTools(
            session_manager=self.session_manager,
            flow_manager=self.flow_manager,
            template_manager=self.template_manager,
            flow_executor=self.flow_executor
        )
    
    def run_end_to_end_test(self, test_name: str, scenario: Dict[str, Any]) -> IntegrationTestResult:
        """Run an end-to-end test scenario"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting end-to-end test: {test_name}")
            
            # Extract scenario parameters
            topic = scenario.get('topic', 'Test topic')
            flow_type = scenario.get('flow_type', 'test_comprehensive')
            expected_steps = scenario.get('expected_steps', 3)
            
            # Step 1: Start thinking
            start_result = self.mcp_tools.start_thinking(topic, complexity="moderate")
            assert 'session_id' in start_result
            assert 'prompt_template' in start_result
            session_id = start_result['session_id']
            
            # Step 2: Execute flow steps
            step_results = []
            current_step = 0
            
            while current_step < expected_steps:
                # Get next step
                next_result = self.mcp_tools.next_step(session_id, f"Step {current_step} result")
                assert 'step' in next_result
                assert 'prompt_template' in next_result
                
                step_results.append(next_result)
                current_step += 1
                
                # Analyze step if needed
                if current_step % 2 == 0:  # Analyze every other step
                    analyze_result = self.mcp_tools.analyze_step(
                        session_id, 
                        next_result['step'], 
                        f"Analysis for step {current_step}"
                    )
                    assert 'analysis_prompt' in analyze_result
            
            # Step 3: Complete thinking
            complete_result = self.mcp_tools.complete_thinking(session_id)
            assert 'status' in complete_result
            assert complete_result['status'] == 'completed'
            
            # Collect metrics
            metrics = {
                'session_id': session_id,
                'steps_executed': len(step_results),
                'completion_status': complete_result['status'],
                'flow_type': flow_type
            }
            
            execution_time = time.time() - start_time
            
            self.logger.info(f"End-to-end test {test_name} completed successfully in {execution_time:.3f}s")
            
            return IntegrationTestResult(
                test_name=test_name,
                success=True,
                execution_time=execution_time,
                metrics=metrics,
                details={'step_results': step_results, 'complete_result': complete_result}
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"End-to-end test {test_name} failed: {e}")
            
            return IntegrationTestResult(
                test_name=test_name,
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    def run_multi_scenario_tests(self) -> List[IntegrationTestResult]:
        """Run multiple integration test scenarios"""
        scenarios = [
            {
                'name': 'comprehensive_analysis_scenario',
                'topic': '如何提高教育质量？',
                'flow_type': 'test_comprehensive',
                'expected_steps': 3
            },
            {
                'name': 'simple_analysis_scenario',
                'topic': '什么是人工智能？',
                'flow_type': 'test_simple',
                'expected_steps': 1
            },
            {
                'name': 'complex_topic_scenario',
                'topic': '气候变化对全球经济的长期影响及应对策略',
                'flow_type': 'test_comprehensive',
                'expected_steps': 3
            },
            {
                'name': 'technical_topic_scenario',
                'topic': '量子计算在密码学中的应用前景',
                'flow_type': 'test_comprehensive',
                'expected_steps': 3
            },
            {
                'name': 'social_topic_scenario',
                'topic': '社交媒体对青少年心理健康的影响',
                'flow_type': 'test_comprehensive',
                'expected_steps': 3
            }
        ]
        
        results = []
        
        for scenario in scenarios:
            result = self.run_end_to_end_test(scenario['name'], scenario)
            results.append(result)
            self.test_results.append(result)
        
        return results
    
    def run_stability_test(self, duration_seconds: int = 60, operations_per_second: int = 5) -> SystemStabilityMetrics:
        """Run system stability and reliability test"""
        self.logger.info(f"Starting stability test: {duration_seconds}s duration, {operations_per_second} ops/sec")
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        # Metrics tracking
        total_operations = 0
        successful_operations = 0
        failed_operations = 0
        response_times = []
        errors = []
        
        # Memory tracking
        import psutil
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        def run_operation():
            """Run a single test operation"""
            nonlocal total_operations, successful_operations, failed_operations
            
            op_start = time.time()
            total_operations += 1
            
            try:
                # Randomly choose operation type
                import random
                operation_type = random.choice(['start_thinking', 'simple_query', 'template_access'])
                
                if operation_type == 'start_thinking':
                    result = self.mcp_tools.start_thinking(f"Test topic {total_operations}")
                    assert 'session_id' in result
                    
                elif operation_type == 'simple_query':
                    # Create a session and query it
                    session_id = f"test_session_{total_operations}"
                    self.session_manager.create_session(session_id, f"Test topic {total_operations}")
                    session = self.session_manager.get_session(session_id)
                    assert session is not None
                    
                elif operation_type == 'template_access':
                    template = self.template_manager.get_template('basic_template', {'topic': f'Test {total_operations}'})
                    assert template is not None
                
                successful_operations += 1
                
            except Exception as e:
                failed_operations += 1
                errors.append(str(e))
            
            finally:
                response_time = time.time() - op_start
                response_times.append(response_time)
        
        # Run operations continuously
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            
            while time.time() < end_time:
                # Submit operations at the desired rate
                for _ in range(operations_per_second):
                    if time.time() >= end_time:
                        break
                    future = executor.submit(run_operation)
                    futures.append(future)
                
                # Wait a bit before next batch
                time.sleep(1.0)
            
            # Wait for all operations to complete
            for future in as_completed(futures, timeout=30):
                try:
                    future.result()
                except Exception as e:
                    self.logger.error(f"Operation failed: {e}")
        
        # Calculate final metrics
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        uptime = time.time() - start_time
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
        else:
            avg_response_time = max_response_time = min_response_time = 0.0
        
        error_rate = failed_operations / max(total_operations, 1)
        
        self.stability_metrics = SystemStabilityMetrics(
            total_operations=total_operations,
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            average_response_time=avg_response_time,
            max_response_time=max_response_time,
            min_response_time=min_response_time,
            memory_usage_mb=final_memory - initial_memory,
            error_rate=error_rate,
            uptime_seconds=uptime
        )
        
        self.logger.info(f"Stability test completed: {successful_operations}/{total_operations} operations successful")
        
        return self.stability_metrics
    
    def run_concurrent_access_test(self, num_threads: int = 10, operations_per_thread: int = 20) -> IntegrationTestResult:
        """Test concurrent access to system components"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting concurrent access test: {num_threads} threads, {operations_per_thread} ops each")
            
            results = []
            errors = []
            
            def worker_thread(thread_id: int):
                """Worker thread function"""
                thread_results = []
                
                for i in range(operations_per_thread):
                    try:
                        # Create unique session
                        session_id = f"concurrent_session_{thread_id}_{i}"
                        topic = f"Concurrent test topic {thread_id}-{i}"
                        
                        # Start thinking
                        start_result = self.mcp_tools.start_thinking(topic)
                        thread_results.append(('start_thinking', True, start_result['session_id']))
                        
                        # Get next step
                        next_result = self.mcp_tools.next_step(start_result['session_id'], "Test result")
                        thread_results.append(('next_step', True, next_result['step']))
                        
                        # Access template
                        template = self.template_manager.get_template('basic_template', {'topic': topic})
                        thread_results.append(('template_access', True, len(template)))
                        
                    except Exception as e:
                        thread_results.append(('error', False, str(e)))
                        errors.append(f"Thread {thread_id}, operation {i}: {e}")
                
                return thread_results
            
            # Run concurrent threads
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(worker_thread, i) for i in range(num_threads)]
                
                for future in as_completed(futures):
                    thread_results = future.result()
                    results.extend(thread_results)
            
            # Analyze results
            total_ops = len(results)
            successful_ops = sum(1 for _, success, _ in results if success)
            failed_ops = total_ops - successful_ops
            
            execution_time = time.time() - start_time
            
            metrics = {
                'total_operations': total_ops,
                'successful_operations': successful_ops,
                'failed_operations': failed_ops,
                'success_rate': successful_ops / max(total_ops, 1),
                'num_threads': num_threads,
                'operations_per_thread': operations_per_thread
            }
            
            success = failed_ops == 0 and len(errors) == 0
            
            self.logger.info(f"Concurrent access test completed: {successful_ops}/{total_ops} operations successful")
            
            return IntegrationTestResult(
                test_name='concurrent_access_test',
                success=success,
                execution_time=execution_time,
                metrics=metrics,
                details={'errors': errors, 'results': results}
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Concurrent access test failed: {e}")
            
            return IntegrationTestResult(
                test_name='concurrent_access_test',
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    def run_error_recovery_test(self) -> IntegrationTestResult:
        """Test error recovery and resilience"""
        start_time = time.time()
        
        try:
            self.logger.info("Starting error recovery test")
            
            recovery_scenarios = []
            
            # Scenario 1: Invalid session ID
            try:
                result = self.mcp_tools.next_step("invalid_session_id", "test result")
                recovery_scenarios.append(('invalid_session', True, 'Handled gracefully'))
            except Exception as e:
                recovery_scenarios.append(('invalid_session', False, str(e)))
            
            # Scenario 2: Missing template
            try:
                template = self.template_manager.get_template('nonexistent_template', {'param': 'value'})
                recovery_scenarios.append(('missing_template', template is None, 'Returned None'))
            except Exception as e:
                recovery_scenarios.append(('missing_template', False, str(e)))
            
            # Scenario 3: Database connection issues (simulate)
            try:
                # Create a session first
                session_id = "recovery_test_session"
                self.mcp_tools.start_thinking("Recovery test topic")
                
                # Try to access it
                session = self.session_manager.get_session(session_id)
                recovery_scenarios.append(('database_access', True, 'Database accessible'))
            except Exception as e:
                recovery_scenarios.append(('database_access', False, str(e)))
            
            # Scenario 4: Malformed input
            try:
                result = self.mcp_tools.start_thinking("")  # Empty topic
                recovery_scenarios.append(('empty_input', True, 'Handled empty input'))
            except Exception as e:
                recovery_scenarios.append(('empty_input', False, str(e)))
            
            # Scenario 5: Resource exhaustion simulation
            try:
                # Create many sessions quickly
                for i in range(100):
                    self.mcp_tools.start_thinking(f"Stress test topic {i}")
                recovery_scenarios.append(('resource_stress', True, 'Handled resource stress'))
            except Exception as e:
                recovery_scenarios.append(('resource_stress', False, str(e)))
            
            execution_time = time.time() - start_time
            
            # Analyze recovery performance
            total_scenarios = len(recovery_scenarios)
            successful_recoveries = sum(1 for _, success, _ in recovery_scenarios if success)
            
            metrics = {
                'total_scenarios': total_scenarios,
                'successful_recoveries': successful_recoveries,
                'recovery_rate': successful_recoveries / max(total_scenarios, 1),
                'scenarios': recovery_scenarios
            }
            
            success = successful_recoveries >= total_scenarios * 0.8  # 80% recovery rate threshold
            
            self.logger.info(f"Error recovery test completed: {successful_recoveries}/{total_scenarios} scenarios handled")
            
            return IntegrationTestResult(
                test_name='error_recovery_test',
                success=success,
                execution_time=execution_time,
                metrics=metrics,
                details={'recovery_scenarios': recovery_scenarios}
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Error recovery test failed: {e}")
            
            return IntegrationTestResult(
                test_name='error_recovery_test',
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    def run_comprehensive_integration_test_suite(self) -> Dict[str, Any]:
        """Run the complete integration test suite"""
        self.logger.info("Starting comprehensive integration test suite")
        suite_start_time = time.time()
        
        # Clear previous results
        self.test_results.clear()
        
        # 1. Multi-scenario end-to-end tests
        self.logger.info("Running multi-scenario tests...")
        scenario_results = self.run_multi_scenario_tests()
        
        # 2. Concurrent access test
        self.logger.info("Running concurrent access test...")
        concurrent_result = self.run_concurrent_access_test()
        self.test_results.append(concurrent_result)
        
        # 3. Error recovery test
        self.logger.info("Running error recovery test...")
        recovery_result = self.run_error_recovery_test()
        self.test_results.append(recovery_result)
        
        # 4. System stability test (shorter duration for testing)
        self.logger.info("Running stability test...")
        stability_metrics = self.run_stability_test(duration_seconds=30, operations_per_second=3)
        
        # Calculate overall results
        total_execution_time = time.time() - suite_start_time
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result.success)
        failed_tests = total_tests - successful_tests
        
        # Generate comprehensive report
        report = {
            'suite_summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': failed_tests,
                'success_rate': successful_tests / max(total_tests, 1),
                'total_execution_time': total_execution_time
            },
            'test_results': [
                {
                    'name': result.test_name,
                    'success': result.success,
                    'execution_time': result.execution_time,
                    'error_message': result.error_message,
                    'metrics': result.metrics
                }
                for result in self.test_results
            ],
            'stability_metrics': {
                'total_operations': stability_metrics.total_operations,
                'successful_operations': stability_metrics.successful_operations,
                'failed_operations': stability_metrics.failed_operations,
                'success_rate': stability_metrics.successful_operations / max(stability_metrics.total_operations, 1),
                'average_response_time': stability_metrics.average_response_time,
                'max_response_time': stability_metrics.max_response_time,
                'error_rate': stability_metrics.error_rate,
                'memory_usage_mb': stability_metrics.memory_usage_mb,
                'uptime_seconds': stability_metrics.uptime_seconds
            },
            'recommendations': self._generate_recommendations()
        }
        
        self.logger.info(f"Integration test suite completed: {successful_tests}/{total_tests} tests passed")
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Analyze test results
        failed_tests = [result for result in self.test_results if not result.success]
        
        if failed_tests:
            recommendations.append(f"Address {len(failed_tests)} failed test(s) to improve system reliability")
        
        # Analyze stability metrics
        if self.stability_metrics:
            if self.stability_metrics.error_rate > 0.05:  # 5% error rate threshold
                recommendations.append(f"High error rate ({self.stability_metrics.error_rate:.2%}) - investigate error handling")
            
            if self.stability_metrics.average_response_time > 1.0:  # 1 second threshold
                recommendations.append(f"Slow average response time ({self.stability_metrics.average_response_time:.3f}s) - optimize performance")
            
            if self.stability_metrics.memory_usage_mb > 100:  # 100MB threshold
                recommendations.append(f"High memory usage ({self.stability_metrics.memory_usage_mb:.1f}MB) - check for memory leaks")
        
        # Analyze concurrent access results
        concurrent_results = [result for result in self.test_results if result.test_name == 'concurrent_access_test']
        if concurrent_results and not concurrent_results[0].success:
            recommendations.append("Concurrent access issues detected - review thread safety")
        
        # Analyze error recovery results
        recovery_results = [result for result in self.test_results if result.test_name == 'error_recovery_test']
        if recovery_results and recovery_results[0].metrics:
            recovery_rate = recovery_results[0].metrics.get('recovery_rate', 0)
            if recovery_rate < 0.8:
                recommendations.append(f"Low error recovery rate ({recovery_rate:.2%}) - improve error handling")
        
        if not recommendations:
            recommendations.append("All tests passed successfully - system is performing well")
        
        return recommendations
    
    def generate_test_report(self) -> str:
        """Generate a comprehensive test report"""
        if not self.test_results:
            return "No test results available. Run tests first."
        
        report_lines = [
            "=" * 80,
            "DEEP THINKING ENGINE - INTEGRATION TEST REPORT",
            "=" * 80,
            "",
            f"Test Environment: {self.temp_dir}",
            f"Report Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "SUMMARY",
            "-" * 40
        ]
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result.success)
        failed_tests = total_tests - successful_tests
        
        report_lines.extend([
            f"Total Tests: {total_tests}",
            f"Successful: {successful_tests}",
            f"Failed: {failed_tests}",
            f"Success Rate: {successful_tests/max(total_tests,1):.1%}",
            ""
        ])
        
        # Test details
        report_lines.extend([
            "TEST DETAILS",
            "-" * 40
        ])
        
        for result in self.test_results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            report_lines.append(f"{status} {result.test_name} ({result.execution_time:.3f}s)")
            
            if result.error_message:
                report_lines.append(f"    Error: {result.error_message}")
            
            if result.metrics:
                for key, value in result.metrics.items():
                    if isinstance(value, (int, float)):
                        report_lines.append(f"    {key}: {value}")
        
        # Stability metrics
        if self.stability_metrics:
            report_lines.extend([
                "",
                "STABILITY METRICS",
                "-" * 40,
                f"Total Operations: {self.stability_metrics.total_operations}",
                f"Successful Operations: {self.stability_metrics.successful_operations}",
                f"Failed Operations: {self.stability_metrics.failed_operations}",
                f"Success Rate: {self.stability_metrics.successful_operations/max(self.stability_metrics.total_operations,1):.1%}",
                f"Average Response Time: {self.stability_metrics.average_response_time:.3f}s",
                f"Max Response Time: {self.stability_metrics.max_response_time:.3f}s",
                f"Error Rate: {self.stability_metrics.error_rate:.2%}",
                f"Memory Usage: {self.stability_metrics.memory_usage_mb:.1f}MB",
                f"Uptime: {self.stability_metrics.uptime_seconds:.1f}s"
            ])
        
        # Recommendations
        recommendations = self._generate_recommendations()
        if recommendations:
            report_lines.extend([
                "",
                "RECOMMENDATIONS",
                "-" * 40
            ])
            for i, rec in enumerate(recommendations, 1):
                report_lines.append(f"{i}. {rec}")
        
        report_lines.extend([
            "",
            "=" * 80
        ])
        
        return "\n".join(report_lines)
    
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
            
            self.logger.info("Integration test environment cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


# Automated test execution functions

def run_automated_integration_tests(output_file: Optional[str] = None) -> bool:
    """Run automated integration tests and return success status"""
    framework = None
    
    try:
        # Initialize framework
        framework = IntegrationTestFramework()
        
        # Run comprehensive test suite
        results = framework.run_comprehensive_integration_test_suite()
        
        # Generate report
        report = framework.generate_test_report()
        
        # Output report
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"Integration test report saved to: {output_file}")
        else:
            print(report)
        
        # Return success status
        success = results['suite_summary']['failed_tests'] == 0
        
        if success:
            print("\n🎉 All integration tests passed!")
        else:
            print(f"\n⚠️  {results['suite_summary']['failed_tests']} integration test(s) failed")
        
        return success
        
    except Exception as e:
        print(f"❌ Integration test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if framework:
            framework.cleanup()


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    output_file = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Run tests
    success = run_automated_integration_tests(output_file)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)