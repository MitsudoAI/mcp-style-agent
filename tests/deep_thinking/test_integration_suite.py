"""
Comprehensive Integration Test Suite

This module orchestrates all integration tests and provides a unified interface
for running the complete integration test suite with various configurations.

Requirements: 集成测试，系统验证
"""

import json
import logging
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import pytest

from test_integration_framework import (
    IntegrationTestFramework,
    IntegrationTestResult,
    SystemStabilityMetrics,
)
from test_system_reliability import SystemReliabilityTester, ReliabilityTestMetrics


@dataclass
class IntegrationTestSuiteConfig:
    """Configuration for the integration test suite"""

    # Test selection
    run_end_to_end_tests: bool = True
    run_multi_scenario_tests: bool = True
    run_concurrent_tests: bool = True
    run_stability_tests: bool = True
    run_reliability_tests: bool = True
    run_edge_case_tests: bool = True

    # Test parameters
    stability_duration_minutes: int = 5
    stability_operations_per_minute: int = 30
    concurrent_threads: int = 10
    concurrent_operations_per_thread: int = 20
    reliability_duration_minutes: int = 3

    # Output configuration
    generate_detailed_report: bool = True
    save_raw_results: bool = True
    output_directory: Optional[str] = None

    # Quality gates
    minimum_success_rate: float = 0.9
    maximum_average_response_time: float = 2.0
    maximum_memory_usage_mb: float = 200
    maximum_resource_leaks: int = 1


@dataclass
class IntegrationTestSuiteResults:
    """Results from the complete integration test suite"""

    config: IntegrationTestSuiteConfig
    start_time: float
    end_time: float
    total_duration: float

    # Test results
    end_to_end_results: List[IntegrationTestResult]
    concurrent_test_result: Optional[IntegrationTestResult]
    stability_metrics: Optional[SystemStabilityMetrics]
    reliability_metrics: List[ReliabilityTestMetrics]

    # Summary statistics
    total_tests: int
    successful_tests: int
    failed_tests: int
    overall_success_rate: float

    # Quality gate results
    quality_gates_passed: int
    quality_gates_total: int
    quality_gates_details: Dict[str, bool]

    # Recommendations
    recommendations: List[str]


