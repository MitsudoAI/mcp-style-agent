"""
Standalone tests for flow update analyzer
"""

import sys
import unittest
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class MockFlowStep:
    """Mock flow step for testing"""

    def __init__(self, step_id, name, agent_type, config=None):
        self.step_id = step_id
        self.name = name
        self.agent_type = agent_type
        self.config = config or {}
        self.conditions = None
        self.depends_on = None


class MockThinkingFlow:
    """Mock thinking flow for testing"""

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
            ],
        }


class FlowUpdateAnalyzer:
    """
    Standalone version of FlowUpdateAnalyzer for testing
    """

    def __init__(self):
        self.change_types = {
            "STEP_ADDED": "step_added",
            "STEP_REMOVED": "step_removed",
            "STEP_MODIFIED": "step_modified",
            "STEP_REORDERED": "step_reordered",
            "FLOW_METADATA_CHANGED": "flow_metadata_changed",
            "BREAKING_CHANGE": "breaking_change",
            "COMPATIBLE_CHANGE": "compatible_change",
        }

    def analyze_flow_changes(self, old_flow, new_flow):
        """Analyze changes between old and new flow configurations"""
        analysis = {
            "flow_name": new_flow.name,
            "changes": [],
            "impact_level": "none",
            "migration_required": False,
            "affected_steps": [],
            "compatibility": "full",
            "migration_strategy": None,
        }

        # Analyze metadata changes
        metadata_changes = self._analyze_metadata_changes(old_flow, new_flow)
        analysis["changes"].extend(metadata_changes)

        # Analyze step changes
        step_changes = self._analyze_step_changes(old_flow, new_flow)
        analysis["changes"].extend(step_changes)

        # Determine overall impact
        analysis["impact_level"] = self._determine_impact_level(analysis["changes"])
        analysis["migration_required"] = self._requires_migration(analysis["changes"])
        analysis["compatibility"] = self._assess_compatibility(analysis["changes"])
        analysis["migration_strategy"] = self._determine_migration_strategy(analysis)

        return analysis

    def _analyze_metadata_changes(self, old_flow, new_flow):
        """Analyze changes in flow metadata"""
        changes = []

        if old_flow.description != new_flow.description:
            changes.append(
                {
                    "type": self.change_types["FLOW_METADATA_CHANGED"],
                    "field": "description",
                    "old_value": old_flow.description,
                    "new_value": new_flow.description,
                    "impact": "low",
                }
            )

        if old_flow.version != new_flow.version:
            changes.append(
                {
                    "type": self.change_types["FLOW_METADATA_CHANGED"],
                    "field": "version",
                    "old_value": old_flow.version,
                    "new_value": new_flow.version,
                    "impact": "low",
                }
            )

        return changes

    def _analyze_step_changes(self, old_flow, new_flow):
        """Analyze changes in flow steps"""
        changes = []

        # Create step mappings
        old_steps = {step.step_id: step for step in old_flow.steps}
        new_steps = {step.step_id: step for step in new_flow.steps}

        # Find added steps
        added_steps = set(new_steps.keys()) - set(old_steps.keys())
        for step_id in added_steps:
            changes.append(
                {
                    "type": self.change_types["STEP_ADDED"],
                    "step_id": step_id,
                    "step_name": new_steps[step_id].name,
                    "agent_type": new_steps[step_id].agent_type,
                    "impact": "medium",
                }
            )

        # Find removed steps
        removed_steps = set(old_steps.keys()) - set(new_steps.keys())
        for step_id in removed_steps:
            changes.append(
                {
                    "type": self.change_types["STEP_REMOVED"],
                    "step_id": step_id,
                    "step_name": old_steps[step_id].name,
                    "agent_type": old_steps[step_id].agent_type,
                    "impact": "high",
                }
            )

        # Find modified steps
        common_steps = set(old_steps.keys()) & set(new_steps.keys())
        for step_id in common_steps:
            old_step = old_steps[step_id]
            new_step = new_steps[step_id]

            step_changes = self._analyze_single_step_changes(old_step, new_step)
            changes.extend(step_changes)

        return changes

    def _analyze_single_step_changes(self, old_step, new_step):
        """Analyze changes in a single step"""
        changes = []

        # Check agent type changes (breaking)
        if old_step.agent_type != new_step.agent_type:
            changes.append(
                {
                    "type": self.change_types["STEP_MODIFIED"],
                    "step_id": old_step.step_id,
                    "field": "agent_type",
                    "old_value": old_step.agent_type,
                    "new_value": new_step.agent_type,
                    "impact": "breaking",
                }
            )

        # Check name changes (low impact)
        if old_step.name != new_step.name:
            changes.append(
                {
                    "type": self.change_types["STEP_MODIFIED"],
                    "step_id": old_step.step_id,
                    "field": "name",
                    "old_value": old_step.name,
                    "new_value": new_step.name,
                    "impact": "low",
                }
            )

        # Check configuration changes
        if old_step.config != new_step.config:
            changes.append(
                {
                    "type": self.change_types["STEP_MODIFIED"],
                    "step_id": old_step.step_id,
                    "field": "config",
                    "old_value": old_step.config,
                    "new_value": new_step.config,
                    "impact": "medium",
                }
            )

        return changes

    def _determine_impact_level(self, changes):
        """Determine overall impact level of changes"""
        if not changes:
            return "none"

        impact_levels = [change.get("impact", "low") for change in changes]

        if "breaking" in impact_levels:
            return "breaking"
        elif "high" in impact_levels:
            return "high"
        elif "medium" in impact_levels:
            return "medium"
        else:
            return "low"

    def _requires_migration(self, changes):
        """Determine if changes require active session migration"""
        high_impact_changes = [
            self.change_types["STEP_REMOVED"],
            self.change_types["STEP_REORDERED"],
        ]

        for change in changes:
            if change["type"] in high_impact_changes:
                return True

            if change.get("impact") in ["high", "breaking"]:
                return True

        return False

    def _assess_compatibility(self, changes):
        """Assess compatibility level"""
        if not changes:
            return "full"

        breaking_changes = [
            change for change in changes if change.get("impact") == "breaking"
        ]
        if breaking_changes:
            return "incompatible"

        high_impact_changes = [
            change for change in changes if change.get("impact") == "high"
        ]
        if high_impact_changes:
            return "partial"

        return "full"

    def _determine_migration_strategy(self, analysis):
        """Determine the best migration strategy"""
        if not analysis["migration_required"]:
            return None

        compatibility = analysis["compatibility"]
        impact_level = analysis["impact_level"]

        if compatibility == "incompatible":
            return "restart_sessions"
        elif impact_level == "high":
            return "graceful_migration"
        else:
            return "hot_update"


