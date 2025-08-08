#!/usr/bin/env python3
"""
Automated Integration Test Runner

This script provides automated execution of the comprehensive integration test suite
for the Deep Thinking Engine. It supports various execution modes and reporting options.

Usage:
    python scripts/run_integration_tests.py [options]

Requirements: 集成测试，系统验证
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tests.deep_thinking.test_integration_framework import (
    IntegrationTestFramework,
    run_automated_integration_tests
)


class IntegrationTestRunner:
    """Automated integration test runner with advanced features"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the test runner"""
        self.config = config or {}
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration"""
        log_level = self.config.get('log_level', 'INFO')
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format=log_format,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('integration_tests.log')
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def run_quick_test_suite(self) -> Dict[str, Any]:
        """Run a quick integration test suite (reduced scope)"""
        self.logger.info("Running quick integration test suite...")
        
        framework = IntegrationTestFramework()
        
        try:
            # Run a subset of tests for quick validation
            results = []
            
            # Quick end-to-end test
            scenario = {
                'topic': '快速测试主题',
                'flow_type': 'test_simple',
                'expected_steps': 1
            }
            result = framework.run_end_to_end_test('quick_e2e_test', scenario)
            results.append(result)
            
            # Quick concurrent test (reduced load)
            concurrent_result = framework.run_concurrent_access_test(num_threads=3, operations_per_thread=5)
            results.append(concurrent_result)
            
            # Quick stability test (very short)
            stability_metrics = framework.run_stability_test(duration_seconds=10, operations_per_second=2)
            
            # Calculate summary
            total_tests = len(results)
            successful_tests = sum(1 for r in results if r.success)
            
            return {
                'test_type': 'quick',
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': total_tests - successful_tests,
                'success_rate': successful_tests / max(total_tests, 1),
                'stability_metrics': {
                    'total_operations': stability_metrics.total_operations,
                    'success_rate': stability_metrics.successful_operations / max(stability_metrics.total_operations, 1),
                    'average_response_time': stability_metrics.average_response_time,
                    'error_rate': stability_metrics.error_rate
                },
                'results': results
            }
            
        finally:
            framework.cleanup()
    
    def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """Run the full comprehensive integration test suite"""
        self.logger.info("Running comprehensive integration test suite...")
        
        framework = IntegrationTestFramework()
        
        try:
            return framework.run_comprehensive_integration_test_suite()
        finally:
            framework.cleanup()
    
    def run_stress_test_suite(self) -> Dict[str, Any]:
        """Run stress testing with high load"""
        self.logger.info("Running stress test suite...")
        
        framework = IntegrationTestFramework()
        
        try:
            results = []
            
            # High-load concurrent test
            concurrent_result = framework.run_concurrent_access_test(num_threads=20, operations_per_thread=50)
            results.append(concurrent_result)
            
            # Extended stability test
            stability_metrics = framework.run_stability_test(duration_seconds=120, operations_per_second=10)
            
            # Memory stress test
            memory_stress_result = self._run_memory_stress_test(framework)
            results.append(memory_stress_result)
            
            # Calculate summary
            total_tests = len(results)
            successful_tests = sum(1 for r in results if r.success)
            
            return {
                'test_type': 'stress',
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': total_tests - successful_tests,
                'success_rate': successful_tests / max(total_tests, 1),
                'stability_metrics': {
                    'total_operations': stability_metrics.total_operations,
                    'success_rate': stability_metrics.successful_operations / max(stability_metrics.total_operations, 1),
                    'average_response_time': stability_metrics.average_response_time,
                    'max_response_time': stability_metrics.max_response_time,
                    'error_rate': stability_metrics.error_rate,
                    'memory_usage_mb': stability_metrics.memory_usage_mb
                },
                'results': results
            }
            
        finally:
            framework.cleanup()
    
    def _run_memory_stress_test(self, framework: IntegrationTestFramework) -> Any:
        """Run memory stress test"""
        from tests.deep_thinking.test_integration_framework import IntegrationTestResult
        
        start_time = time.time()
        
        try:
            self.logger.info("Running memory stress test...")
            
            # Create many sessions to test memory usage
            session_ids = []
            for i in range(1000):
                result = framework.mcp_tools.start_thinking(f"Memory stress test topic {i}")
                session_ids.append(result['session_id'])
                
                # Every 100 sessions, check memory
                if i % 100 == 0:
                    import psutil
                    process = psutil.Process()
                    memory_mb = process.memory_info().rss / 1024 / 1024
                    self.logger.info(f"Created {i+1} sessions, memory usage: {memory_mb:.1f}MB")
            
            execution_time = time.time() - start_time
            
            # Final memory check
            import psutil
            process = psutil.Process()
            final_memory_mb = process.memory_info().rss / 1024 / 1024
            
            metrics = {
                'sessions_created': len(session_ids),
                'final_memory_mb': final_memory_mb,
                'memory_per_session_kb': (final_memory_mb * 1024) / max(len(session_ids), 1)
            }
            
            # Consider test successful if memory usage is reasonable
            success = final_memory_mb < 500  # Less than 500MB
            
            return IntegrationTestResult(
                test_name='memory_stress_test',
                success=success,
                execution_time=execution_time,
                metrics=metrics
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return IntegrationTestResult(
                test_name='memory_stress_test',
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    def run_regression_test_suite(self) -> Dict[str, Any]:
        """Run regression tests to ensure no functionality breaks"""
        self.logger.info("Running regression test suite...")
        
        framework = IntegrationTestFramework()
        
        try:
            results = []
            
            # Test all core MCP tools
            mcp_tools_tests = [
                ('start_thinking_regression', lambda: framework.mcp_tools.start_thinking("回归测试主题")),
                ('template_access_regression', lambda: framework.template_manager.get_template('basic_template', {'topic': '回归测试'})),
                ('session_management_regression', lambda: framework.session_manager.create_session('regression_test', '回归测试主题')),
            ]
            
            for test_name, test_func in mcp_tools_tests:
                start_time = time.time()
                try:
                    result = test_func()
                    execution_time = time.time() - start_time
                    
                    from tests.deep_thinking.test_integration_framework import IntegrationTestResult
                    test_result = IntegrationTestResult(
                        test_name=test_name,
                        success=result is not None,
                        execution_time=execution_time,
                        metrics={'result_type': type(result).__name__}
                    )
                    results.append(test_result)
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    from tests.deep_thinking.test_integration_framework import IntegrationTestResult
                    test_result = IntegrationTestResult(
                        test_name=test_name,
                        success=False,
                        execution_time=execution_time,
                        error_message=str(e)
                    )
                    results.append(test_result)
            
            # Run error recovery test
            recovery_result = framework.run_error_recovery_test()
            results.append(recovery_result)
            
            # Calculate summary
            total_tests = len(results)
            successful_tests = sum(1 for r in results if r.success)
            
            return {
                'test_type': 'regression',
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': total_tests - successful_tests,
                'success_rate': successful_tests / max(total_tests, 1),
                'results': results
            }
            
        finally:
            framework.cleanup()
    
    def generate_json_report(self, results: Dict[str, Any], output_file: str):
        """Generate JSON report"""
        # Convert IntegrationTestResult objects to dictionaries
        if 'results' in results:
            serializable_results = []
            for result in results['results']:
                if hasattr(result, '__dict__'):
                    serializable_results.append({
                        'test_name': result.test_name,
                        'success': result.success,
                        'execution_time': result.execution_time,
                        'error_message': result.error_message,
                        'metrics': result.metrics
                    })
                else:
                    serializable_results.append(result)
            results['results'] = serializable_results
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"JSON report saved to: {output_file}")
    
    def generate_html_report(self, results: Dict[str, Any], output_file: str):
        """Generate HTML report"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Deep Thinking Engine - Integration Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .test-result {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ccc; }}
        .success {{ border-left-color: #4CAF50; background-color: #f9fff9; }}
        .failure {{ border-left-color: #f44336; background-color: #fff9f9; }}
        .metrics {{ margin-top: 10px; font-size: 0.9em; color: #666; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Deep Thinking Engine - Integration Test Report</h1>
        <p>Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Test Type: {results.get('test_type', 'comprehensive')}</p>
    </div>
    
    <div class="summary">
        <h2>Summary</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Total Tests</td><td>{results.get('total_tests', 0)}</td></tr>
            <tr><td>Successful Tests</td><td>{results.get('successful_tests', 0)}</td></tr>
            <tr><td>Failed Tests</td><td>{results.get('failed_tests', 0)}</td></tr>
            <tr><td>Success Rate</td><td>{results.get('success_rate', 0):.1%}</td></tr>
        </table>
    </div>
"""
        
        # Add stability metrics if available
        if 'stability_metrics' in results:
            stability = results['stability_metrics']
            html_content += f"""
    <div class="summary">
        <h2>Stability Metrics</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Total Operations</td><td>{stability.get('total_operations', 0)}</td></tr>
            <tr><td>Success Rate</td><td>{stability.get('success_rate', 0):.1%}</td></tr>
            <tr><td>Average Response Time</td><td>{stability.get('average_response_time', 0):.3f}s</td></tr>
            <tr><td>Error Rate</td><td>{stability.get('error_rate', 0):.2%}</td></tr>
        </table>
    </div>
"""
        
        # Add test results
        html_content += """
    <div class="summary">
        <h2>Test Results</h2>
"""
        
        if 'results' in results:
            for result in results['results']:
                if hasattr(result, '__dict__'):
                    success = result.success
                    test_name = result.test_name
                    execution_time = result.execution_time
                    error_message = result.error_message
                else:
                    success = result.get('success', False)
                    test_name = result.get('test_name', 'Unknown')
                    execution_time = result.get('execution_time', 0)
                    error_message = result.get('error_message', '')
                
                status_class = 'success' if success else 'failure'
                status_text = '✅ PASS' if success else '❌ FAIL'
                
                html_content += f"""
        <div class="test-result {status_class}">
            <strong>{status_text} {test_name}</strong> ({execution_time:.3f}s)
"""
                
                if error_message:
                    html_content += f"""
            <div class="metrics">Error: {error_message}</div>
"""
                
                html_content += """
        </div>
"""
        
        html_content += """
    </div>
</body>
</html>
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"HTML report saved to: {output_file}")


def main():
    """Main entry point for the integration test runner"""
    parser = argparse.ArgumentParser(description='Deep Thinking Engine Integration Test Runner')
    
    parser.add_argument(
        '--mode', 
        choices=['quick', 'comprehensive', 'stress', 'regression'],
        default='comprehensive',
        help='Test execution mode'
    )
    
    parser.add_argument(
        '--output-format',
        choices=['text', 'json', 'html'],
        default='text',
        help='Output report format'
    )
    
    parser.add_argument(
        '--output-file',
        help='Output file path (optional)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )
    
    parser.add_argument(
        '--config-file',
        help='Configuration file path (optional)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = {'log_level': args.log_level}
    if args.config_file and Path(args.config_file).exists():
        import yaml
        with open(args.config_file, 'r') as f:
            config.update(yaml.safe_load(f))
    
    # Initialize runner
    runner = IntegrationTestRunner(config)
    
    try:
        # Run tests based on mode
        if args.mode == 'quick':
            results = runner.run_quick_test_suite()
        elif args.mode == 'comprehensive':
            results = runner.run_comprehensive_test_suite()
        elif args.mode == 'stress':
            results = runner.run_stress_test_suite()
        elif args.mode == 'regression':
            results = runner.run_regression_test_suite()
        else:
            raise ValueError(f"Unknown test mode: {args.mode}")
        
        # Generate output
        if args.output_format == 'json':
            output_file = args.output_file or f'integration_test_report_{args.mode}.json'
            runner.generate_json_report(results, output_file)
        elif args.output_format == 'html':
            output_file = args.output_file or f'integration_test_report_{args.mode}.html'
            runner.generate_html_report(results, output_file)
        else:
            # Text format - use existing framework functionality
            if args.mode == 'comprehensive':
                success = run_automated_integration_tests(args.output_file)
            else:
                # For other modes, print summary
                print(f"\n{'='*60}")
                print(f"INTEGRATION TEST RESULTS - {args.mode.upper()} MODE")
                print(f"{'='*60}")
                print(f"Total Tests: {results.get('total_tests', 0)}")
                print(f"Successful: {results.get('successful_tests', 0)}")
                print(f"Failed: {results.get('failed_tests', 0)}")
                print(f"Success Rate: {results.get('success_rate', 0):.1%}")
                
                if 'stability_metrics' in results:
                    stability = results['stability_metrics']
                    print(f"\nStability Metrics:")
                    print(f"  Operations: {stability.get('total_operations', 0)}")
                    print(f"  Success Rate: {stability.get('success_rate', 0):.1%}")
                    print(f"  Avg Response: {stability.get('average_response_time', 0):.3f}s")
                    print(f"  Error Rate: {stability.get('error_rate', 0):.2%}")
                
                success = results.get('failed_tests', 1) == 0
        
        # Exit with appropriate code
        if args.output_format in ['json', 'html']:
            success = results.get('failed_tests', 1) == 0
        
        if success:
            print(f"\n🎉 All {args.mode} integration tests passed!")
            sys.exit(0)
        else:
            print(f"\n⚠️  Some {args.mode} integration tests failed!")
            sys.exit(1)
            
    except Exception as e:
        runner.logger.error(f"Integration test execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()