class IntegrationTestSuite:
    """Comprehensive integration test suite orchestrator"""

    def __init__(self, config: Optional[IntegrationTestSuiteConfig] = None):
        """Initialize the test suite"""
        self.config = config or IntegrationTestSuiteConfig()
        self.logger = logging.getLogger(__name__)

        # Initialize test frameworks
        self.integration_framework: Optional[IntegrationTestFramework] = None
        self.reliability_tester: Optional[SystemReliabilityTester] = None

        # Results storage
        self.results: Optional[IntegrationTestSuiteResults] = None

    def run_complete_test_suite(self) -> IntegrationTestSuiteResults:
        """Run the complete integration test suite"""
        self.logger.info("Starting comprehensive integration test suite")
        start_time = time.time()

        try:
            # Initialize test frameworks
            self._initialize_test_frameworks()

            # Initialize results structure
            end_to_end_results = []
            concurrent_test_result = None
            stability_metrics = None
            reliability_metrics = []

            # Run end-to-end tests
            if self.config.run_end_to_end_tests:
                self.logger.info("Running end-to-end tests...")
                end_to_end_results = self._run_end_to_end_tests()

            # Run multi-scenario tests
            if self.config.run_multi_scenario_tests:
                self.logger.info("Running multi-scenario tests...")
                scenario_results = self._run_multi_scenario_tests()
                end_to_end_results.extend(scenario_results)

            # Run concurrent tests
            if self.config.run_concurrent_tests:
                self.logger.info("Running concurrent tests...")
                concurrent_test_result = self._run_concurrent_tests()

            # Run stability tests
            if self.config.run_stability_tests:
                self.logger.info("Running stability tests...")
                stability_metrics = self._run_stability_tests()

            # Run reliability tests
            if self.config.run_reliability_tests:
                self.logger.info("Running reliability tests...")
                reliability_metrics = self._run_reliability_tests()

            # Run edge case tests
            if self.config.run_edge_case_tests:
                self.logger.info("Running edge case tests...")
                edge_case_metrics = self._run_edge_case_tests()
                reliability_metrics.extend(edge_case_metrics)

            # Calculate summary statistics
            total_tests, successful_tests, failed_tests = self._calculate_summary_stats(
                end_to_end_results, concurrent_test_result, reliability_metrics
            )

            overall_success_rate = successful_tests / max(total_tests, 1)

            # Evaluate quality gates
            quality_gates_passed, quality_gates_total, quality_gates_details = (
                self._evaluate_quality_gates(
                    end_to_end_results,
                    concurrent_test_result,
                    stability_metrics,
                    reliability_metrics,
                )
            )

            # Generate recommendations
            recommendations = self._generate_recommendations(
                end_to_end_results,
                concurrent_test_result,
                stability_metrics,
                reliability_metrics,
            )

            # Create results object
            end_time = time.time()
            self.results = IntegrationTestSuiteResults(
                config=self.config,
                start_time=start_time,
                end_time=end_time,
                total_duration=end_time - start_time,
                end_to_end_results=end_to_end_results,
                concurrent_test_result=concurrent_test_result,
                stability_metrics=stability_metrics,
                reliability_metrics=reliability_metrics,
                total_tests=total_tests,
                successful_tests=successful_tests,
                failed_tests=failed_tests,
                overall_success_rate=overall_success_rate,
                quality_gates_passed=quality_gates_passed,
                quality_gates_total=quality_gates_total,
                quality_gates_details=quality_gates_details,
                recommendations=recommendations,
            )

            self.logger.info(
                f"Integration test suite completed: {successful_tests}/{total_tests} tests passed"
            )

            return self.results

        except Exception as e:
            self.logger.error(f"Integration test suite failed: {e}")
            raise

        finally:
            self._cleanup_test_frameworks()

    def _initialize_test_frameworks(self):
        """Initialize test frameworks"""
        self.integration_framework = IntegrationTestFramework()
        self.reliability_tester = SystemReliabilityTester()

    def _cleanup_test_frameworks(self):
        """Cleanup test frameworks"""
        if self.integration_framework:
            self.integration_framework.cleanup()
        if self.reliability_tester:
            self.reliability_tester.cleanup()

    def _run_end_to_end_tests(self) -> List[IntegrationTestResult]:
        """Run basic end-to-end tests"""
        basic_scenarios = [
            {
                "name": "basic_comprehensive_test",
                "topic": "如何提高工作效率？",
                "flow_type": "test_comprehensive",
                "expected_steps": 3,
            },
            {
                "name": "basic_simple_test",
                "topic": "什么是机器学习？",
                "flow_type": "test_simple",
                "expected_steps": 1,
            },
        ]

        results = []
        for scenario in basic_scenarios:
            result = self.integration_framework.run_end_to_end_test(
                scenario["name"], scenario
            )
            results.append(result)

        return results

    def _run_multi_scenario_tests(self) -> List[IntegrationTestResult]:
        """Run multi-scenario tests"""
        return self.integration_framework.run_multi_scenario_tests()

    def _run_concurrent_tests(self) -> IntegrationTestResult:
        """Run concurrent access tests"""
        return self.integration_framework.run_concurrent_access_test(
            num_threads=self.config.concurrent_threads,
            operations_per_thread=self.config.concurrent_operations_per_thread,
        )

    def _run_stability_tests(self) -> SystemStabilityMetrics:
        """Run system stability tests"""
        return self.integration_framework.run_stability_test(
            duration_seconds=self.config.stability_duration_minutes * 60,
            operations_per_second=self.config.stability_operations_per_minute // 60,
        )

    def _run_reliability_tests(self) -> List[ReliabilityTestMetrics]:
        """Run reliability tests"""
        results = []

        # Long-term stability test (shorter for integration testing)
        stability_metrics = self.reliability_tester.test_long_term_stability(
            duration_minutes=self.config.reliability_duration_minutes,
            operations_per_minute=30,
        )
        results.append(stability_metrics)

        # Resource leak detection
        leak_metrics = self.reliability_tester.test_resource_leak_detection()
        results.append(leak_metrics)

        # Concurrent stress test
        stress_metrics = self.reliability_tester.test_concurrent_stress(
            num_threads=5, operations_per_thread=20
        )
        results.append(stress_metrics)

        return results

    def _run_edge_case_tests(self) -> List[ReliabilityTestMetrics]:
        """Run edge case tests"""
        edge_case_metrics = self.reliability_tester.test_edge_case_handling()
        return [edge_case_metrics]

    def _calculate_summary_stats(
        self,
        end_to_end_results: List[IntegrationTestResult],
        concurrent_result: Optional[IntegrationTestResult],
        reliability_metrics: List[ReliabilityTestMetrics],
    ) -> tuple:
        """Calculate summary statistics"""
        total_tests = 0
        successful_tests = 0
        failed_tests = 0

        # Count end-to-end tests
        for result in end_to_end_results:
            total_tests += 1
            if result.success:
                successful_tests += 1
            else:
                failed_tests += 1

        # Count concurrent test
        if concurrent_result:
            total_tests += 1
            if concurrent_result.success:
                successful_tests += 1
            else:
                failed_tests += 1

        # Count reliability tests (simplified - consider them successful if they completed)
        for metrics in reliability_metrics:
            total_tests += 1
            # Consider successful if success rate > 80%
            success_rate = metrics.successful_operations / max(
                metrics.total_operations, 1
            )
            if success_rate > 0.8:
                successful_tests += 1
            else:
                failed_tests += 1

        return total_tests, successful_tests, failed_tests

    def _evaluate_quality_gates(
        self,
        end_to_end_results: List[IntegrationTestResult],
        concurrent_result: Optional[IntegrationTestResult],
        stability_metrics: Optional[SystemStabilityMetrics],
        reliability_metrics: List[ReliabilityTestMetrics],
    ) -> tuple:
        """Evaluate quality gates"""
        gates_details = {}

        # Gate 1: Overall success rate
        total_tests, successful_tests, _ = self._calculate_summary_stats(
            end_to_end_results, concurrent_result, reliability_metrics
        )
        overall_success_rate = successful_tests / max(total_tests, 1)
        gates_details["success_rate"] = (
            overall_success_rate >= self.config.minimum_success_rate
        )

        # Gate 2: Average response time
        response_times = []
        for result in end_to_end_results:
            response_times.append(result.execution_time)
        if concurrent_result:
            response_times.append(concurrent_result.execution_time)

        avg_response_time = (
            sum(response_times) / len(response_times) if response_times else 0
        )
        gates_details["response_time"] = (
            avg_response_time <= self.config.maximum_average_response_time
        )

        # Gate 3: Memory usage
        max_memory_usage = 0
        if stability_metrics:
            max_memory_usage = max(max_memory_usage, stability_metrics.memory_usage_mb)
        for metrics in reliability_metrics:
            max_memory_usage = max(max_memory_usage, metrics.memory_usage_mb)

        gates_details["memory_usage"] = (
            max_memory_usage <= self.config.maximum_memory_usage_mb
        )

        # Gate 4: Resource leaks
        total_resource_leaks = 0
        for metrics in reliability_metrics:
            total_resource_leaks += metrics.resource_leaks_detected

        gates_details["resource_leaks"] = (
            total_resource_leaks <= self.config.maximum_resource_leaks
        )

        # Gate 5: Stability (if stability tests were run)
        if stability_metrics:
            stability_success_rate = stability_metrics.successful_operations / max(
                stability_metrics.total_operations, 1
            )
            gates_details["stability"] = stability_success_rate >= 0.95
        else:
            gates_details["stability"] = True  # Pass if not tested

        gates_passed = sum(1 for passed in gates_details.values() if passed)
        gates_total = len(gates_details)

        return gates_passed, gates_total, gates_details

    def _generate_recommendations(
        self,
        end_to_end_results: List[IntegrationTestResult],
        concurrent_result: Optional[IntegrationTestResult],
        stability_metrics: Optional[SystemStabilityMetrics],
        reliability_metrics: List[ReliabilityTestMetrics],
    ) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        # Analyze end-to-end test failures
        failed_e2e_tests = [r for r in end_to_end_results if not r.success]
        if failed_e2e_tests:
            recommendations.append(
                f"{len(failed_e2e_tests)} end-to-end test(s) failed - investigate core functionality issues"
            )

        # Analyze concurrent test results
        if concurrent_result and not concurrent_result.success:
            recommendations.append(
                "Concurrent access test failed - review thread safety and resource contention"
            )

        # Analyze stability metrics
        if stability_metrics:
            if stability_metrics.error_rate > 0.05:
                recommendations.append(
                    f"High error rate in stability test ({stability_metrics.error_rate:.2%}) - improve error handling"
                )

            if stability_metrics.average_response_time > 1.0:
                recommendations.append(
                    f"Slow response times in stability test ({stability_metrics.average_response_time:.3f}s) - optimize performance"
                )

        # Analyze reliability metrics
        for metrics in reliability_metrics:
            success_rate = metrics.successful_operations / max(
                metrics.total_operations, 1
            )
            if success_rate < 0.9:
                recommendations.append(
                    f"Low success rate in {metrics.test_name} ({success_rate:.2%}) - investigate reliability issues"
                )

            if metrics.resource_leaks_detected > 0:
                recommendations.append(
                    f"Resource leaks detected in {metrics.test_name} - review resource management"
                )

            if metrics.recovery_attempts > 0:
                recovery_rate = (
                    metrics.successful_recoveries / metrics.recovery_attempts
                )
                if recovery_rate < 0.8:
                    recommendations.append(
                        f"Poor error recovery in {metrics.test_name} ({recovery_rate:.2%}) - improve error handling"
                    )

        # Quality gate recommendations
        if self.results:
            failed_gates = [
                gate
                for gate, passed in self.results.quality_gates_details.items()
                if not passed
            ]
            if failed_gates:
                recommendations.append(
                    f"Quality gates failed: {', '.join(failed_gates)} - address these issues before release"
                )

        if not recommendations:
            recommendations.append(
                "All integration tests passed successfully - system is ready for deployment"
            )

        return recommendations

    def generate_comprehensive_report(self) -> str:
        """Generate comprehensive test report"""
        if not self.results:
            return "No test results available. Run tests first."

        report_lines = [
            "=" * 100,
            "DEEP THINKING ENGINE - COMPREHENSIVE INTEGRATION TEST REPORT",
            "=" * 100,
            "",
            f"Test Suite Configuration:",
            f"  End-to-End Tests: {'✓' if self.config.run_end_to_end_tests else '✗'}",
            f"  Multi-Scenario Tests: {'✓' if self.config.run_multi_scenario_tests else '✗'}",
            f"  Concurrent Tests: {'✓' if self.config.run_concurrent_tests else '✗'}",
            f"  Stability Tests: {'✓' if self.config.run_stability_tests else '✗'}",
            f"  Reliability Tests: {'✓' if self.config.run_reliability_tests else '✗'}",
            f"  Edge Case Tests: {'✓' if self.config.run_edge_case_tests else '✗'}",
            "",
            f"Execution Summary:",
            f"  Start Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.results.start_time))}",
            f"  End Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.results.end_time))}",
            f"  Total Duration: {self.results.total_duration:.1f} seconds",
            "",
            "OVERALL RESULTS",
            "-" * 50,
            f"Total Tests: {self.results.total_tests}",
            f"Successful Tests: {self.results.successful_tests}",
            f"Failed Tests: {self.results.failed_tests}",
            f"Overall Success Rate: {self.results.overall_success_rate:.2%}",
            "",
            "QUALITY GATES",
            "-" * 50,
            f"Gates Passed: {self.results.quality_gates_passed}/{self.results.quality_gates_total}",
            "",
        ]

        # Quality gate details
        for gate_name, passed in self.results.quality_gates_details.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            report_lines.append(f"  {status} {gate_name.replace('_', ' ').title()}")

        report_lines.append("")

        # End-to-end test results
        if self.results.end_to_end_results:
            report_lines.extend(["END-TO-END TEST RESULTS", "-" * 50])

            for result in self.results.end_to_end_results:
                status = "✅ PASS" if result.success else "❌ FAIL"
                report_lines.append(
                    f"{status} {result.test_name} ({result.execution_time:.3f}s)"
                )

                if result.error_message:
                    report_lines.append(f"    Error: {result.error_message}")

            report_lines.append("")

        # Concurrent test results
        if self.results.concurrent_test_result:
            report_lines.extend(["CONCURRENT ACCESS TEST", "-" * 50])

            result = self.results.concurrent_test_result
            status = "✅ PASS" if result.success else "❌ FAIL"
            report_lines.append(
                f"{status} {result.test_name} ({result.execution_time:.3f}s)"
            )

            if result.metrics:
                for key, value in result.metrics.items():
                    if isinstance(value, (int, float)):
                        report_lines.append(f"    {key}: {value}")

            if result.error_message:
                report_lines.append(f"    Error: {result.error_message}")

            report_lines.append("")

        # Stability test results
        if self.results.stability_metrics:
            metrics = self.results.stability_metrics
            report_lines.extend(
                [
                    "STABILITY TEST RESULTS",
                    "-" * 50,
                    f"Total Operations: {metrics.total_operations}",
                    f"Successful Operations: {metrics.successful_operations}",
                    f"Failed Operations: {metrics.failed_operations}",
                    f"Success Rate: {metrics.successful_operations/max(metrics.total_operations,1):.2%}",
                    f"Average Response Time: {metrics.average_response_time:.3f}s",
                    f"Max Response Time: {metrics.max_response_time:.3f}s",
                    f"Error Rate: {metrics.error_rate:.2%}",
                    f"Memory Usage: {metrics.memory_usage_mb:.1f}MB",
                    f"Uptime: {metrics.uptime_seconds:.1f}s",
                    "",
                ]
            )

        # Reliability test results
        if self.results.reliability_metrics:
            report_lines.extend(["RELIABILITY TEST RESULTS", "-" * 50])

            for metrics in self.results.reliability_metrics:
                success_rate = metrics.successful_operations / max(
                    metrics.total_operations, 1
                )
                report_lines.extend(
                    [
                        f"Test: {metrics.test_name}",
                        f"  Duration: {metrics.duration_seconds:.1f}s",
                        f"  Operations: {metrics.successful_operations}/{metrics.total_operations} ({success_rate:.2%})",
                        f"  Avg Response Time: {metrics.average_response_time:.3f}s",
                        f"  Memory Usage: {metrics.memory_usage_mb:.1f}MB",
                        f"  Resource Leaks: {metrics.resource_leaks_detected}",
                        "",
                    ]
                )

        # Recommendations
        if self.results.recommendations:
            report_lines.extend(["RECOMMENDATIONS", "-" * 50])
            for i, rec in enumerate(self.results.recommendations, 1):
                report_lines.append(f"{i}. {rec}")
            report_lines.append("")

        # Final assessment
        overall_status = "✅ PASSED" if self.results.failed_tests == 0 else "❌ FAILED"
        quality_gate_status = (
            "✅ PASSED"
            if self.results.quality_gates_passed == self.results.quality_gates_total
            else "❌ FAILED"
        )

        report_lines.extend(
            [
                "FINAL ASSESSMENT",
                "-" * 50,
                f"Overall Test Status: {overall_status}",
                f"Quality Gate Status: {quality_gate_status}",
                f"System Readiness: {'✅ READY FOR DEPLOYMENT' if overall_status == '✅ PASSED' and quality_gate_status == '✅ PASSED' else '❌ NEEDS ATTENTION'}",
                "",
                "=" * 100,
            ]
        )

        return "\n".join(report_lines)

    def save_results(self, output_directory: Optional[str] = None):
        """Save test results to files"""
        if not self.results:
            raise ValueError("No test results to save. Run tests first.")

        output_dir = Path(
            output_directory
            or self.config.output_directory
            or "integration_test_results"
        )
        output_dir.mkdir(exist_ok=True)

        # Save comprehensive report
        report = self.generate_comprehensive_report()
        with open(output_dir / "comprehensive_report.txt", "w", encoding="utf-8") as f:
            f.write(report)

        # Save raw results as JSON
        if self.config.save_raw_results:
            # Convert results to serializable format
            results_dict = asdict(self.results)

            # Handle non-serializable objects
            def convert_for_json(obj):
                if hasattr(obj, "__dict__"):
                    return obj.__dict__
                return str(obj)

            with open(output_dir / "raw_results.json", "w", encoding="utf-8") as f:
                json.dump(
                    results_dict,
                    f,
                    indent=2,
                    default=convert_for_json,
                    ensure_ascii=False,
                )

        self.logger.info(f"Test results saved to: {output_dir}")

        return output_dir


