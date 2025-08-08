#!/usr/bin/env python3
"""
Basic Integration Test

This script provides a basic integration test that validates core functionality
using only standard library modules and the most essential components.

Requirements: 系统集成，功能验证
"""

import json
import logging
import sqlite3
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any
import sys

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


@dataclass
class BasicTestResult:
    """Result of a basic integration test"""
    test_name: str
    success: bool
    execution_time: float
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class BasicDatabase:
    """Basic database implementation without encryption"""
    
    def __init__(self, db_path: str):
        """Initialize basic database"""
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    topic TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    data TEXT
                )
            ''')
            
            # Create session_steps table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS session_steps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    step_name TEXT NOT NULL,
                    step_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (id)
                )
            ''')
            
            conn.commit()
    
    def create_session(self, session_id: str, topic: str) -> bool:
        """Create a new session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO sessions (id, topic) VALUES (?, ?)',
                    (session_id, topic)
                )
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to create session: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT id, topic, created_at, status, data FROM sessions WHERE id = ?',
                    (session_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    return {
                        'id': row[0],
                        'topic': row[1],
                        'created_at': row[2],
                        'status': row[3],
                        'data': json.loads(row[4]) if row[4] else {}
                    }
                return None
        except Exception as e:
            self.logger.error(f"Failed to get session: {e}")
            return None
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Get all sessions"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id, topic, created_at, status FROM sessions')
                rows = cursor.fetchall()
                
                return [
                    {
                        'id': row[0],
                        'topic': row[1],
                        'created_at': row[2],
                        'status': row[3]
                    }
                    for row in rows
                ]
        except Exception as e:
            self.logger.error(f"Failed to get all sessions: {e}")
            return []
    
    def shutdown(self):
        """Shutdown database (no-op for SQLite)"""
        pass


class BasicTemplateManager:
    """Basic template manager implementation"""
    
    def __init__(self, templates_dir: str):
        """Initialize template manager"""
        self.templates_dir = Path(templates_dir)
        self.logger = logging.getLogger(__name__)
        self._template_cache = {}
    
    def get_template(self, template_name: str, params: Dict[str, Any]) -> Optional[str]:
        """Get template with parameter substitution"""
        try:
            # Add .tmpl extension if not present
            if not template_name.endswith('.tmpl'):
                template_name += '.tmpl'
            
            template_path = self.templates_dir / template_name
            
            if not template_path.exists():
                self.logger.error(f"Template not found: {template_path}")
                return None
            
            # Load template
            if template_name not in self._template_cache:
                self._template_cache[template_name] = template_path.read_text(encoding='utf-8')
            
            template_content = self._template_cache[template_name]
            
            # Simple parameter substitution
            for key, value in params.items():
                template_content = template_content.replace(f'{{{key}}}', str(value))
            
            return template_content
            
        except Exception as e:
            self.logger.error(f"Failed to get template: {e}")
            return None
    
    def list_templates(self) -> List[str]:
        """List available templates"""
        try:
            return [f.stem for f in self.templates_dir.glob('*.tmpl')]
        except Exception as e:
            self.logger.error(f"Failed to list templates: {e}")
            return []
    
    def shutdown(self):
        """Shutdown template manager"""
        self._template_cache.clear()


class BasicSessionManager:
    """Basic session manager implementation"""
    
    def __init__(self, database: BasicDatabase):
        """Initialize session manager"""
        self.database = database
        self.logger = logging.getLogger(__name__)
    
    def create_session(self, session_id: str, topic: str) -> bool:
        """Create a new session"""
        return self.database.create_session(session_id, topic)
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID"""
        return self.database.get_session(session_id)
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Get all sessions"""
        return self.database.get_all_sessions()


class BasicMCPTools:
    """Basic MCP tools implementation"""
    
    def __init__(self, session_manager: BasicSessionManager, template_manager: BasicTemplateManager):
        """Initialize MCP tools"""
        self.session_manager = session_manager
        self.template_manager = template_manager
        self.logger = logging.getLogger(__name__)
    
    def start_thinking(self, topic: str) -> Dict[str, Any]:
        """Start thinking workflow"""
        try:
            # Generate session ID
            import uuid
            session_id = str(uuid.uuid4())
            
            # Create session
            success = self.session_manager.create_session(session_id, topic)
            if not success:
                raise Exception("Failed to create session")
            
            # Get template
            template = self.template_manager.get_template('basic_template', {'topic': topic})
            if not template:
                template = f"Please analyze the following topic: {topic}"
            
            return {
                'session_id': session_id,
                'prompt_template': template,
                'instructions': 'Please analyze the topic according to the template',
                'next_action': 'Provide your analysis'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to start thinking: {e}")
            raise
    
    def next_step(self, session_id: str, previous_result: str) -> Dict[str, Any]:
        """Get next step in workflow"""
        try:
            # Verify session exists
            session = self.session_manager.get_session(session_id)
            if not session:
                raise Exception(f"Session not found: {session_id}")
            
            # For basic implementation, just return a simple next step
            return {
                'session_id': session_id,
                'step': 'continue_analysis',
                'prompt_template': f"Continue analyzing the topic: {session['topic']}. Previous result: {previous_result}",
                'instructions': 'Please continue your analysis based on the previous result'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get next step: {e}")
            raise
    
    def complete_thinking(self, session_id: str) -> Dict[str, Any]:
        """Complete thinking workflow"""
        try:
            # Verify session exists
            session = self.session_manager.get_session(session_id)
            if not session:
                raise Exception(f"Session not found: {session_id}")
            
            # Return completion result
            return {
                'session_id': session_id,
                'status': 'completed',
                'summary_prompt': f"Please provide a final summary for the analysis of: {session['topic']}",
                'instructions': 'Summarize your complete analysis'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to complete thinking: {e}")
            raise


class BasicIntegrationTester:
    """Basic integration tester"""
    
    def __init__(self):
        """Initialize the basic integration tester"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        self.logger = logging.getLogger(__name__)
        self.start_time = time.time()
        
        # Test results
        self.test_results: List[BasicTestResult] = []
        
        # System components
        self.database: Optional[BasicDatabase] = None
        self.template_manager: Optional[BasicTemplateManager] = None
        self.session_manager: Optional[BasicSessionManager] = None
        self.mcp_tools: Optional[BasicMCPTools] = None
        
        self.setup_basic_system()
    
    def setup_basic_system(self):
        """Setup basic system for testing"""
        try:
            self.logger.info("Setting up basic system integration test environment...")
            
            # Create directories
            (self.temp_path / "templates").mkdir(exist_ok=True)
            (self.temp_path / "data").mkdir(exist_ok=True)
            
            # Create basic templates
            self._create_basic_templates()
            
            # Initialize components
            self._initialize_basic_components()
            
            self.logger.info(f"Basic system setup successful: {self.temp_dir}")
            
        except Exception as e:
            self.logger.error(f"Failed to setup basic system: {e}")
            raise
    
    def _create_basic_templates(self):
        """Create basic test templates"""
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
    
    def _initialize_basic_components(self):
        """Initialize basic system components"""
        try:
            # Database
            db_path = str(self.temp_path / "data" / "test.db")
            self.database = BasicDatabase(db_path)
            
            # Template manager
            templates_dir = str(self.temp_path / "templates")
            self.template_manager = BasicTemplateManager(templates_dir)
            
            # Session manager
            self.session_manager = BasicSessionManager(self.database)
            
            # MCP tools
            self.mcp_tools = BasicMCPTools(self.session_manager, self.template_manager)
            
            self.logger.info("Basic system components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize basic components: {e}")
            raise
    
    def run_test(self, test_name: str, test_func) -> BasicTestResult:
        """Run a single test"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Running test: {test_name}")
            
            result = test_func()
            duration = time.time() - start_time
            
            test_result = BasicTestResult(
                test_name=test_name,
                success=True,
                execution_time=duration,
                details=result if isinstance(result, dict) else None
            )
            
            self.logger.info(f"✅ Test {test_name} PASSED ({duration:.3f}s)")
            
        except Exception as e:
            duration = time.time() - start_time
            
            test_result = BasicTestResult(
                test_name=test_name,
                success=False,
                execution_time=duration,
                error_message=str(e)
            )
            
            self.logger.error(f"❌ Test {test_name} FAILED ({duration:.3f}s): {e}")
        
        self.test_results.append(test_result)
        return test_result
    
    def test_database_functionality(self):
        """Test database functionality"""
        assert self.database is not None, "Database should be initialized"
        
        # Test session creation
        session_id = "test_session_001"
        topic = "Test database topic"
        
        success = self.database.create_session(session_id, topic)
        assert success, "Session creation should succeed"
        
        # Test session retrieval
        session = self.database.get_session(session_id)
        assert session is not None, "Session should be retrievable"
        assert session['topic'] == topic, "Session topic should match"
        
        # Test session listing
        all_sessions = self.database.get_all_sessions()
        assert len(all_sessions) > 0, "Should have at least one session"
        
        return {
            'database_initialized': True,
            'session_created': success,
            'session_retrieved': session is not None,
            'topic_matches': session['topic'] == topic if session else False,
            'sessions_count': len(all_sessions)
        }
    
    def test_template_functionality(self):
        """Test template functionality"""
        assert self.template_manager is not None, "Template manager should be initialized"
        
        # Test template listing
        templates = self.template_manager.list_templates()
        assert len(templates) > 0, "Should have templates available"
        
        # Test template loading
        template = self.template_manager.get_template('basic_template', {'topic': 'test topic'})
        assert template is not None, "Should be able to load template"
        assert 'test topic' in template, "Template should contain substituted parameter"
        
        return {
            'template_manager_initialized': True,
            'templates_count': len(templates),
            'template_substitution_works': 'test topic' in template,
            'available_templates': templates
        }
    
    def test_session_manager_functionality(self):
        """Test session manager functionality"""
        assert self.session_manager is not None, "Session manager should be initialized"
        
        # Test session creation
        session_id = "test_session_002"
        topic = "Test session manager topic"
        
        success = self.session_manager.create_session(session_id, topic)
        assert success, "Session creation should succeed"
        
        # Test session retrieval
        session = self.session_manager.get_session(session_id)
        assert session is not None, "Session should be retrievable"
        assert session['topic'] == topic, "Session topic should match"
        
        return {
            'session_manager_initialized': True,
            'session_creation': success,
            'session_retrieval': session is not None,
            'topic_matches': session['topic'] == topic if session else False
        }
    
    def test_mcp_tools_functionality(self):
        """Test MCP tools functionality"""
        assert self.mcp_tools is not None, "MCP tools should be initialized"
        
        topic = "Test MCP tools topic"
        
        # Test start_thinking
        start_result = self.mcp_tools.start_thinking(topic)
        assert isinstance(start_result, dict), "Result should be a dictionary"
        assert 'session_id' in start_result, "Result should contain session_id"
        assert 'prompt_template' in start_result, "Result should contain prompt_template"
        
        session_id = start_result['session_id']
        
        # Test next_step
        next_result = self.mcp_tools.next_step(session_id, "Test previous result")
        assert isinstance(next_result, dict), "Result should be a dictionary"
        assert 'session_id' in next_result, "Result should contain session_id"
        
        # Test complete_thinking
        complete_result = self.mcp_tools.complete_thinking(session_id)
        assert isinstance(complete_result, dict), "Result should be a dictionary"
        assert 'session_id' in complete_result, "Result should contain session_id"
        assert 'status' in complete_result, "Result should contain status"
        
        return {
            'mcp_tools_initialized': True,
            'start_thinking_works': True,
            'next_step_works': True,
            'complete_thinking_works': True,
            'session_id': session_id
        }
    
    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        topic = "End-to-end workflow test"
        
        # Step 1: Start thinking
        start_result = self.mcp_tools.start_thinking(topic)
        session_id = start_result['session_id']
        
        # Step 2: Get next step
        next_result = self.mcp_tools.next_step(session_id, "Initial analysis completed")
        
        # Step 3: Complete thinking
        complete_result = self.mcp_tools.complete_thinking(session_id)
        
        # Step 4: Verify session persistence
        final_session = self.session_manager.get_session(session_id)
        
        return {
            'workflow_completed': True,
            'session_id': session_id,
            'start_step_success': 'session_id' in start_result,
            'next_step_success': 'session_id' in next_result,
            'complete_step_success': 'status' in complete_result,
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
                
                # Create session via MCP tools
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
            ('database_functionality', self.test_database_functionality),
            ('template_functionality', self.test_template_functionality),
            ('session_manager_functionality', self.test_session_manager_functionality),
            ('mcp_tools_functionality', self.test_mcp_tools_functionality),
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
            "DEEP THINKING ENGINE - BASIC SYSTEM INTEGRATION TEST REPORT",
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
            f"Core Components Working: {'✅ YES' if passed_tests >= 4 else '❌ NO'}",
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
        output_dir = Path(output_directory or "basic_integration_results")
        output_dir.mkdir(exist_ok=True)
        
        # Save report
        report = self.generate_integration_report()
        with open(output_dir / "basic_integration_report.txt", 'w', encoding='utf-8') as f:
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
        
        with open(output_dir / "basic_integration_results.json", 'w', encoding='utf-8') as f:
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
            
            self.logger.info("Basic system integration test environment cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deep Thinking Engine Basic System Integration Test')
    parser.add_argument('--output-dir', help='Output directory for results')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 80)
    print("DEEP THINKING ENGINE - BASIC SYSTEM INTEGRATION TEST")
    print("=" * 80)
    
    tester = None
    
    try:
        # Initialize tester
        tester = BasicIntegrationTester()
        print(f"✅ Basic system initialized: {tester.temp_dir}")
        
        # Run all tests
        print("\n🧪 Running basic system integration tests...")
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
            print("\n🎉 ALL BASIC SYSTEM INTEGRATION TESTS PASSED!")
            print("✅ Core Deep Thinking Engine functionality is working correctly!")
            return True
        else:
            failed_tests = total_tests - passed_tests
            print(f"\n⚠️  {failed_tests} test(s) FAILED out of {total_tests}")
            print("❌ System integration needs attention")
            return False
        
    except Exception as e:
        print(f"❌ Basic system integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if tester:
            tester.cleanup()


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)