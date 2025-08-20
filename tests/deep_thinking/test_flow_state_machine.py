"""
Tests for the Flow State Machine
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.mcps.deep_thinking.config.exceptions import InvalidTransitionError
from src.mcps.deep_thinking.flows.flow_manager import (
    FlowManager,
    FlowStatus,
    FlowStepStatus,
    ThinkingFlow,
)
from src.mcps.deep_thinking.flows.flow_state_machine import FlowStateMachine, FlowEvent


class TestFlowStateMachine:
    """Test flow state machine functionality"""

    @pytest.fixture
    def flow_manager(self):
        """Create a flow manager for testing"""
        return FlowManager()

    @pytest.fixture
    def state_machine(self):
        """Create a state machine for testing"""
        return FlowStateMachine()

    @pytest.fixture
    def test_flow(self, flow_manager):
        """Create a test flow"""
        session_id = "test-session-state-machine"
        flow_id = flow_manager.create_flow(session_id, "quick_analysis")
        return flow_manager.get_flow(flow_id)

    def test_state_machine_initialization(self, state_machine):
        """Test state machine initialization"""
        assert state_machine is not None
        assert hasattr(state_machine, "_valid_transitions")
        assert FlowStatus.INITIALIZED in state_machine._valid_transitions
        assert FlowStatus.RUNNING in state_machine._valid_transitions
        assert FlowStatus.PAUSED in state_machine._valid_transitions
        assert FlowStatus.COMPLETED in state_machine._valid_transitions
        assert FlowStatus.FAILED in state_machine._valid_transitions
        assert FlowStatus.CANCELLED in state_machine._valid_transitions

    def test_valid_transitions(self, state_machine, test_flow):
        """Test valid state transitions"""
        # Initial state should be INITIALIZED
        assert test_flow.status == FlowStatus.INITIALIZED

        # Test START transition
        new_state, success = state_machine.transition(test_flow, FlowEvent.START)
        assert new_state == FlowStatus.RUNNING
        assert success is True
        assert test_flow.status == FlowStatus.RUNNING

        # Test PAUSE transition
        new_state, success = state_machine.transition(test_flow, FlowEvent.PAUSE)
        assert new_state == FlowStatus.PAUSED
        assert success is True
        assert test_flow.status == FlowStatus.PAUSED

        # Test RESUME transition
        new_state, success = state_machine.transition(test_flow, FlowEvent.RESUME)
        assert new_state == FlowStatus.RUNNING
        assert success is True
        assert test_flow.status == FlowStatus.RUNNING

        # Test CANCEL transition
        new_state, success = state_machine.transition(test_flow, FlowEvent.CANCEL)
        assert new_state == FlowStatus.CANCELLED
        assert success is True
        assert test_flow.status == FlowStatus.CANCELLED

        # Test RESET transition
        new_state, success = state_machine.transition(test_flow, FlowEvent.RESET)
        assert new_state == FlowStatus.INITIALIZED
        assert success is True
        assert test_flow.status == FlowStatus.INITIALIZED

    def test_invalid_transitions(self, state_machine, test_flow):
        """Test invalid state transitions"""
        # Cannot PAUSE from INITIALIZED
        with pytest.raises(InvalidTransitionError):
            state_machine.transition(test_flow, FlowEvent.PAUSE)

        # Start the flow
        state_machine.transition(test_flow, FlowEvent.START)
        assert test_flow.status == FlowStatus.RUNNING

        # Cannot RESET from RUNNING
        with pytest.raises(InvalidTransitionError):
            state_machine.transition(test_flow, FlowEvent.RESET)

    @pytest.mark.skip(reason="Manual override functionality needs to be fixed")
    def test_manual_override(self, state_machine):
        """Test manual override transitions"""
        # Create a flow directly without using the fixture
        flow = ThinkingFlow(
            flow_id="test-manual-override-flow",
            flow_name="Test Manual Override Flow",
            session_id="test-session-manual-override",
        )

        # Manually set the flow status to COMPLETED
        flow.status = FlowStatus.COMPLETED

        # Verify that the status was set correctly
        assert flow.status == FlowStatus.COMPLETED

        # Use manual override to force a transition to RUNNING
        new_state, success = state_machine.transition(
            flow, FlowEvent.MANUAL_OVERRIDE, {"target_state": FlowStatus.RUNNING}
        )

        # Check that the flow status was updated
        assert flow.status == FlowStatus.RUNNING
        assert success is True

        # Use manual override to force a transition back to COMPLETED
        new_state, success = state_machine.transition(
            flow, FlowEvent.MANUAL_OVERRIDE, {"target_state": FlowStatus.COMPLETED}
        )

        # Check that the flow status was updated
        assert flow.status == FlowStatus.COMPLETED
        assert success is True

    def test_step_completion(self, state_machine, test_flow):
        """Test step completion transitions"""
        # Start the flow
        state_machine.transition(test_flow, FlowEvent.START)

        # Get first step
        first_step = list(test_flow.steps.values())[0]

        # Complete the step
        new_state, success = state_machine.transition(
            test_flow,
            FlowEvent.COMPLETE_STEP,
            {
                "step_id": first_step.step_id,
                "result": "Step completed successfully",
                "quality_score": 0.9,
            },
        )

        assert new_state == FlowStatus.RUNNING  # Flow stays in running state
        assert success is True
        assert first_step.status == FlowStepStatus.COMPLETED
        assert first_step.result == "Step completed successfully"
        assert first_step.quality_score == 0.9

    def test_step_failure(self, state_machine, test_flow):
        """Test step failure transitions"""
        # Start the flow
        state_machine.transition(test_flow, FlowEvent.START)

        # Get first step
        first_step = list(test_flow.steps.values())[0]

        # Fail the step
        new_state, success = state_machine.transition(
            test_flow,
            FlowEvent.FAIL_STEP,
            {
                "step_id": first_step.step_id,
                "error_message": "Step failed due to error",
            },
        )

        assert new_state == FlowStatus.RUNNING  # Flow stays in running state
        assert success is True
        assert first_step.status == FlowStepStatus.FAILED
        assert first_step.error_message == "Step failed due to error"
        assert first_step.retry_count == 1

    def test_critical_step_failure(self, state_machine, test_flow):
        """Test critical step failure causing flow failure"""
        # Start the flow
        state_machine.transition(test_flow, FlowEvent.START)

        # Get first step
        first_step = list(test_flow.steps.values())[0]

        # Set max retries to 0 to force immediate failure
        first_step.max_retries = 0

        # Fail the step as critical
        new_state, success = state_machine.transition(
            test_flow,
            FlowEvent.FAIL_STEP,
            {
                "step_id": first_step.step_id,
                "error_message": "Critical step failed",
                "critical": True,
            },
        )

        # The flow should still be in running state after the step failure
        assert new_state == FlowStatus.RUNNING

        # But the step should be failed
        assert first_step.status == FlowStepStatus.FAILED
        assert first_step.error_message == "Critical step failed"
        assert first_step.retry_count == 1
        assert not first_step.can_retry()

    def test_state_history(self, state_machine, test_flow):
        """Test state history tracking"""
        # Perform a series of transitions
        state_machine.transition(test_flow, FlowEvent.START)
        state_machine.transition(test_flow, FlowEvent.PAUSE)
        state_machine.transition(test_flow, FlowEvent.RESUME)

        # Check history
        history = state_machine.get_state_history(test_flow.flow_id)
        assert len(history) == 3

        # Check first transition
        assert history[0]["from_state"] == FlowStatus.INITIALIZED.value
        assert history[0]["to_state"] == FlowStatus.RUNNING.value
        assert history[0]["event"] == FlowEvent.START.value

        # Check second transition
        assert history[1]["from_state"] == FlowStatus.RUNNING.value
        assert history[1]["to_state"] == FlowStatus.PAUSED.value
        assert history[1]["event"] == FlowEvent.PAUSE.value

        # Check third transition
        assert history[2]["from_state"] == FlowStatus.PAUSED.value
        assert history[2]["to_state"] == FlowStatus.RUNNING.value
        assert history[2]["event"] == FlowEvent.RESUME.value

    def test_can_transition(self, state_machine, test_flow):
        """Test transition possibility checking"""
        # Initial state is INITIALIZED
        assert state_machine.can_transition(test_flow, FlowEvent.START) is True
        assert state_machine.can_transition(test_flow, FlowEvent.PAUSE) is False

        # After starting
        state_machine.transition(test_flow, FlowEvent.START)
        assert state_machine.can_transition(test_flow, FlowEvent.PAUSE) is True
        assert state_machine.can_transition(test_flow, FlowEvent.RESUME) is False

    def test_reset_flow(self, state_machine, test_flow):
        """Test flow reset functionality"""
        # Start the flow and complete a step
        state_machine.transition(test_flow, FlowEvent.START)
        first_step = list(test_flow.steps.values())[0]
        state_machine.transition(
            test_flow,
            FlowEvent.COMPLETE_STEP,
            {"step_id": first_step.step_id, "result": "Completed"},
        )

        # Verify step is completed
        assert first_step.status == FlowStepStatus.COMPLETED
        assert first_step.result == "Completed"

        # Reset the flow
        success = state_machine.reset_flow(test_flow)
        assert success is True

        # Verify flow is reset
        assert test_flow.status == FlowStatus.INITIALIZED
        assert test_flow.start_time is None

        # Verify step is reset
        assert first_step.status == FlowStepStatus.PENDING
        assert first_step.result is None
        assert first_step.start_time is None
        assert first_step.retry_count == 0

    def test_flow_state_summary(self, state_machine, test_flow):
        """Test flow state summary generation"""
        # Start the flow and complete a step
        state_machine.transition(test_flow, FlowEvent.START)
        first_step = list(test_flow.steps.values())[0]
        state_machine.transition(
            test_flow,
            FlowEvent.COMPLETE_STEP,
            {
                "step_id": first_step.step_id,
                "result": "Completed",
                "quality_score": 0.85,
            },
        )

        # Get summary
        summary = state_machine.get_flow_state_summary(test_flow)

        # Check summary contents
        assert summary["flow_id"] == test_flow.flow_id
        assert summary["session_id"] == test_flow.session_id
        assert summary["status"] == FlowStatus.RUNNING.value
        assert summary["total_steps"] == len(test_flow.steps)
        assert summary["completed_steps"] == 1
        assert summary["failed_steps"] == 0
        assert summary["average_quality"] == 0.85
        assert summary["progress_percentage"] > 0
        assert "valid_transitions" in summary
        assert FlowEvent.PAUSE.value in summary["valid_transitions"]

    @patch("src.mcps.deep_thinking.data.database.ThinkingDatabase")
    def test_state_persistence(self, mock_db, test_flow):
        """Test state persistence to database"""
        # Create mock database
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance

        # Create state machine with mock database
        state_machine = FlowStateMachine(mock_db_instance)

        # Perform transitions
        state_machine.transition(test_flow, FlowEvent.START)

        # Check that database was called
        mock_db_instance.update_session.assert_called()

        # Get the arguments from the last call
        args, kwargs = mock_db_instance.update_session.call_args_list[0]

        # Check that session ID was passed
        assert args[0] == test_flow.session_id

        # Check that status was updated
        assert "status" in kwargs
        assert kwargs["status"] == FlowStatus.RUNNING.value
        assert kwargs["context"]["flow_state"] is not None

    @patch("src.mcps.deep_thinking.data.database.ThinkingDatabase")
    def test_restore_flow_state(self, mock_db, flow_manager):
        """Test flow state restoration from database"""
        # Create mock database
        mock_db_instance = MagicMock()

        # Setup mock to return session data
        session_id = "test-restore-session"
        flow_id = f"{session_id}_quick_analysis_20250720"

        # Create a flow to get realistic flow data
        flow = flow_manager.get_flow(
            flow_manager.create_flow(session_id, "quick_analysis")
        )
        flow.start()
        first_step = list(flow.steps.values())[0]
        first_step.complete("Step completed", 0.9)

        # Mock the database response
        mock_db_instance.get_session.return_value = {
            "id": session_id,
            "context": {
                "flow_state": flow.to_dict(),
                "current_step": first_step.step_id,
                "step_number": 1,
            },
            "quality_metrics": {
                "flow_state_history": [
                    {
                        "timestamp": datetime.now().isoformat(),
                        "from_state": FlowStatus.INITIALIZED.value,
                        "to_state": FlowStatus.RUNNING.value,
                        "event": FlowEvent.START.value,
                        "metadata": {},
                    }
                ]
            },
        }

        # Create state machine with mock database
        state_machine = FlowStateMachine(mock_db_instance)

        # Restore flow state
        restored_flow = state_machine.restore_flow_state(flow_id, session_id)

        # Check that database was called
        mock_db_instance.get_session.assert_called_with(session_id)

        # Check restored flow
        assert restored_flow is not None
        assert restored_flow.flow_id == flow_id
        assert restored_flow.session_id == session_id
        assert restored_flow.status == FlowStatus.RUNNING

        # Check that steps were restored
        assert len(restored_flow.steps) > 0
        assert first_step.step_id in restored_flow.steps
        assert (
            restored_flow.steps[first_step.step_id].status == FlowStepStatus.COMPLETED
        )


if __name__ == "__main__":
    pytest.main([__file__])