# Pytest integration


class TestIntegrationSuite:
    """Pytest test class for the integration suite"""

    @pytest.fixture
    def test_suite(self):
        """Create test suite fixture"""
        config = IntegrationTestSuiteConfig(
            stability_duration_minutes=1,  # Shorter for testing
            reliability_duration_minutes=1,
            concurrent_threads=3,
            concurrent_operations_per_thread=10,
        )
        suite = IntegrationTestSuite(config)
        yield suite

    def test_quick_integration_suite(self, test_suite):
        """Run a quick version of the integration suite"""
        # Configure for quick testing
        test_suite.config.run_stability_tests = False  # Skip long-running tests
        test_suite.config.run_reliability_tests = False

        results = test_suite.run_complete_test_suite()

        # Basic assertions
        assert results.total_tests > 0
        assert results.overall_success_rate >= 0.8  # 80% success rate
        assert (
            results.quality_gates_passed >= results.quality_gates_total * 0.8
        )  # 80% of quality gates

    def test_comprehensive_integration_suite(self, test_suite):
        """Run the comprehensive integration suite (longer test)"""
        results = test_suite.run_complete_test_suite()

        # Comprehensive assertions
        assert results.total_tests >= 5  # Should have multiple test types
        assert results.overall_success_rate >= 0.9  # 90% success rate
        assert (
            results.quality_gates_passed == results.quality_gates_total
        )  # All quality gates should pass
        assert len(results.recommendations) > 0  # Should have recommendations


