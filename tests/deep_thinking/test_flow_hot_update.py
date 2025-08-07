"""
Tests for flow configuration hot update system
"""

import asyncio
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.mcps.deep_thinking.config.flow_hot_update import (
    ActiveSessionMigrator,
    FlowHotUpdateManager,
    FlowUpdateAnalyzer,
)
from src.mcps.deep_thinking.models.thinking_models import FlowStep, ThinkingFlow


class TestFlowUpdateAnalyzer(unittest.TestCase):
    """Test flow update analyzer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = FlowUpdateAnalyzer()
        
        # Create test flows
        self.old_flow = ThinkingFlow(
            name="test_flow",
            description="Original test flow",
            version="1.0",
            steps=[
                FlowStep(
                    step_id="step1",
                    name="Step 1",
                    agent_type="decomposer",
                    config={"max_questions": 3}
                ),
                FlowStep(
                    step_id="step2",
                    name="Step 2",
                    agent_type="critic",
                    config={"standards": "basic"}
                ),
            ]
        )
        
        self.new_flow_minor_change = ThinkingFlow(
            name="test_flow",
            description="Updated test flow",  # Changed description
            version="1.1",  # Changed version
            steps=[
                FlowStep(
                    step_id="step1",
                    name="Step 1",
                    agent_type="decomposer",
                    config={"max_questions": 3}
                ),
                FlowStep(
                    step_id="step2",
                    name="Step 2",
                    agent_type="critic",
                    config={"standards": "basic"}
                ),
            ]
        )
        
        self.new_flow_step_added = ThinkingFlow(
            name="test_flow",
            description="Original test flow",
            version="1.0",
            steps=[
                FlowStep(
                    step_id="step1",
                    name="Step 1",
                    agent_type="decomposer",
                    config={"max_questions": 3}
                ),
                FlowStep(
                    step_id="step2",
                    name="Step 2",
                    agent_type="critic",
                    config={"standards": "basic"}
                ),
                FlowStep(
                    step_id="step3",
                    name="Step 3",
                    agent_type="reflector",
                    config={"depth": "shallow"}
                ),
            ]
        )
        
        self.new_flow_step_removed = ThinkingFlow(
            name="test_flow",
            description="Original test flow",
            version="1.0",
            steps=[
                FlowStep(
                    step_id="step1",
                    name="Step 1",
                    agent_type="decomposer",
                    config={"max_questions": 3}
                ),
            ]
        )
        
        self.new_flow_breaking_change = ThinkingFlow(
            name="test_flow",
            description="Original test flow",
            version="1.0",
            steps=[
                FlowStep(
                    step_id="step1",
                    name="Step 1",
                    agent_type="evidence_seeker",  # Changed agent type
                    config={"max_questions": 3}
                ),
                FlowStep(
                    step_id="step2",
                    name="Step 2",
                    agent_type="critic",
                    config={"standards": "basic"}
                ),
            ]
        )
    
    def test_analyze_metadata_changes(self):
        """Test analysis of metadata changes"""
        analysis = self.analyzer.analyze_flow_changes(self.old_flow, self.new_flow_minor_change)
        
        self.assertEqual(analysis["flow_name"], "test_flow")
        self.assertEqual(analysis["impact_level"], "low")
        self.assertFalse(analysis["migration_required"])
        self.assertEqual(analysis["compatibility"], "full")
        
        # Check for description and version changes
        change_types = [change["type"] for change in analysis["changes"]]
        self.assertIn("flow_metadata_changed", change_types)
    
    def test_analyze_step_added(self):
        """Test analysis when step is added"""
        analysis = self.analyzer.analyze_flow_changes(self.old_flow, self.new_flow_step_added)
        
        self.assertEqual(analysis["impact_level"], "medium")
        self.assertFalse(analysis["migration_required"])  # Adding steps usually doesn't require migration
        self.assertEqual(analysis["compatibility"], "full")
        
        # Check for step added change
        added_changes = [
            change for change in analysis["changes"] 
            if change["type"] == "step_added"
        ]
        self.assertEqual(len(added_changes), 1)
        self.assertEqual(added_changes[0]["step_id"], "step3")
    
    def test_analyze_step_removed(self):
        """Test analysis when step is removed"""
        analysis = self.analyzer.analyze_flow_changes(self.old_flow, self.new_flow_step_removed)
        
        self.assertEqual(analysis["impact_level"], "high")
        self.assertTrue(analysis["migration_required"])
        self.assertEqual(analysis["compatibility"], "partial")
        
        # Check for step removed change
        removed_changes = [
            change for change in analysis["changes"] 
            if change["type"] == "step_removed"
        ]
        self.assertEqual(len(removed_changes), 1)
        self.assertEqual(removed_changes[0]["step_id"], "step2")
    
    def test_analyze_breaking_change(self):
        """Test analysis of breaking changes"""
        analysis = self.analyzer.analyze_flow_changes(self.old_flow, self.new_flow_breaking_change)
        
        self.assertEqual(analysis["impact_level"], "breaking")
        self.assertTrue(analysis["migration_required"])
        self.assertEqual(analysis["compatibility"], "incompatible")
        self.assertEqual(analysis["migration_strategy"], "restart_sessions")
        
        # Check for agent type change
        breaking_changes = [
            change for change in analysis["changes"] 
            if change.get("impact") == "breaking"
        ]
        self.assertGreater(len(breaking_changes), 0)
    
    def test_determine_migration_strategy(self):
        """Test migration strategy determination"""
        # Test hot update strategy
        minor_analysis = self.analyzer.analyze_flow_changes(self.old_flow, self.new_flow_minor_change)
        self.assertIsNone(minor_analysis["migration_strategy"])
        
        # Test graceful migration strategy
        step_removed_analysis = self.analyzer.analyze_flow_changes(self.old_flow, self.new_flow_step_removed)
        self.assertEqual(step_removed_analysis["migration_strategy"], "graceful_migration")
        
        # Test restart strategy
        breaking_analysis = self.analyzer.analyze_flow_changes(self.old_flow, self.new_flow_breaking_change)
        self.assertEqual(breaking_analysis["migration_strategy"], "restart_sessions")


class TestActiveSessionMigrator(unittest.TestCase):
    """Test active session migrator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_session_manager = MagicMock()
        self.migrator = ActiveSessionMigrator(self.mock_session_manager)
        
        # Create test flows
        self.old_flow = ThinkingFlow(
            name="test_flow",
            description="Original test flow",
            version="1.0",
            steps=[
                FlowStep(
                    step_id="step1",
                    name="Step 1",
                    agent_type="decomposer",
                    config={"max_questions": 3}
                ),
                FlowStep(
                    step_id="step2",
                    name="Step 2",
                    agent_type="critic",
                    config={"standards": "basic"}
                ),
            ]
        )
        
        self.new_flow = ThinkingFlow(
            name="test_flow",
            description="Updated test flow",
            version="1.1",
            steps=[
                FlowStep(
                    step_id="step1",
                    name="Step 1",
                    agent_type="decomposer",
                    config={"max_questions": 5}  # Changed config
                ),
                FlowStep(
                    step_id="step2",
                    name="Step 2",
                    agent_type="critic",
                    config={"standards": "basic"}
                ),
            ]
        )
        
        # Mock active sessions
        self.mock_sessions = [
            {
                "session_id": "session1",
                "flow_name": "test_flow",
                "topic": "Test topic 1",
                "user_id": "user1",
            },
            {
                "session_id": "session2",
                "flow_name": "test_flow",
                "topic": "Test topic 2",
                "user_id": "user2",
            },
        ]
    
    def test_get_active_sessions(self):
        """Test getting active sessions for a flow"""
        # Mock session manager response
        all_sessions = [
            {"session_id": "session1", "flow_name": "test_flow"},
            {"session_id": "session2", "flow_name": "other_flow"},
            {"session_id": "session3", "flow_name": "test_flow"},
        ]
        
        async def mock_get_active_sessions():
            return all_sessions
        
        self.mock_session_manager.get_active_sessions = mock_get_active_sessions
        
        # Test filtering
        async def run_test():
            sessions = await self.migrator._get_active_sessions("test_flow")
            self.assertEqual(len(sessions), 2)
            self.assertEqual(sessions[0]["session_id"], "session1")
            self.assertEqual(sessions[1]["session_id"], "session3")
        
        # Run async test
        asyncio.run(run_test())
    
    def test_hot_update_migration(self):
        """Test hot update migration strategy"""
        # Mock session manager methods
        async def mock_update_session_flow(session_id, flow):
            pass
        
        self.mock_session_manager.update_session_flow = mock_update_session_flow
        
        # Mock update session flow cache
        async def mock_update_cache(session_id, flow):
            pass
        
        self.migrator._update_session_flow_cache = mock_update_cache
        
        async def run_test():
            analysis = {"changes": [], "impact_level": "low"}
            
            results = await self.migrator._hot_update_migration(
                "test_flow", self.old_flow, self.new_flow, self.mock_sessions, analysis
            )
            
            self.assertEqual(results["strategy"], "hot_update")
            self.assertEqual(results["sessions_processed"], 2)
            self.assertEqual(results["successful_migrations"], 2)
            self.assertEqual(results["failed_migrations"], 0)
        
        asyncio.run(run_test())
    
    def test_restart_sessions(self):
        """Test restart sessions migration strategy"""
        # Mock session manager methods
        async def mock_get_session_state(session_id):
            return {
                "topic": f"Topic for {session_id}",
                "step_results": {"step1": "result1"},
            }
        
        async def mock_stop_session(session_id):
            pass
        
        async def mock_create_session(topic, flow_name, user_id):
            return f"new_{session_id}"
        
        self.mock_session_manager.get_session_state = mock_get_session_state
        self.mock_session_manager.stop_session = mock_stop_session
        self.mock_session_manager.create_session = mock_create_session
        
        # Mock restore session state
        async def mock_restore_state(new_session_id, session_state, new_flow):
            pass
        
        self.migrator._restore_session_state = mock_restore_state
        
        async def run_test():
            analysis = {"changes": [], "impact_level": "breaking"}
            
            results = await self.migrator._restart_sessions(
                "test_flow", self.old_flow, self.new_flow, self.mock_sessions, analysis
            )
            
            self.assertEqual(results["strategy"], "restart_sessions")
            self.assertEqual(results["sessions_processed"], 2)
            self.assertEqual(results["successful_migrations"], 2)
            self.assertEqual(results["failed_migrations"], 0)
        
        asyncio.run(run_test())


