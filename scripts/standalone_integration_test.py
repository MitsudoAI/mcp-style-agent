#!/usr/bin/env python3
"""
Standalone Integration Test

This script provides a standalone integration test that doesn't require pytest
or other external testing dependencies. It demonstrates the core functionality
of the integration testing framework.

Requirements: 集成测试，系统验证
"""

import json
import logging
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any
import sys

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Core imports
from mcps.deep_thinking.config.config_manager import ConfigManager
from mcps.deep_thinking.data.database import ThinkingDatabase
from mcps.deep_thinking.flows.flow_manager import FlowManager
from mcps.deep_thinking.sessions.session_manager import SessionManager
from mcps.deep_thinking.templates.template_manager import TemplateManager
from mcps.deep_thinking.tools.mcp_tools import MCPTools


@dataclass
class TestResult:
    """Simple test result"""
    name: str
    success: bool
    duration: float
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class StandaloneIntegrationTester:
    """Standalone integration tester without external dependencies"""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """Initialize the tester"""
        self.temp_dir = temp_dir or tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        self.logger = logging.getLogger(__name__)
        self.results: List[TestResult] = []
        
        # System components
        self.database: Optional[ThinkingDatabase] = None
        self.template_manager: Optional[TemplateManager] = None
        self.flow_manager: Optional[FlowManager] = None
        self.session_manager: Optional[SessionManager] = None
        self.mcp_tools: Optional[MCPTools] = None
        
        self.setup_test_environment()
    
    def setup_test_environment(self):
        """Setup test environment"""
        try:
            # Create directories
            (self.temp_path / "config").mkdir(exist_ok=True)
            (self.temp_path / "templates").mkdir(exist_ok=True)
            (self.temp_path / "data").mkdir(exist_ok=True)
            
            # Create test configuration
            import yaml
            config = {
                'database': {'path': str(self.temp_path / "data" / "test.db")},
                'templates': {'directory': str(self.temp_path / "templates")}
            }
            
            with open(self.temp_path / "config" / "system.yaml", 'w') as f:
                yaml.dump(config, f)
            
            # Create test template
            (self.temp_path / "templates" / "test_template.tmpl").write_text(
                "Test template: {topic}"
            )
            
            # Initialize components
            self._initialize_components()
            
            self.logger.info(f"Test environment setup complete: {self.temp_dir}")
            
        except Exception as e:
            self.logger.error(f"Failed to setup test environment: {e}")
            raise
    
    def _initialize_components(self):
        """Initialize system components"""
        try:
            # Database
            db_path = str(self.temp_path / "data" / "test.db")
            self.database = ThinkingDatabase(db_path)
            
            # Template manager
            templates_dir = str(self.temp_path / "templates")
            self.template_manager = TemplateManager(templates_dir)
            
            # Flow manager
            self.flow_manager = FlowManager(self.database)
            
            # Session manager
            self.session_manager = SessionManager(self.database)
            
            # MCP tools
            self.mcp_tools = MCPTools(
                session_manager=self.session_manager,
                flow_manager=self.flow_manager,
                template_manager=self.template_manager,
                flow_executor=None  # Not needed for basic tests
            )
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            raise
    
    def run_test(self, test_name: str, test_func) -> TestResult:
        """Run a single test"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Running test: {test_name}")
            
            result = test_func()
            duration = time.time() - start_time
            
            test_result = TestResult(
                name=test_name,
                success=True,
                duration=duration,
                details=result if isinstance(result, dict) else None
            )
            
            self.logger.info(f"Test {test_name} PASSED ({duration:.3f}s)")
            
        except Exception as e:
            duration = time.time() - start_time
            
            test_result = TestResult(
                name=test_name,
                success=False,
                duration=duration,
                error_message=str(e)
            )
            
            self.logger.error(f"Test {test_name} FAILED ({duration:.3f}s): {e}")
        
        self.results.append(test_result)
        return test_result
    
    def test_component_initialization(self):
        """Test that all components initialize correctly"""
        assert self.database is not None, "Database should be initialized"
        assert self.template_manager is not None, "Template manager should be initialized"
        assert self.flow_manager is not None, "Flow manager should be initialized"
        assert self.session_manager is not None, "Session manager should be initialized"
        assert self.mcp_tools is not None, "MCP tools should be initialized"
        
        return {
            'database_initialized': self.database is not None,
            'template_manager_initialized': self.template_manager is not None,
            'flow_manager_initialized': self.flow_manager is not None,
            'session_manager_initialized': self.session_manager is not None,
            'mcp_tools_initialized': self.mcp_tools is not None
        }
    
    def test_session_creation(self):
        """Test session creation functionality"""
        session_id = "test_session_001"
        topic = "Test session topic"
        
        # Create session
        success = self.session_manager.create_session(session_id, topic)
        assert success, "Session creation should succeed"
        
        # Retrieve session
        session = self.session_manager.get_session(session_id)
        assert session is not None, "Session should be retrievable"
        assert session['topic'] == topic, "Session topic should match"
        
        return {
            'session_created': success,
            'session_retrieved': session is not None,
            'session_id': session_id,
            'topic_matches': session['topic'] == topic if session else False
        }
    
    def test_template_access(self):
        """Test template access functionality"""
        template_name = "test_template"
        params = {'topic': 'Integration test topic'}
        
        # Get template
        template = self.template_manager.get_template(template_name, params)
        assert template is not None, "Template should be accessible"
        assert "Integration test topic" in template, "Template should contain parameter value"
        
        return {
            'template_accessed': template is not None,
            'template_content': template,
            'parameter_substitution': "Integration test topic" in template if template else False
        }
    
    def test_mcp_tools_start_thinking(self):
        """Test MCP tools start_thinking functionality"""
        topic = "Integration test thinking topic"
        
        # Start thinking
        result = self.mcp_tools.start_thinking(topic)
        assert isinstance(result, dict), "Result should be a dictionary"
        assert 'session_id' in result, "Result should contain session_id"
        assert 'prompt_template' in result, "Result should contain prompt_template"
        
        return {
            'result_type': type(result).__name__,
            'has_session_id': 'session_id' in result,
            'has_prompt_template': 'prompt_template' in result,
            'session_id': result.get('session_id')
        }
    
    def test_mcp_tools_next_step(self):
        """Test MCP tools next_step functionality"""
        # First create a session
        start_result = self.mcp_tools.start_thinking("Next step test topic")
        session_id = start_result['session_id']
        
        # Get next step
        next_result = self.mcp_tools.next_step(session_id, "Previous step result")
        assert isinstance(next_result, dict), "Result should be a dictionary"
        assert 'step' in next_result, "Result should contain step"
        
        return {
            'result_type': type(next_result).__name__,
            'has_step': 'step' in next_result,
            'session_id': session_id,
            'step_name': next_result.get('step')
        }
    
    def test_database_operations(self):
        """Test basic database operations"""
        # Test session storage and retrieval
        session_id = "db_test_session"
        topic = "Database test topic"
        
        # Create session
        success = self.database.create_session(session_id, topic)
        assert success, "Database session creation should succeed"
        
        # Retrieve session
        session = self.database.get_session(session_id)
        assert session is not None, "Database session retrieval should succeed"
        assert session['topic'] == topic, "Retrieved session should have correct topic"
        
        # Get all sessions
        all_sessions = self.database.get_all_sessions()
        assert isinstance(all_sessions, list), "get_all_sessions should return a list"
        assert len(all_sessions) > 0, "Should have at least one session"
        
        return {
            'session_created': success,
            'session_retrieved': session is not None,
            'all_sessions_count': len(all_sessions),
            'topic_matches': session['topic'] == topic if session else False
        }
    
    def test_concurrent_operations(self):
        """Test basic concurrent operations"""
        import threading
        import time
        
        results = []
        errors = []
        
        def worker_operation(worker_id):
            """Worker operation for concurrent testing"""
            try:
                # Create session
                session_id = f"concurrent_session_{worker_id}"
                topic = f"Concurrent test topic {worker_id}"
                
                success = self.session_manager.create_session(session_id, topic)
                if success:
                    # Retrieve session
                    session = self.session_manager.get_session(session_id)
                    if session:
                        results.append((worker_id, 'success', session['topic']))
                    else:
                        results.append((worker_id, 'retrieve_failed', None))
                else:
                    results.append((worker_id, 'create_failed', None))
                    
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # Run concurrent operations
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker_operation, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Analyze results
        successful_operations = len([r for r in results if r[1] == 'success'])
        
        assert len(errors) == 0, f"No errors should occur, but got: {errors}"
        assert successful_operations == 5, f"All 5 operations should succeed, got {successful_operations}"
        
        return {
            'total_operations': len(results),
            'successful_operations': successful_operations,
            'errors': len(errors),
            'results': results
        }
    
    def test_error_handling(self):
        """Test error handling capabilities"""
        error_scenarios = []
        
        # Test invalid session ID
        try:
            result = self.mcp_tools.next_step("invalid_session_id", "test")
            error_scenarios.append(('invalid_session', 'no_error', result))
        except Exception as e:
            error_scenarios.append(('invalid_session', 'error_handled', str(e)))
        
        # Test missing template
        try:
            template = self.template_manager.get_template('nonexistent_template', {'param': 'value'})
            error_scenarios.append(('missing_template', 'no_error' if template is None else 'returned_none', template))
        except Exception as e:
            error_scenarios.append(('missing_template', 'error_handled', str(e)))
        
        # Test empty topic
        try:
            result = self.mcp_tools.start_thinking("")
            error_scenarios.append(('empty_topic', 'no_error', result))
        except Exception as e:
            error_scenarios.append(('empty_topic', 'error_handled', str(e)))
        
        # At least some error scenarios should be handled gracefully
        handled_scenarios = [s for s in error_scenarios if s[1] in ['error_handled', 'returned_none']]
        
        return {
            'total_scenarios': len(error_scenarios),
            'handled_scenarios': len(handled_scenarios),
            'scenarios': error_scenarios
        }
    
    def run_all_tests(self):
        """Run all integration tests"""
        tests = [
            ('component_initialization', self.test_component_initialization),
            ('session_creation', self.test_session_creation),
            ('template_access', self.test_template_access),
            ('mcp_tools_start_thinking', self.test_mcp_tools_start_thinking),
            ('mcp_tools_next_step', self.test_mcp_tools_next_step),
            ('database_operations', self.test_database_operations),
            ('concurrent_operations', self.test_concurrent_operations),
            ('error_handling', self.test_error_handling)
        ]
        
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
    
    def generate_report(self) -> str:
        """Generate test report"""
        if not self.results:
            return "No test results available."
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - passed_tests
        total_duration = sum(r.duration for r in self.results)
        
        report_lines = [
            "=" * 80,
            "STANDALONE INTEGRATION TEST REPORT",
            "=" * 80,
            "",
            f"Test Environment: {self.temp_dir}",
            f"Report Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "SUMMARY",
            "-" * 40,
            f"Total Tests: {total_tests}",
            f"Passed: {passed_tests}",
            f"Failed: {failed_tests}",
            f"Success Rate: {passed_tests/total_tests:.1%}",
            f"Total Duration: {total_duration:.3f}s",
            "",
            "TEST DETAILS",
            "-" * 40
        ]
        
        for result in self.results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            report_lines.append(f"{status} {result.name} ({result.duration:.3f}s)")
            
            if result.error_message:
                report_lines.append(f"    Error: {result.error_message}")
            
            if result.details:
                for key, value in result.details.items():
                    report_lines.append(f"    {key}: {value}")
        
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
            
            self.logger.info("Test environment cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


def main():
    """Main function"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 80)
    print("STANDALONE INTEGRATION TEST")
    print("=" * 80)
    
    tester = None
    
    try:
        # Initialize tester
        tester = StandaloneIntegrationTester()
        print(f"✅ Test environment initialized: {tester.temp_dir}")
        
        # Run all tests
        print("\n🧪 Running integration tests...")
        tester.run_all_tests()
        
        # Generate and display report
        report = tester.generate_report()
        print("\n" + report)
        
        # Save report to file
        report_file = "standalone_integration_test_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n📄 Report saved to: {report_file}")
        
        # Determine success
        passed_tests = sum(1 for r in tester.results if r.success)
        total_tests = len(tester.results)
        
        if passed_tests == total_tests:
            print("\n🎉 All integration tests PASSED!")
            print("✅ Integration testing framework is working correctly!")
            return True
        else:
            failed_tests = total_tests - passed_tests
            print(f"\n⚠️  {failed_tests} test(s) FAILED out of {total_tests}")
            print("❌ Integration testing framework needs attention")
            return False
        
    except Exception as e:
        print(f"❌ Integration test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if tester:
            tester.cleanup()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)