# Command-line interface


def main():
    """Main entry point for running the integration test suite"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Deep Thinking Engine Integration Test Suite"
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick test suite (skip long-running tests)",
    )
    parser.add_argument("--output-dir", help="Output directory for results")
    parser.add_argument("--config-file", help="Configuration file (JSON)")

    args = parser.parse_args()

    # Load configuration
    config = IntegrationTestSuiteConfig()

    if args.config_file and Path(args.config_file).exists():
        with open(args.config_file, "r") as f:
            config_data = json.load(f)
            for key, value in config_data.items():
                if hasattr(config, key):
                    setattr(config, key, value)

    if args.quick:
        config.stability_duration_minutes = 1
        config.reliability_duration_minutes = 1
        config.concurrent_threads = 3
        config.concurrent_operations_per_thread = 10

    if args.output_dir:
        config.output_directory = args.output_dir

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run test suite
    suite = IntegrationTestSuite(config)

    try:
        results = suite.run_complete_test_suite()

        # Print summary
        print(f"\n{'='*60}")
        print("INTEGRATION TEST SUITE SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {results.total_tests}")
        print(f"Successful: {results.successful_tests}")
        print(f"Failed: {results.failed_tests}")
        print(f"Success Rate: {results.overall_success_rate:.2%}")
        print(
            f"Quality Gates: {results.quality_gates_passed}/{results.quality_gates_total}"
        )
        print(f"Duration: {results.total_duration:.1f}s")

        # Save results
        output_dir = suite.save_results()
        print(f"\nDetailed results saved to: {output_dir}")

        # Exit with appropriate code
        if (
            results.failed_tests == 0
            and results.quality_gates_passed == results.quality_gates_total
        ):
            print("\n🎉 All integration tests passed! System is ready for deployment.")
            exit(0)
        else:
            print(
                f"\n⚠️  Integration tests completed with issues. Check the detailed report."
            )
            exit(1)

    except Exception as e:
        print(f"❌ Integration test suite failed: {e}")
        import traceback

        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