class TestFlowHotUpdateManager(unittest.TestCase):
    """Test flow hot update manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_flow_config_manager = MagicMock()
        self.mock_session_manager = MagicMock()
        
        self.manager = FlowHotUpdateManager(
            self.mock_flow_config_manager,
            self.mock_session_manager
        )
        
        # Create test flows
        self.test_flow = ThinkingFlow(
            name="test_flow",
            description="Test flow",
            version="1.0",
            steps=[
                FlowStep(
                    step_id="step1",
                    name="Step 1",
                    agent_type="decomposer",
                    config={"max_questions": 3}
                ),
            ]
        )
    
    def test_add_callbacks(self):
        """Test adding update and error callbacks"""
        update_callback = MagicMock()
        error_callback = MagicMock()
        
        self.manager.add_update_callback(update_callback)
        self.manager.add_error_callback(error_callback)
        
        self.assertIn(update_callback, self.manager.update_callbacks)
        self.assertIn(error_callback, self.manager.error_callbacks)
    
    def test_handle_new_flow(self):
        """Test handling new flow addition"""
        async def run_test():
            # Mock callback
            callback_called = False
            callback_data = None
            
            def mock_callback(update_info):
                nonlocal callback_called, callback_data
                callback_called = True
                callback_data = update_info
            
            self.manager.add_update_callback(mock_callback)
            
            # Handle new flow
            await self.manager._handle_new_flow("new_flow", self.test_flow)
            
            self.assertTrue(callback_called)
            self.assertEqual(callback_data["type"], "flow_added")
            self.assertEqual(callback_data["flow_name"], "new_flow")
        
        asyncio.run(run_test())
    
    def test_get_flow_update_status(self):
        """Test getting flow update status"""
        # Mock flow config manager
        self.mock_flow_config_manager.get_all_flows.return_value = {
            "flow1": self.test_flow,
            "flow2": self.test_flow,
        }
        
        # Mock session manager
        async def mock_get_active_sessions():
            return [
                {"session_id": "s1", "flow_name": "flow1"},
                {"session_id": "s2", "flow_name": "flow1"},
                {"session_id": "s3", "flow_name": "flow2"},
            ]
        
        self.mock_session_manager.get_active_sessions = mock_get_active_sessions
        
        async def run_test():
            status = await self.manager.get_flow_update_status()
            
            self.assertEqual(status["total_flows"], 2)
            self.assertEqual(status["active_sessions"], 3)
            self.assertEqual(status["sessions_by_flow"]["flow1"], 2)
            self.assertEqual(status["sessions_by_flow"]["flow2"], 1)
            self.assertTrue(status["hot_update_enabled"])
        
        asyncio.run(run_test())


def run_flow_hot_update_tests():
    """Run flow hot update tests"""
    print("Running flow hot update tests...")
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestFlowUpdateAnalyzer))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestActiveSessionMigrator))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestFlowHotUpdateManager))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    if result.wasSuccessful():
        print(f"\n✅ All {result.testsRun} tests passed!")
        return True
    else:
        print(f"\n❌ {len(result.failures)} failures, {len(result.errors)} errors")
        for failure in result.failures:
            print(f"FAILURE: {failure[0]}")
            print(failure[1])
        for error in result.errors:
            print(f"ERROR: {error[0]}")
            print(error[1])
        return False


if __name__ == "__main__":
    success = run_flow_hot_update_tests()
    exit(0 if success else 1)