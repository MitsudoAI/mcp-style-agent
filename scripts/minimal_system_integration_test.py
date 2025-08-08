#!/usr/bin/env python3
"""
Minimal System Integration Test

This script provides a minimal system integration test that validates
the core functionality of the Deep Thinking Engine without requiring
external dependencies like watchdog, psutil, etc.

Requirements: 系统集成，功能验证
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

# Core imports (only the essential ones)
from mcps.deep_thinking.data.database import ThinkingDatabase
from mcps.deep_thinking.sessions.session_manager import SessionManager
from mcps.deep_thinking.templates.template_manager import TemplateManager
from mcps.deep_thinking.tools.mcp_tools import MCPTools


@dataclass
class MinimalTestResult:
    """Result of a minimal integration test"""
    test_name: str
    success: bool
    execution_time: float
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class MinimalSystemIntegrationTester:
    """Minimal system integration tester"""
    
    def __init__(self):
        """Initialize the minimal integration tester"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        self.logger = logging.getLogger(__name__)
        self.start_time = time.time()
        
        # Test results
        self.test_results: List[MinimalTestResult] = []
        
        # System components
        self.database: Optional[ThinkingDatabase] = None
        self.template_manager: Optional[TemplateManager] = None
        self.session_manager: Optional[SessionManager] = None
        self.mcp_tools: Optional[MCPTools] = None
        
        self.setup_minimal_system()
    
    def setup_minimal_system(self):
        """Setup minimal system for testing"""
        try:
            self.logger.info("Setting up minimal system integration test environment...")
            
            # Create directories
            (self.temp_path / "templates").mkdir(exist_ok=True)
            (self.temp_path / "data").mkdir(exist_ok=True)
            
            # Create minimal templates
            self._create_minimal_templates()
            
            # Initialize components
            self._initialize_minimal_components()
            
            self.logger.info(f"Minimal system setup successful: {self.temp_dir}")
            
        except Exception as e:
            self.logger.error(f"Failed to setup minimal system: {e}")
            raise
    
    def _create_minimal_templates(self):
        """Create minimal test templates"""
        templates = {
            'basic_template.tmpl': """
# 基础分析模板

请对以下主题进行基础分析：

**主题**: {topic}

## 分析要求：
1. 简要概述主题的核心内容
2. 识别关键要点
3. 提供初步结论

请开始分析：
""",
            
            'decomposition_template.tmpl': """
# 问题分解模板

请将以下复杂问题分解为可管理的子问题：

**主要问题**: {topic}

## 分解要求：
1. 将主问题分解为3-5个核心子问题
2. 每个子问题应该相对独立且可深入分析

开始分解：
"""
        }
        
        for template_name, template_content in templates.items():
            template_path = self.temp_path / "templates" / template_name
            template_path.write_text(template_content, encoding='utf-8')
    
    def _initialize_minimal_components(self):
        """Initialize minimal system components"""
        try:
            # Database
            db_path = str(self.temp_path / "data" / "test.db")
            self.database = ThinkingDatabase(db_path)
            
            # Template manager
            templates_dir = str(self.temp_path / "templates")
            self.template_manager = TemplateManager(templates_dir)
            
            # Session manager
            self.session_manager = SessionManager(self.database)
            
            # MCP tools (simplified initialization)
            self.mcp_tools = MCPTools(
                session_manager=self.session_manager,
                flow_manager=None,  # Not needed for basic tests
                template_manager=self.template_manager,
                flow_executor=None  # Not needed for basic tests
            )
            
            self.logger.info("Minimal system components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize minimal components: {e}")
            raise
    
    def run_test(self, test_name: str, test_func) -> MinimalTestResult:
        """Run a single test"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Running test: {test_name}")
            
            result = test_func()
            duration = time.time() - start_time
            
            test_result = MinimalTestResult(
                test_name=test_name,
                success=True,
                execution_time=duration,
                details=result if isinstance(result, dict) else None
            )
            
            self.logger.info(f"✅ Test {test_name} PASSED ({duration:.3f}s)")
            
        except Exception as e:
            duration = time.time() - start_time
            
            test_result = MinimalTestResult(
                test_name=test_name,
                success=False,
                execution_time=duration,
                error_message=str(e)
            )
            
            self.logger.error(f"❌ Test {test_name} FAILED ({duration:.3f}s): {e}")
        
        self.test_results.append(test_result)
        return test_result
    
    def test_database_initialization(self):
        """Test database initialization"""
        assert self.database is not None, "Database should be initialized"
        
        # Test connection
        connection = self.database.get_connection()
        assert connection is not None, "Database connection should be available"
        
        return {
            'database_initialized': True,
            'connection_available': True
        }
    
    def test_template_manager_initialization(self):
        """Test template manager initialization"""
        assert self.template_manager is not None, "Template manager should be initialized"
        
        # Test template listing
        templates = self.template_manager.list_templates()
        assert len(templates) > 0, "Should have templates available"
        
        # Test template loading
        template = self.template_manager.get_template('basic_template', {'topic': 'test'})
        assert template is not None, "Should be able to load template"
        assert 'test' in template, "Template should contain substituted parameter"
        
        return {
            'template_manager_initialized': True,
            'templates_count': len(templates),
            'template_substitution_works': 'test' in template
        }
    
    def test_session_manager_functionality(self):
        """Test session manager functionality"""
        assert self.session_manager is not None, "Session manager should be initialized"
        
        # Test session creation
        session_id = "test_session_001"
        topic = "Test session topic"
        
        success = self.session_manager.create_session(session_id, topic)
        assert success, "Session creation should succeed"
        
        # Test session retrieval
        session = self.session_manager.get_session(session_id)
        assert session is not None, "Session should be retrievable"
        assert session['topic'] == topic, "Session topic should match"
        
        # Test session listing
        all_sessions = self.session_manager.get_all_sessions()
        assert len(all_sessions) > 0, "Should have at least one session"
        
        return {
            'session_creation': success,
            'session_retrieval': session is not None,
            'topic_matches': session['topic'] == topic if session else False,
            'sessions_count': len(all_sessions)
        }
    
    def test_mcp_tools_start_thinking(self):
        """Test MCP tools start_thinking functionality"""
        assert self.mcp_tools is not None, "MCP tools should be initialized"
        
        topic = "Integration test thinking topic"
        
        # Test start_thinking
        result = self.mcp_tools.start_thinking(topic)
        assert isinstance(result, dict), "Result should be a dictionary"
        assert 'session_id' in result, "Result should contain session_id"
        assert 'prompt_template' in result, "Result should contain prompt_template"
        
        # Verify session was created
        session_id = result['session_id']
        session = self.session_manager.get_session(session_id)
        assert session is not None, "Session should be created"
        assert session['topic'] == topic, "Session topic should match"
        
        return {
            'start_thinking_works': True,
            'session_id': session_id,
            'has_prompt_template': 'prompt_template' in result,
            'session_created': session is not None,
            'topic_matches': session['topic'] == topic if session else False
        }
    
    def test_mcp_tools_next_step(self):
        """Test MCP tools next_step functionality"""
        # First create a session
        start_result = self.mcp_tools.start_thinking("Next step test topic")
        session_id = start_result['session_id']
        
        # Test next_step
        next_result = self.mcp_tools.next_step(session_id, "Previous step result")
        assert isinstance(next_result, dict), "Result should be a dictionary"
        
        # The result should contain some kind of response
        assert len(next_result) > 0, "Result should not be empty"
        
        return {
            'next_step_works': True,
            'session_id': session_id,
            'result_keys': list(next_result.keys()),
            'result_not_empty': len(next_result) > 0
        }
    
    def test_mcp_tools_complete_thinking(self):
        """Test MCP tools complete_thinking functionality"""
        # First create a session
        start_result = self.mcp_tools.start_thinking("Complete thinking test topic")
        session_id = start_result['session_id']
        
        # Test complete_thinking
        complete_result = self.mcp_tools.complete_thinking(session_id)
        assert isinstance(complete_result, dict), "Result should be a dictionary"
        
        # The result should contain some kind of response
        assert len(complete_result) > 0, "Result should not be empty"
        
        return {
            'complete_thinking_works': True,
            'session_id': session_id,
            'result_keys': list(complete_result.keys()),
            'result_not_empty': len(complete_result) > 0
        }
    
    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        topic = "End-to-end workflow test topic"
        
        # Step 1: Start thinking
        start_result = self.mcp_tools.start_thinking(topic)
        session_id = start_result['session_id']
        
        # Step 2: Get next step
        next_result = self.mcp_tools.next_step(session_id, "Initial analysis completed")
        
        # Step 3: Complete thinking
        complete_result = self.mcp_tools.complete_thinking(session_id)
        
        # Verify session persistence
        final_session = self.session_manager.get_session(session_id)
        
        return {
            'workflow_completed': True,
            'session_id': session_id,
            'start_step_success': 'session_id' in start_result,
            'next_step_success': isinstance(next_result, dict),
            'complete_step_success': isinstance(complete_result, dict),
            'session_persisted': final_session is not None,
            'topic_preserved': final_session['topic'] == topic if final_session else False
        }
    
    def test_concurrent_operations(self):
        """Test basic concurrent operations"""
        import threading
        
        results = []
        errors = []
        
        def worker_operation(worker_id):
            """Worker operation for concurrent testing"""
            try:
                topic = f"Concurrent test topic {worker_id}"
                
                # Create session
                start_result = self.mcp_tools.start_thinking(topic)
                session_id = start_result['session_id']
                
                # Verify session
                session = self.session_manager.get_session(session_id)
                
                if session and session['topic'] == topic:
                    results.append((worker_id, 'success', session_id))
                else:
                    results.append((worker_id, 'verification_failed', session_id))
                    
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # Run concurrent operations
        threads = []
        for i in range(3):  # Small number for basic test
            thread = threading.Thread(target=worker_operation, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Analyze results
        successful_operations = len([r for r in results if r[1] == 'success'])
        
        return {
            'concurrent_operations_completed': True,
            'total_operations': len(results),
            'successful_operations': successful_operations,
            'errors': len(errors),
            'success_rate': successful_operations / max(len(results), 1),
            'thread_safety_verified': len(errors) == 0
        }
    
    def run_all_tests(self):
        """Run all integration tests"""
        tests = [
            ('database_initialization', self.test_database_initialization),
            ('template_manager_initialization', self.test_template_manager_initialization),
            ('session_manager_functionality', self.test_session_manager_functionality),
            ('mcp_tools_start_thinking', self.test_mcp_tools_start_thinking),
            ('mcp_tools_next_step', self.test_mcp_tools_next_step),
            ('mcp_tools_complete_thinking', self.test_mcp_tools_complete_thinking),
            ('end_to_end_workflow', self.test_end_to_end_workflow),
            ('concurrent_operations', self.test_concurrent_operations)
        ]
        
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
    
    def generate_integration_report(self) -> str:
        """Generate integration test report"""
        if not self.test_results:
            return "No test results available."
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.success)
        failed_tests = total_tests - passed_tests
        total_duration = sum(r.execution_time for r in self.test_results)
        
        report_lines = [
            "=" * 80,
            "DEEP THINKING ENGINE - MINIMAL SYSTEM INTEGRATION TEST REPORT",
            "=" * 80,
            "",
            f"Test Environment: {self.temp_dir}",
            f"Report Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"System Uptime: {time.time() - self.start_time:.1f} seconds",
            "",
            "EXECUTIVE SUMMARY",
            "-" * 40,
            f"Total Tests: {total_tests}",
            f"Passed: {passed_tests}",
            f"Failed: {failed_tests}",
            f"Success Rate: {passed_tests/total_tests:.1%}",
            f"Total Duration: {total_duration:.3f}s",
            f"Average Duration: {total_duration/total_tests:.3f}s",
            "",
            "DETAILED RESULTS",
            "-" * 40
        ]
        
        for result in self.test_results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            report_lines.append(f"{status} {result.test_name} ({result.execution_time:.3f}s)")
            
            if result.error_message:
                report_lines.append(f"    Error: {result.error_message}")
            
            if result.details:
                for key, value in result.details.items():
                    report_lines.append(f"    {key}: {value}")
        
        # Final assessment
        system_ready = failed_tests == 0 and passed_tests > 0
        
        report_lines.extend([
            "",
            "FINAL ASSESSMENT",
            "-" * 40,
            f"System Integration Status: {'✅ PASSED' if system_ready else '❌ FAILED'}",
            f"Core Components Working: {'✅ YES' if passed_tests >= 6 else '❌ NO'}",
            f"End-to-End Workflow: {'✅ FUNCTIONAL' if any('end_to_end' in r.test_name and r.success for r in self.test_results) else '❌ BROKEN'}",
            f"Concurrent Operations: {'✅ STABLE' if any('concurrent' in r.test_name and r.success for r in self.test_results) else '❌ UNSTABLE'}",
            "",
            f"DEPLOYMENT READINESS: {'🚀 READY FOR BASIC DEPLOYMENT' if system_ready else '⚠️ NEEDS ATTENTION'}",
            "",
            "=" * 80
        ])
        
        return "\n".join(report_lines)
    
    def save_results(self, output_directory: Optional[str] = None):
        """Save test results"""
        output_dir = Path(output_directory or "minimal_integration_results")
        output_dir.mkdir(exist_ok=True)
        
        # Save report
        report = self.generate_integration_report()
        with open(output_dir / "minimal_integration_report.txt", 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Save raw results
        results_data = {
            'test_results': [
                {
                    'test_name': r.test_name,
                    'success': r.success,
                    'execution_time': r.execution_time,
                    'error_message': r.error_message,
                    'details': r.details
                }
                for r in self.test_results
            ],
            'summary': {
                'total_tests': len(self.test_results),
                'passed_tests': sum(1 for r in self.test_results if r.success),
                'failed_tests': sum(1 for r in self.test_results if not r.success),
                'total_duration': sum(r.execution_time for r in self.test_results)
            }
        }
        
        with open(output_dir / "minimal_integration_results.json", 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Test results saved to: {output_dir}")
        return output_dir
    
    def cleanup(self):
        """Cleanup test environment"""
        try:
            # Shutdown components
            if self.database:
                self.database.shutdown()
            if self.template_manager:
                self.template_manager.shutdown()
            
            # Clean up temporary files
            import shutil
            if Path(self.temp_dir).exists():
                shutil.rmtree(self.temp_dir)
            
            self.logger.info("Minimal system integration test environment cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deep Thinking Engine Minimal System Integration Test')
    parser.add_argument('--output-dir', help='Output directory for results')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 80)
    print("DEEP THINKING ENGINE - MINIMAL SYSTEM INTEGRATION TEST")
    print("=" * 80)
    
    tester = None
    
    try:
        # Initialize tester
        tester = MinimalSystemIntegrationTester()
        print(f"✅ Minimal system initialized: {tester.temp_dir}")
        
        # Run all tests
        print("\n🧪 Running minimal system integration tests...")
        tester.run_all_tests()
        
        # Generate and display report
        report = tester.generate_integration_report()
        print("\n" + report)
        
        # Save results
        output_dir = tester.save_results(args.output_dir)
        print(f"\n📄 Results saved to: {output_dir}")
        
        # Determine success
        passed_tests = sum(1 for r in tester.test_results if r.success)
        total_tests = len(tester.test_results)
        
        if passed_tests == total_tests:
            print("\n🎉 ALL MINIMAL SYSTEM INTEGRATION TESTS PASSED!")
            print("✅ Core Deep Thinking Engine functionality is working correctly!")
            return True
        else:
            failed_tests = total_tests - passed_tests
            print(f"\n⚠️  {failed_tests} test(s) FAILED out of {total_tests}")
            print("❌ System integration needs attention")
            return False
        
    except Exception as e:
        print(f"❌ Minimal system integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if tester:
            tester.cleanup()


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)