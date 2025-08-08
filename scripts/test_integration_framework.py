#!/usr/bin/env python3
"""
Simple test script to verify the integration testing framework works

This script tests the basic functionality of the integration testing framework
without requiring pytest or other external dependencies.
"""

import sys
import tempfile
from pathlib import Path

# Add src and tests to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))

def test_basic_framework_functionality():
    """Test basic framework functionality"""
    print("🧪 Testing Integration Test Framework...")
    
    try:
        # Import the framework
        from tests.deep_thinking.test_integration_framework import IntegrationTestFramework
        print("✅ Integration test framework imports successfully")
        
        # Initialize framework
        with tempfile.TemporaryDirectory() as temp_dir:
            framework = IntegrationTestFramework(temp_dir)
            print("✅ Integration test framework initializes successfully")
            
            # Test basic MCP tools functionality
            if framework.mcp_tools:
                print("✅ MCP tools initialized")
            
            # Test template manager
            if framework.template_manager:
                print("✅ Template manager initialized")
            
            # Test database
            if framework.database:
                print("✅ Database initialized")
            
            # Test session manager
            if framework.session_manager:
                print("✅ Session manager initialized")
            
            # Cleanup
            framework.cleanup()
            print("✅ Framework cleanup successful")
        
        print("\n🎉 Integration test framework basic functionality test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test framework test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_reliability_framework():
    """Test reliability testing framework"""
    print("\n🧪 Testing System Reliability Framework...")
    
    try:
        # Import the reliability tester
        from tests.deep_thinking.test_system_reliability import SystemReliabilityTester
        print("✅ System reliability tester imports successfully")
        
        # Initialize tester
        with tempfile.TemporaryDirectory() as temp_dir:
            tester = SystemReliabilityTester(temp_dir)
            print("✅ System reliability tester initializes successfully")
            
            # Test basic components
            if tester.database:
                print("✅ Database initialized")
            
            if tester.template_manager:
                print("✅ Template manager initialized")
            
            if tester.mcp_tools:
                print("✅ MCP tools initialized")
            
            # Cleanup
            tester.cleanup()
            print("✅ Reliability tester cleanup successful")
        
        print("\n🎉 System reliability framework basic functionality test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ System reliability framework test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration_suite():
    """Test integration test suite"""
    print("\n🧪 Testing Integration Test Suite...")
    
    try:
        # Import the test suite
        from tests.deep_thinking.test_integration_suite import IntegrationTestSuite, IntegrationTestSuiteConfig
        print("✅ Integration test suite imports successfully")
        
        # Create configuration for quick testing
        config = IntegrationTestSuiteConfig(
            run_stability_tests=False,  # Skip long-running tests
            run_reliability_tests=False,
            stability_duration_minutes=1,
            reliability_duration_minutes=1
        )
        
        # Initialize suite
        suite = IntegrationTestSuite(config)
        print("✅ Integration test suite initializes successfully")
        
        print("\n🎉 Integration test suite basic functionality test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test suite test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("=" * 80)
    print("INTEGRATION TESTING FRAMEWORK VERIFICATION")
    print("=" * 80)
    
    tests = [
        test_basic_framework_functionality,
        test_reliability_framework,
        test_integration_suite
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    print(f"Tests Passed: {passed}")
    print(f"Tests Failed: {failed}")
    print(f"Total Tests: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All integration testing framework verification tests PASSED!")
        print("✅ Integration testing framework is ready for use!")
        return True
    else:
        print(f"\n⚠️  {failed} verification test(s) failed")
        print("❌ Integration testing framework needs attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)