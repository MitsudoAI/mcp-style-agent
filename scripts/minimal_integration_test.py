#!/usr/bin/env python3
"""
Minimal Integration Test

This script provides a minimal integration test that verifies the core
integration testing framework components work correctly without external dependencies.

Requirements: 集成测试，系统验证
"""

import json
import logging
import tempfile
import time
from pathlib import Path
import sys

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def test_core_imports():
    """Test that core modules can be imported"""
    print("🧪 Testing core module imports...")
    
    try:
        # Test database import
        from mcps.deep_thinking.data.database import ThinkingDatabase
        print("✅ Database module imports successfully")
        
        # Test template manager import
        from mcps.deep_thinking.templates.template_manager import TemplateManager
        print("✅ Template manager module imports successfully")
        
        # Test session manager import
        from mcps.deep_thinking.sessions.session_manager import SessionManager
        print("✅ Session manager module imports successfully")
        
        # Test MCP tools import
        from mcps.deep_thinking.tools.mcp_tools import MCPTools
        print("✅ MCP tools module imports successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Core module import failed: {e}")
        return False

def test_database_functionality():
    """Test basic database functionality"""
    print("\n🧪 Testing database functionality...")
    
    try:
        from mcps.deep_thinking.data.database import ThinkingDatabase
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = str(Path(temp_dir) / "test.db")
            
            # Initialize database
            database = ThinkingDatabase(db_path)
            print("✅ Database initializes successfully")
            
            # Test session creation
            session_id = "test_session_001"
            topic = "Test database topic"
            
            success = database.create_session(session_id, topic)
            if success:
                print("✅ Session creation works")
            else:
                print("❌ Session creation failed")
                return False
            
            # Test session retrieval
            session = database.get_session(session_id)
            if session and session['topic'] == topic:
                print("✅ Session retrieval works")
            else:
                print("❌ Session retrieval failed")
                return False
            
            # Test get all sessions
            all_sessions = database.get_all_sessions()
            if isinstance(all_sessions, list) and len(all_sessions) > 0:
                print("✅ Get all sessions works")
            else:
                print("❌ Get all sessions failed")
                return False
            
            # Cleanup
            database.shutdown()
            print("✅ Database cleanup successful")
            
        return True
        
    except Exception as e:
        print(f"❌ Database functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_template_manager_functionality():
    """Test basic template manager functionality"""
    print("\n🧪 Testing template manager functionality...")
    
    try:
        from mcps.deep_thinking.templates.template_manager import TemplateManager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            templates_dir = Path(temp_dir) / "templates"
            templates_dir.mkdir()
            
            # Create test template
            test_template_content = "Test template: {topic}"
            (templates_dir / "test_template.tmpl").write_text(test_template_content)
            
            # Initialize template manager
            template_manager = TemplateManager(str(templates_dir))
            print("✅ Template manager initializes successfully")
            
            # Test template retrieval
            template = template_manager.get_template("test_template", {"topic": "Integration test"})
            if template and "Integration test" in template:
                print("✅ Template retrieval and parameter substitution works")
            else:
                print("❌ Template retrieval failed")
                return False
            
            # Test missing template handling
            missing_template = template_manager.get_template("nonexistent_template", {})
            if missing_template is None:
                print("✅ Missing template handling works")
            else:
                print("❌ Missing template handling failed")
                return False
            
            # Cleanup
            template_manager.shutdown()
            print("✅ Template manager cleanup successful")
            
        return True
        
    except Exception as e:
        print(f"❌ Template manager functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_session_manager_functionality():
    """Test basic session manager functionality"""
    print("\n🧪 Testing session manager functionality...")
    
    try:
        from mcps.deep_thinking.data.database import ThinkingDatabase
        from mcps.deep_thinking.sessions.session_manager import SessionManager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = str(Path(temp_dir) / "test.db")
            
            # Initialize components
            database = ThinkingDatabase(db_path)
            session_manager = SessionManager(database)
            print("✅ Session manager initializes successfully")
            
            # Test session creation
            session_id = "session_manager_test_001"
            topic = "Session manager test topic"
            
            success = session_manager.create_session(session_id, topic)
            if success:
                print("✅ Session manager session creation works")
            else:
                print("❌ Session manager session creation failed")
                return False
            
            # Test session retrieval
            session = session_manager.get_session(session_id)
            if session and session['topic'] == topic:
                print("✅ Session manager session retrieval works")
            else:
                print("❌ Session manager session retrieval failed")
                return False
            
            # Cleanup
            database.shutdown()
            print("✅ Session manager cleanup successful")
            
        return True
        
    except Exception as e:
        print(f"❌ Session manager functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mcp_tools_functionality():
    """Test basic MCP tools functionality"""
    print("\n🧪 Testing MCP tools functionality...")
    
    try:
        from mcps.deep_thinking.data.database import ThinkingDatabase
        from mcps.deep_thinking.sessions.session_manager import SessionManager
        from mcps.deep_thinking.templates.template_manager import TemplateManager
        from mcps.deep_thinking.flows.flow_manager import FlowManager
        from mcps.deep_thinking.tools.mcp_tools import MCPTools
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup components
            db_path = str(Path(temp_dir) / "test.db")
            templates_dir = Path(temp_dir) / "templates"
            templates_dir.mkdir()
            
            # Create test template
            (templates_dir / "test_template.tmpl").write_text("Test template: {topic}")
            
            # Initialize components
            database = ThinkingDatabase(db_path)
            template_manager = TemplateManager(str(templates_dir))
            flow_manager = FlowManager(database)
            session_manager = SessionManager(database)
            
            mcp_tools = MCPTools(
                session_manager=session_manager,
                flow_manager=flow_manager,
                template_manager=template_manager,
                flow_executor=None  # Not needed for basic test
            )
            print("✅ MCP tools initialize successfully")
            
            # Test start_thinking
            topic = "MCP tools test topic"
            result = mcp_tools.start_thinking(topic)
            
            if isinstance(result, dict) and 'session_id' in result and 'prompt_template' in result:
                print("✅ MCP tools start_thinking works")
                session_id = result['session_id']
            else:
                print("❌ MCP tools start_thinking failed")
                return False
            
            # Test next_step
            next_result = mcp_tools.next_step(session_id, "Previous step result")
            if isinstance(next_result, dict) and 'step' in next_result:
                print("✅ MCP tools next_step works")
            else:
                print("❌ MCP tools next_step failed")
                return False
            
            # Cleanup
            database.shutdown()
            template_manager.shutdown()
            print("✅ MCP tools cleanup successful")
            
        return True
        
    except Exception as e:
        print(f"❌ MCP tools functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration_framework_structure():
    """Test that integration framework files exist and are structured correctly"""
    print("\n🧪 Testing integration framework structure...")
    
    try:
        # Check that integration test files exist
        integration_files = [
            "tests/deep_thinking/test_integration_framework.py",
            "tests/deep_thinking/test_system_reliability.py", 
            "tests/deep_thinking/test_integration_suite.py",
            "scripts/run_integration_tests.py"
        ]
        
        for file_path in integration_files:
            full_path = project_root / file_path
            if full_path.exists():
                print(f"✅ {file_path} exists")
            else:
                print(f"❌ {file_path} missing")
                return False
        
        # Check that files have reasonable content
        framework_file = project_root / "tests/deep_thinking/test_integration_framework.py"
        content = framework_file.read_text()
        
        required_classes = [
            "IntegrationTestFramework",
            "IntegrationTestResult", 
            "SystemStabilityMetrics"
        ]
        
        for class_name in required_classes:
            if class_name in content:
                print(f"✅ {class_name} class found in framework")
            else:
                print(f"❌ {class_name} class missing from framework")
                return False
        
        # Check for key methods
        required_methods = [
            "run_end_to_end_test",
            "run_multi_scenario_tests",
            "run_stability_test",
            "run_concurrent_access_test"
        ]
        
        for method_name in required_methods:
            if method_name in content:
                print(f"✅ {method_name} method found in framework")
            else:
                print(f"❌ {method_name} method missing from framework")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Integration framework structure test failed: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 80)
    print("MINIMAL INTEGRATION TEST")
    print("=" * 80)
    print("Testing core integration testing framework functionality...")
    
    tests = [
        ("Core Module Imports", test_core_imports),
        ("Database Functionality", test_database_functionality),
        ("Template Manager Functionality", test_template_manager_functionality),
        ("Session Manager Functionality", test_session_manager_functionality),
        ("MCP Tools Functionality", test_mcp_tools_functionality),
        ("Integration Framework Structure", test_integration_framework_structure)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print('='*60)
        
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
            failed += 1
    
    print(f"\n{'='*80}")
    print("MINIMAL INTEGRATION TEST SUMMARY")
    print('='*80)
    print(f"Tests Passed: {passed}")
    print(f"Tests Failed: {failed}")
    print(f"Total Tests: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All minimal integration tests PASSED!")
        print("✅ Core integration testing framework functionality is working!")
        print("\n📋 Integration Testing Framework Status:")
        print("  ✅ Core modules can be imported and initialized")
        print("  ✅ Database operations work correctly")
        print("  ✅ Template management works correctly")
        print("  ✅ Session management works correctly")
        print("  ✅ MCP tools work correctly")
        print("  ✅ Integration test framework files are properly structured")
        print("\n🚀 The integration testing framework is ready for use!")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        print("❌ Integration testing framework needs attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)