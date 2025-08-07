"""
Simplified tests for flow configuration hot update system
"""

import sys
import unittest
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Create mock models to avoid import issues
class MockFlowStep:
    def __init__(self, step_id, name, agent_type, config=None):
        self.step_id = step_id
        self.name = name
        self.agent_type = agent_type
        self.config = config or {}
        self.conditions = None
        self.depends_on = None

class MockThinkingFlow:
    def __init__(self, name, description, version, steps):
        self.name = name
        self.description = description
        self.version = version
        self.steps = steps
        self.estimated_duration = None
    
    def model_dump(self):
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "steps": [
                {
                    "step_id": step.step_id,
                    "name": step.name,
                    "agent_type": step.agent_type,
                    "config": step.config,
                }
                for step in self.steps
            ]
        }

# Import the analyzer class directly
from src.mcps.deep_thinking.config.flow_hot_update import FlowUpdateAnalyzer


class TestFlowUpdateAnalyzer(unittest.TestCase):
    """Test flow update analyzer with mock objects"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = FlowUpdateAnalyzer()
        
        # Create test flows using mock objects
        self.old_flow = MockThinkingFlow(
            name="test_flow",
            description="Original test flow",
            version="1.0",
            steps=[
                MockFlowStep(
                    step_id="step1",
                    name="Step 1",
                    agent_type="decomposer",
                    config={"max_questions": 3}
                ),
                MockFlowStep(
                    step_id="step2",
                    name="Step 2",
                    agent_type="critic",
                    config={"standards": "basic"}
                ),
            ]
        )
        
        self.new_flow_minor_change = MockThinkingFlow(
            name="test_flow",
            description="Updated test flow",  # Changed description
            version="1.1",  # Changed version
            steps=[
                MockFlowStep(
                    step_id="step1",
                    name="Step 1",
                    agent_type="decomposer",
                    config={"max_questions": 3}
                ),
                MockFlowStep(
                    step_id="step2",
                    name="Step 2",
                    agent_type="critic",
                    config={"standards": "basic"}
                ),
            ]
        )
        
        self.new_flow_step_added = MockThinkingFlow(
            name="test_flow",
            description="Original test flow",
            version="1.0",
            steps=[
                MockFlowStep(
                    step_id="step1",
                    name="Step 1",
                    agent_type="decomposer",
                    config={"max_questions": 3}
                ),
                MockFlowStep(
                    step_id="step2",
                    name="Step 2",
                    agent_type="critic",
                    config={"standards": "basic"}
                ),
                MockFlowStep(
                    step_id="step3",
                    name="Step 3",
                    agent_type="reflector",
                    config={"depth": "shallow"}
                ),
            ]
        )
        
        self.new_flow_step_removed = MockThinkingFlow(
            name="test_flow",
            description="Original test flow",
            version="1.0",
            steps=[
                MockFlowStep(
                    step_id="step1",
                    name="Step 1",
                    agent_type="decomposer",
                    config={"max_questions": 3}
                ),
            ]
        )
        
        self.new_flow_breaking_change = MockThinkingFlow(
            name="test_flow",
            description="Original test flow",
            version="1.0",
            steps=[
                MockFlowStep(
                    step_id="step1",
                    name="Step 1",
                    agent_type="evidence_seeker",  # Changed agent type
                    config={"max_questions": 3}
                ),
                MockFlowStep(
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
        # Test no migration needed
        minor_analysis = self.analyzer.analyze_flow_changes(self.old_flow, self.new_flow_minor_change)
        self.assertIsNone(minor_analysis["migration_strategy"])
        
        # Test graceful migration strategy
        step_removed_analysis = self.analyzer.analyze_flow_changes(self.old_flow, self.new_flow_step_removed)
        self.assertEqual(step_removed_analysis["migration_strategy"], "graceful_migration")
        
        # Test restart strategy
        breaking_analysis = self.analyzer.analyze_flow_changes(self.old_flow, self.new_flow_breaking_change)
        self.assertEqual(breaking_analysis["migration_strategy"], "restart_sessions")
    
    def test_analyze_step_config_changes(self):
        """Test analysis of step configuration changes"""
        # Create flow with modified step config
        new_flow_config_change = MockThinkingFlow(
            name="test_flow",
            description="Original test flow",
            version="1.0",
            steps=[
                MockFlowStep(
                    step_id="step1",
                    name="Step 1",
                    agent_type="decomposer",
                    config={"max_questions": 5}  # Changed from 3 to 5
                ),
                MockFlowStep(
                    step_id="step2",
                    name="Step 2",
                    agent_type="critic",
                    config={"standards": "basic"}
                ),
            ]
        )
        
        analysis = self.analyzer.analyze_flow_changes(self.old_flow, new_flow_config_change)
        
        self.assertEqual(analysis["impact_level"], "medium")
        self.assertFalse(analysis["migration_required"])
        self.assertEqual(analysis["compatibility"], "full")
        
        # Check for config change
        config_changes = [
            change for change in analysis["changes"] 
            if change["type"] == "step_modified" and change["field"] == "config"
        ]
        self.assertEqual(len(config_changes), 1)
        self.assertEqual(config_changes[0]["step_id"], "step1")
    
    def test_impact_level_determination(self):
        """Test impact level determination logic"""
        # Test with no changes
        no_changes = []
        impact = self.analyzer._determine_impact_level(no_changes)
        self.assertEqual(impact, "none")
        
        # Test with low impact changes
        low_changes = [{"impact": "low"}]
        impact = self.analyzer._determine_impact_level(low_changes)
        self.assertEqual(impact, "low")
        
        # Test with mixed impact changes
        mixed_changes = [{"impact": "low"}, {"impact": "medium"}, {"impact": "low"}]
        impact = self.analyzer._determine_impact_level(mixed_changes)
        self.assertEqual(impact, "medium")
        
        # Test with breaking changes
        breaking_changes = [{"impact": "low"}, {"impact": "breaking"}]
        impact = self.analyzer._determine_impact_level(breaking_changes)
        self.assertEqual(impact, "breaking")
    
    def test_compatibility_assessment(self):
        """Test compatibility assessment logic"""
        # Test full compatibility
        low_changes = [{"impact": "low"}]
        compatibility = self.analyzer._assess_compatibility(low_changes)
        self.assertEqual(compatibility, "full")
        
        # Test partial compatibility
        high_changes = [{"impact": "high"}]
        compatibility = self.analyzer._assess_compatibility(high_changes)
        self.assertEqual(compatibility, "partial")
        
        # Test incompatibility
        breaking_changes = [{"impact": "breaking"}]
        compatibility = self.analyzer._assess_compatibility(breaking_changes)
        self.assertEqual(compatibility, "incompatible")


def run_simple_flow_hot_update_tests():
    """Run simplified flow hot update tests"""
    print("Running simplified flow hot update tests...")
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestFlowUpdateAnalyzer))
    
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
    success = run_simple_flow_hot_update_tests()
    exit(0 if success else 1)