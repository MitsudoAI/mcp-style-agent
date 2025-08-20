"""
Test for the for_each bug fix in flow execution.

This test verifies that when a step has for_each configuration,
all items in the referenced collection are processed.
"""

import json
import sys
import os

# Add src to path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from src.mcps.deep_thinking.flows.flow_executor import FlowExecutor
    from src.mcps.deep_thinking.flows.flow_manager import FlowManager
    from src.mcps.deep_thinking.templates.template_manager import TemplateManager
except ImportError as e:
    print(f"Import error: {e}")
    print("Running basic functionality tests without full imports...")


class MockStep:
    """Mock step for testing"""

    def __init__(self, step_id, for_each=None, config=None):
        self.step_id = step_id
        self.for_each = for_each
        self.config = config or {}
        self.status = "pending"


class MockFlowManager:
    """Mock flow manager for testing"""

    def __init__(self):
        self.current_step = 0
        self.steps = []

    def get_next_step_in_flow(self, flow_id):
        if self.current_step < len(self.steps):
            step = self.steps[self.current_step]
            self.current_step += 1
            return step
        return None


class MockTemplateManager:
    """Mock template manager for testing"""

    def get_template(self, template_name, params):
        return f"Template {template_name} with params: {params}"


def test_for_each_execution():
    """Test that for_each executes for all sub-questions"""

    # Setup mocks
    flow_manager = MockFlowManager()
    template_manager = MockTemplateManager()

    executor = FlowExecutor(flow_manager, template_manager)

    # Mock decomposer step output (what would be returned by decomposer)
    decomposer_output = {
        "main_question": "Test question",
        "sub_questions": [
            {"id": "SQ1", "question": "Sub-question 1"},
            {"id": "SQ2", "question": "Sub-question 2"},
            {"id": "SQ3", "question": "Sub-question 3"},
        ],
    }

    # Setup flow steps
    decomposer_step = MockStep("decomposer")
    evidence_step = MockStep("evidence_seeker", for_each="decomposer.sub_questions")

    flow_manager.steps = [decomposer_step, evidence_step]

    # Mock the execute_step method to return controlled outputs
    original_execute_step = executor.execute_step

    def mock_execute_step(flow_id, step_id, context):
        if step_id == "decomposer":
            return {
                "execution_id": "exec_1",
                "flow_id": flow_id,
                "step_id": step_id,
                "template_name": "decomposition",
                "template_content": json.dumps(decomposer_output),
                "context": context,
                "status": "completed",
                "execution_time_ms": 100,
            }
        elif step_id.startswith("evidence_seeker_iter_"):
            # Extract iteration info from context
            current_item = context.get("current_item", {})
            return {
                "execution_id": f"exec_{step_id}",
                "flow_id": flow_id,
                "step_id": step_id,
                "template_name": "evidence_collection",
                "template_content": f"Evidence for: {current_item.get('question', 'unknown')}",
                "context": context,
                "status": "completed",
                "execution_time_ms": 50,
            }
        else:
            return original_execute_step(flow_id, step_id, context)

    executor.execute_step = mock_execute_step

    # Execute the flow
    result = executor.execute_flow("test_flow")

    # Verify results
    assert result["status"] == "completed"
    assert result["steps_succeeded"] == 4  # 1 decomposer + 3 evidence iterations
    assert result["steps_failed"] == 0
    assert len(result["failed_steps"]) == 0

    # Verify step outputs contain all iterations
    step_outputs = result.get("step_outputs", {})
    assert "decomposer" in step_outputs
    assert "evidence_seeker" in step_outputs

    # Verify evidence_seeker results contain all 3 iterations
    evidence_results = step_outputs["evidence_seeker"]
    assert len(evidence_results) == 3

    # Verify each iteration was processed correctly
    for i, result_data in enumerate(evidence_results):
        assert result_data["iteration_index"] == i
        assert f"Sub-question {i+1}" in result_data["result"]
        assert result_data["iteration_item"]["id"] == f"SQ{i+1}"


def test_for_each_reference_resolution():
    """Test for_each reference resolution"""

    flow_manager = MockFlowManager()
    template_manager = MockTemplateManager()
    executor = FlowExecutor(flow_manager, template_manager)

    # Test data
    step_outputs = {
        "decomposer": json.dumps(
            {
                "sub_questions": [
                    {"id": "SQ1", "question": "Question 1"},
                    {"id": "SQ2", "question": "Question 2"},
                ]
            }
        )
    }

    context = {}

    # Test successful resolution
    result = executor._resolve_for_each_reference(
        "decomposer.sub_questions", step_outputs, context
    )
    assert len(result) == 2
    assert result[0]["id"] == "SQ1"
    assert result[1]["id"] == "SQ2"

    # Test invalid reference format
    result = executor._resolve_for_each_reference(
        "invalid_format", step_outputs, context
    )
    assert result == []

    # Test missing step
    result = executor._resolve_for_each_reference(
        "missing_step.sub_questions", step_outputs, context
    )
    assert result == []

    # Test missing property
    result = executor._resolve_for_each_reference(
        "decomposer.missing_property", step_outputs, context
    )
    assert result == []


def test_for_each_error_handling():
    """Test error handling in for_each execution"""

    flow_manager = MockFlowManager()
    template_manager = MockTemplateManager()
    executor = FlowExecutor(flow_manager, template_manager)

    # Mock step that will fail on second iteration
    def failing_execute_step(flow_id, step_id, context):
        if "iter_1" in step_id:  # Fail on second iteration
            raise Exception("Simulated error")
        return {
            "execution_id": f"exec_{step_id}",
            "template_content": "Success",
            "context": context,
            "status": "completed",
        }

    executor.execute_step = failing_execute_step

    # Test data
    iteration_data = [{"id": "1"}, {"id": "2"}, {"id": "3"}]
    step = MockStep("test_step", for_each="test.items")

    # Test with continue_on_error=True
    result = executor._execute_step_with_for_each(
        "test_flow",
        step,
        "test.items",
        {},
        {"test": {"items": iteration_data}},
        continue_on_error=True,
    )

    assert result["steps_executed"] == 3
    assert result["steps_succeeded"] == 2
    assert result["steps_failed"] == 1
    assert len(result["failed_steps"]) == 1
    assert "iter_1" in result["failed_steps"][0]["step_id"]


if __name__ == "__main__":
    test_for_each_execution()
    test_for_each_reference_resolution()
    test_for_each_error_handling()
    print("All tests passed!")