class TestFlowUpdateAnalyzer(unittest.TestCase):
    """Test flow update analyzer"""

    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = FlowUpdateAnalyzer()

        # Create test flows
        self.old_flow = MockThinkingFlow(
            name="test_flow",
            description="Original test flow",
            version="1.0",
            steps=[
                MockFlowStep(
                    step_id="step1",
                    name="Step 1",
                    agent_type="decomposer",
                    config={"max_questions": 3},
                ),
                MockFlowStep(
                    step_id="step2",
                    name="Step 2",
                    agent_type="critic",
                    config={"standards": "basic"},
                ),
            ],
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
                    config={"max_questions": 3},
                ),
                MockFlowStep(
                    step_id="step2",
                    name="Step 2",
                    agent_type="critic",
                    config={"standards": "basic"},
                ),
            ],
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
                    config={"max_questions": 3},
                ),
                MockFlowStep(
                    step_id="step2",
                    name="Step 2",
                    agent_type="critic",
                    config={"standards": "basic"},
                ),
                MockFlowStep(
                    step_id="step3",
                    name="Step 3",
                    agent_type="reflector",
                    config={"depth": "shallow"},
                ),
            ],
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
                    config={"max_questions": 3},
                ),
            ],
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
                    config={"max_questions": 3},
                ),
                MockFlowStep(
                    step_id="step2",
                    name="Step 2",
                    agent_type="critic",
                    config={"standards": "basic"},
                ),
            ],
        )

    def test_analyze_metadata_changes(self):
        """Test analysis of metadata changes"""
        analysis = self.analyzer.analyze_flow_changes(
            self.old_flow, self.new_flow_minor_change
        )

        self.assertEqual(analysis["flow_name"], "test_flow")
        self.assertEqual(analysis["impact_level"], "low")
        self.assertFalse(analysis["migration_required"])
        self.assertEqual(analysis["compatibility"], "full")

        # Check for description and version changes
        change_types = [change["type"] for change in analysis["changes"]]
        self.assertIn("flow_metadata_changed", change_types)

    def test_analyze_step_added(self):
        """Test analysis when step is added"""
        analysis = self.analyzer.analyze_flow_changes(
            self.old_flow, self.new_flow_step_added
        )

        self.assertEqual(analysis["impact_level"], "medium")
        self.assertFalse(analysis["migration_required"])
        self.assertEqual(analysis["compatibility"], "full")

        # Check for step added change
        added_changes = [
            change for change in analysis["changes"] if change["type"] == "step_added"
        ]
        self.assertEqual(len(added_changes), 1)
        self.assertEqual(added_changes[0]["step_id"], "step3")

    def test_analyze_step_removed(self):
        """Test analysis when step is removed"""
        analysis = self.analyzer.analyze_flow_changes(
            self.old_flow, self.new_flow_step_removed
        )

        self.assertEqual(analysis["impact_level"], "high")
        self.assertTrue(analysis["migration_required"])
        self.assertEqual(analysis["compatibility"], "partial")

        # Check for step removed change
        removed_changes = [
            change for change in analysis["changes"] if change["type"] == "step_removed"
        ]
        self.assertEqual(len(removed_changes), 1)
        self.assertEqual(removed_changes[0]["step_id"], "step2")

    def test_analyze_breaking_change(self):
        """Test analysis of breaking changes"""
        analysis = self.analyzer.analyze_flow_changes(
            self.old_flow, self.new_flow_breaking_change
        )

        self.assertEqual(analysis["impact_level"], "breaking")
        self.assertTrue(analysis["migration_required"])
        self.assertEqual(analysis["compatibility"], "incompatible")
        self.assertEqual(analysis["migration_strategy"], "restart_sessions")

        # Check for agent type change
        breaking_changes = [
            change
            for change in analysis["changes"]
            if change.get("impact") == "breaking"
        ]
        self.assertGreater(len(breaking_changes), 0)

    def test_determine_migration_strategy(self):
        """Test migration strategy determination"""
        # Test no migration needed
        minor_analysis = self.analyzer.analyze_flow_changes(
            self.old_flow, self.new_flow_minor_change
        )
        self.assertIsNone(minor_analysis["migration_strategy"])

        # Test graceful migration strategy
        step_removed_analysis = self.analyzer.analyze_flow_changes(
            self.old_flow, self.new_flow_step_removed
        )
        self.assertEqual(
            step_removed_analysis["migration_strategy"], "graceful_migration"
        )

        # Test restart strategy
        breaking_analysis = self.analyzer.analyze_flow_changes(
            self.old_flow, self.new_flow_breaking_change
        )
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
                    config={"max_questions": 5},  # Changed from 3 to 5
                ),
                MockFlowStep(
                    step_id="step2",
                    name="Step 2",
                    agent_type="critic",
                    config={"standards": "basic"},
                ),
            ],
        )

        analysis = self.analyzer.analyze_flow_changes(
            self.old_flow, new_flow_config_change
        )

        self.assertEqual(analysis["impact_level"], "medium")
        self.assertFalse(analysis["migration_required"])
        self.assertEqual(analysis["compatibility"], "full")

        # Check for config change
        config_changes = [
            change
            for change in analysis["changes"]
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


def run_flow_analyzer_tests():
    """Run flow analyzer tests"""
    print("Running flow analyzer tests...")

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
    success = run_flow_analyzer_tests()
    exit(0 if success else 1)
