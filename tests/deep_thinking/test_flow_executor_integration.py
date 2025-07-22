"""
Integration tests for the Flow Executor
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from src.mcps.deep_thinking.config.exceptions import FlowExecutionError
from src.mcps.deep_thinking.flows.flow_executor import FlowExecutor
from src.mcps.deep_thinking.flows.flow_manager import FlowManager, FlowStep, FlowStatus, ThinkingFlow
from src.mcps.deep_thinking.templates.template_manager import TemplateManager


class TestFlowExecutorIntegration(unittest.TestCase):
    """Integration tests for the Flow Executor"""

    def setUp(self):
        """Set up test fixtures"""
        # Create real components with mocked dependencies
        self.db = MagicMock()
        self.flow_manager = FlowManager(self.db)
        self.template_manager = TemplateManager()
        
        # Add test templates
        self.template_manager.add_template = MagicMock()
        self.template_manager.get_template = MagicMock(return_value="Test template content")
        self.template_manager.has_template = MagicMock(return_value=False)
        
        # Create flow executor
        self.flow_executor = FlowExecutor(
            flow_manager=self.flow_manager,
            template_manager=self.template_manager,
            db=self.db
        )
        
        # Create test flow
        self.flow_id = self.flow_manager.create_flow("test_session_id", "comprehensive_analysis")
        
        # Mock state machine
        self.flow_manager.state_machine = MagicMock()

    def test_execute_step_integration(self):
        """Test step execution integration"""
        # Get flow
        flow = self.flow_manager.get_flow(self.flow_id)
        self.assertIsNotNone(flow)
        
        # Get first step
        step = list(flow.steps.values())[0]
        self.assertIsNotNone(step)
        
        # Mock dependencies check
        flow._check_dependencies = MagicMock(return_value=True)
        
        # Execute step
        result = self.flow_executor.execute_step(self.flow_id, step.step_id)
        
        # Verify result
        self.assertEqual(result["flow_id"], self.flow_id)
        self.assertEqual(result["step_id"], step.step_id)
        self.assertEqual(result["status"], "completed")
        self.assertIn("template_content", result)
        self.assertIn("execution_time_ms", result)

    def test_execute_flow_integration(self):
        """Test flow execution integration"""
        # Get flow
        flow = self.flow_manager.get_flow(self.flow_id)
        self.assertIsNotNone(flow)
        
        # Mock dependencies check for all steps
        flow._check_dependencies = MagicMock(return_value=True)
        
        # Mock get_next_step_in_flow to return steps in sequence
        steps = list(flow.steps.values())
        self.flow_manager.get_next_step_in_flow = MagicMock(side_effect=steps + [None])
        
        # Execute flow
        result = self.flow_executor.execute_flow(self.flow_id)
        
        # Verify result
        self.assertEqual(result["flow_id"], self.flow_id)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["steps_executed"], len(steps))
        self.assertEqual(result["steps_succeeded"], len(steps))
        self.assertEqual(result["steps_failed"], 0)
        self.assertIn("execution_time_ms", result)

    def test_error_handling_integration(self):
        """Test error handling integration"""
        # Get flow
        flow = self.flow_manager.get_flow(self.flow_id)
        self.assertIsNotNone(flow)
        
        # Get first step
        step = list(flow.steps.values())[0]
        self.assertIsNotNone(step)
        
        # Mock dependencies check
        flow._check_dependencies = MagicMock(return_value=True)
        
        # Mock template manager to raise exception
        self.template_manager.get_template.side_effect = Exception("Template error")
        
        # Execute step and verify exception
        with self.assertRaises(FlowExecutionError) as context:
            self.flow_executor.execute_step(self.flow_id, step.step_id)
        
        self.assertIn("Error executing step", str(context.exception))
        
        # Test error handling
        error_info = self.flow_executor.handle_error(self.flow_id, step.step_id, context.exception)
        
        # Verify error handling info
        self.assertEqual(error_info["flow_id"], self.flow_id)
        self.assertEqual(error_info["step_id"], step.step_id)
        self.assertIn("error_message", error_info)
        self.assertIn("recovery_options", error_info)
        self.assertIn("diagnostics", error_info)

    def test_template_selection_integration(self):
        """Test template selection integration"""
        # Get flow
        flow = self.flow_manager.get_flow(self.flow_id)
        self.assertIsNotNone(flow)
        
        # Get first step
        step = list(flow.steps.values())[0]
        self.assertIsNotNone(step)
        
        # Set up template manager
        self.template_manager.has_template = MagicMock(return_value=True)
        
        # Test with high complexity
        flow.context = {"complexity": "high"}
        template_name, _ = self.flow_executor._select_template(flow, step, flow.context)
        self.assertEqual(template_name, f"{step.template_name}_high")
        
        # Test with low complexity
        flow.context = {"complexity": "low"}
        template_name, _ = self.flow_executor._select_template(flow, step, flow.context)
        self.assertEqual(template_name, f"{step.template_name}_low")
        
        # Test with template override in step config
        step.config = {"template": "override_template"}
        template_name, _ = self.flow_executor._select_template(flow, step, flow.context)
        self.assertEqual(template_name, "override_template")


if __name__ == "__main__":
    unittest.main()