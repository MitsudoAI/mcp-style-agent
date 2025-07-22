"""
Tests for the Flow Executor
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from src.mcps.deep_thinking.config.exceptions import FlowExecutionError, TemplateError
from src.mcps.deep_thinking.flows.flow_executor import FlowExecutor
from src.mcps.deep_thinking.flows.flow_manager import FlowManager, FlowStep, FlowStatus, ThinkingFlow
from src.mcps.deep_thinking.templates.template_manager import TemplateManager


class TestFlowExecutor(unittest.TestCase):
    """Test cases for the Flow Executor"""

    def setUp(self):
        """Set up test fixtures"""
        self.flow_manager = MagicMock(spec=FlowManager)
        self.template_manager = MagicMock(spec=TemplateManager)
        self.db = MagicMock()
        
        # Mock state machine
        self.state_machine = MagicMock()
        self.flow_manager.state_machine = self.state_machine
        
        # Create flow executor
        self.flow_executor = FlowExecutor(
            flow_manager=self.flow_manager,
            template_manager=self.template_manager,
            db=self.db
        )
        
        # Mock flow and step
        self.flow = MagicMock(spec=ThinkingFlow)
        self.flow.flow_id = "test_flow_id"
        self.flow.flow_name = "Test Flow"
        self.flow.session_id = "test_session_id"
        self.flow.status = FlowStatus.RUNNING
        self.flow.context = {"test_key": "test_value"}
        self.flow.steps = {}
        
        self.step = MagicMock(spec=FlowStep)
        self.step.step_id = "test_step_id"
        self.step.step_name = "Test Step"
        self.step.step_type = "test"
        self.step.template_name = "test_template"
        self.step.status = "pending"
        
        # Add step to flow
        self.flow.steps[self.step.step_id] = self.step
        
        # Set up flow manager to return our flow
        self.flow_manager.get_flow.return_value = self.flow
        
        # Set up flow to return our step as the next step
        self.flow.get_next_step.return_value = self.step
        
        # Set up template manager
        self.template_manager.get_template.return_value = "Test template content"
        # Add has_template method to mock
        self.template_manager.has_template = MagicMock(return_value=False)

    def test_execute_step_success(self):
        """Test successful step execution"""
        # Set up dependencies check to succeed
        self.flow._check_dependencies.return_value = True
        
        # Execute step
        result = self.flow_executor.execute_step("test_flow_id", "test_step_id")
        
        # Verify result
        self.assertEqual(result["flow_id"], "test_flow_id")
        self.assertEqual(result["step_id"], "test_step_id")
        self.assertEqual(result["template_name"], "test_template")
        self.assertEqual(result["template_content"], "Test template content")
        self.assertEqual(result["status"], "completed")
        
        # Verify flow manager calls
        self.flow_manager.get_flow.assert_called_once_with("test_flow_id")
        
        # Verify template manager calls
        self.template_manager.get_template.assert_called_once()
        
        # Verify step was marked as in progress
        self.step.start.assert_called_once()

    def test_execute_step_flow_not_found(self):
        """Test step execution with flow not found"""
        # Set up flow manager to return None
        self.flow_manager.get_flow.return_value = None
        
        # Execute step and verify exception
        with self.assertRaises(FlowExecutionError) as context:
            self.flow_executor.execute_step("nonexistent_flow_id", "test_step_id")
        
        self.assertIn("Flow not found", str(context.exception))

    def test_execute_step_step_not_found(self):
        """Test step execution with step not found"""
        # Execute step and verify exception
        with self.assertRaises(FlowExecutionError) as context:
            self.flow_executor.execute_step("test_flow_id", "nonexistent_step_id")
        
        self.assertIn("Step not found", str(context.exception))

    def test_execute_step_dependencies_not_satisfied(self):
        """Test step execution with dependencies not satisfied"""
        # Set up dependencies check to fail
        self.flow._check_dependencies.return_value = False
        
        # Execute step and verify exception
        with self.assertRaises(FlowExecutionError) as context:
            self.flow_executor.execute_step("test_flow_id", "test_step_id")
        
        self.assertIn("Dependencies not satisfied", str(context.exception))

    def test_execute_step_template_error(self):
        """Test step execution with template error"""
        # Set up dependencies check to succeed
        self.flow._check_dependencies.return_value = True
        
        # Set up template manager to raise exception
        self.template_manager.get_template.side_effect = Exception("Template error")
        
        # Execute step and verify exception
        with self.assertRaises(FlowExecutionError) as context:
            self.flow_executor.execute_step("test_flow_id", "test_step_id")
        
        self.assertIn("Error executing step", str(context.exception))

    def test_execute_flow_success(self):
        """Test successful flow execution"""
        # Set up dependencies check to succeed
        self.flow._check_dependencies.return_value = True
        
        # Set up flow to return None after first step (to simulate completion)
        self.flow_manager.get_next_step_in_flow.side_effect = [self.step, None]
        
        # Execute flow
        result = self.flow_executor.execute_flow("test_flow_id")
        
        # Verify result
        self.assertEqual(result["flow_id"], "test_flow_id")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["steps_executed"], 1)
        self.assertEqual(result["steps_succeeded"], 1)
        self.assertEqual(result["steps_failed"], 0)
        
        # Verify flow manager calls
        self.flow_manager.get_flow.assert_called_once_with("test_flow_id")
        self.flow_manager.get_next_step_in_flow.assert_called_with("test_flow_id")

    def test_execute_flow_with_error(self):
        """Test flow execution with error"""
        # Set up dependencies check to succeed
        self.flow._check_dependencies.return_value = True
        
        # Set up execute_step to raise exception
        with patch.object(self.flow_executor, 'execute_step') as mock_execute_step:
            mock_execute_step.side_effect = FlowExecutionError("Test error")
            
            # Execute flow
            result = self.flow_executor.execute_flow("test_flow_id", continue_on_error=False)
            
            # Verify result
            self.assertEqual(result["flow_id"], "test_flow_id")
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["steps_executed"], 1)
            self.assertEqual(result["steps_succeeded"], 0)
            self.assertEqual(result["steps_failed"], 1)

    def test_execute_flow_continue_on_error(self):
        """Test flow execution with continue on error"""
        # Set up dependencies check to succeed
        self.flow._check_dependencies.return_value = True
        
        # Create a second step
        step2 = MagicMock(spec=FlowStep)
        step2.step_id = "test_step_id_2"
        step2.step_name = "Test Step 2"
        step2.step_type = "test"
        step2.template_name = "test_template"
        step2.status = "pending"
        
        # Set up flow to return steps then None
        self.flow_manager.get_next_step_in_flow.side_effect = [self.step, step2, None]
        
        # Set up execute_step to raise exception for first step only
        with patch.object(self.flow_executor, 'execute_step') as mock_execute_step:
            mock_execute_step.side_effect = [
                FlowExecutionError("Test error"),
                {"execution_id": "test_execution_id", "status": "completed"}
            ]
            
            # Execute flow with continue_on_error=True
            result = self.flow_executor.execute_flow("test_flow_id", continue_on_error=True)
            
            # Verify result
            self.assertEqual(result["flow_id"], "test_flow_id")
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["steps_executed"], 2)
            self.assertEqual(result["steps_succeeded"], 1)
            self.assertEqual(result["steps_failed"], 1)

    def test_get_execution_stats(self):
        """Test getting execution statistics"""
        # Set up some execution stats
        self.flow_executor.execution_stats = {
            "test_flow_id": {
                "total_executions": 5,
                "successful_executions": 4,
                "failed_executions": 1,
                "total_execution_time": 10.5,
                "steps": {
                    "test_step_id": {
                        "total_executions": 5,
                        "successful_executions": 4,
                        "failed_executions": 1,
                        "total_execution_time": 10.5,
                        "average_execution_time": 2.1,
                    }
                }
            }
        }
        
        # Get stats for specific flow
        flow_stats = self.flow_executor.get_execution_stats("test_flow_id")
        self.assertEqual(flow_stats["total_executions"], 5)
        self.assertEqual(flow_stats["successful_executions"], 4)
        self.assertEqual(flow_stats["failed_executions"], 1)
        
        # Get overall stats
        overall_stats = self.flow_executor.get_execution_stats()
        self.assertEqual(overall_stats["total_flows"], 1)
        self.assertEqual(overall_stats["total_executions"], 5)
        self.assertEqual(overall_stats["successful_executions"], 4)
        self.assertEqual(overall_stats["failed_executions"], 1)

    def test_template_selection(self):
        """Test template selection logic"""
        # Set up template manager to return True for complexity-specific templates
        self.template_manager.has_template.return_value = True
        
        # Test with high complexity
        self.flow.context["complexity"] = "high"
        template_name, _ = self.flow_executor._select_template(self.flow, self.step, self.flow.context)
        self.assertEqual(template_name, "test_template_high")
        
        # Test with low complexity
        self.flow.context["complexity"] = "low"
        template_name, _ = self.flow_executor._select_template(self.flow, self.step, self.flow.context)
        self.assertEqual(template_name, "test_template_low")
        
        # Test with template override in step config
        self.step.config = {"template": "override_template"}
        template_name, _ = self.flow_executor._select_template(self.flow, self.step, self.flow.context)
        self.assertEqual(template_name, "override_template")


if __name__ == "__main__":
    unittest.main()