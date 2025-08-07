"""
Unit tests for Flow Interruption Recovery functionality
Tests flow interruption detection and recovery mechanisms
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.mcps.deep_thinking.data.database import ThinkingDatabase
from src.mcps.deep_thinking.models.mcp_models import SessionState
from src.mcps.deep_thinking.sessions.session_manager import SessionManager


class TestFlowInterruptionRecovery:
    """Test suite for flow interruption recovery functionality"""

    @pytest.fixture
    def mock_db(self):
        """Create mock database"""
        return Mock(spec=ThinkingDatabase)

    @pytest.fixture
    def session_manager(self, mock_db):
        """Create session manager with mock database"""
        with patch('src.mcps.deep_thinking.sessions.session_manager.ThinkingDatabase', return_value=mock_db):
            return SessionManager(db_path=":memory:")

    @pytest.fixture
    def sample_session(self):
        """Create a sample session for testing"""
        return SessionState(
            session_id="test-session-123",
            topic="Test topic",
            current_step="collect_evidence",
            flow_type="comprehensive_analysis",
            context={"complexity": "moderate"},
            step_results={
                "decompose_problem": {
                    "result": "Problem decomposed",
                    "quality_score": 0.8
                }
            },
            quality_scores={"decompose_problem": 0.8},
            step_number=1,
            status="active",
            created_at=datetime.now() - timedelta(minutes=10),
            updated_at=datetime.now() - timedelta(minutes=5)
        )

    def test_detect_flow_interruption_no_interruption(self, session_manager, sample_session):
        """Test flow interruption detection when no interruption exists"""
        session_manager._active_sessions[sample_session.session_id] = sample_session
        
        # Update session to be recent and set current step to a completed step
        sample_session.updated_at = datetime.now()
        sample_session.step_results["collect_evidence"] = {"result": "Evidence collected", "quality_score": 0.8}
        sample_session.quality_scores["collect_evidence"] = 0.8
        sample_session.current_step = "collect_evidence"  # Set to completed step
        
        result = session_manager.detect_flow_interruption(sample_session.session_id)
        
        assert result is None

    def test_detect_flow_interruption_session_timeout(self, session_manager, sample_session):
        """Test flow interruption detection for session timeout"""
        session_manager._active_sessions[sample_session.session_id] = sample_session
        
        # Set session to be old (more than 30 minutes)
        sample_session.updated_at = datetime.now() - timedelta(minutes=35)
        
        result = session_manager.detect_flow_interruption(sample_session.session_id)
        
        assert result is not None
        assert result["interrupted"] is True
        assert "session_timeout" in result["reasons"]
        assert result["timeout_duration"] == "35.0 minutes"
        assert result["recovery_needed"] is True
        assert "resume_from_last_step" in result["recovery_options"]

    def test_detect_flow_interruption_incomplete_step(self, session_manager, sample_session):
        """Test flow interruption detection for incomplete step execution"""
        session_manager._active_sessions[sample_session.session_id] = sample_session
        
        # Set current step that's not in step_results
        sample_session.current_step = "multi_perspective_debate"
        sample_session.updated_at = datetime.now()  # Recent update to avoid timeout
        
        result = session_manager.detect_flow_interruption(sample_session.session_id)
        
        assert result is not None
        assert result["interrupted"] is True
        assert "incomplete_step_execution" in result["reasons"]
        assert result["incomplete_step"] == "multi_perspective_debate"
        assert "retry_current_step" in result["recovery_options"]

    def test_detect_flow_interruption_quality_gate_failure(self, session_manager, sample_session):
        """Test flow interruption detection for quality gate failure"""
        session_manager._active_sessions[sample_session.session_id] = sample_session
        
        # Add low quality scores
        sample_session.quality_scores = {
            "decompose_problem": 0.5,  # Below 0.6 threshold
            "collect_evidence": 0.4
        }
        sample_session.updated_at = datetime.now()
        
        result = session_manager.detect_flow_interruption(sample_session.session_id)
        
        assert result is not None
        assert result["interrupted"] is True
        assert "quality_gate_failure" in result["reasons"]
        assert "decompose_problem" in result["low_quality_steps"]
        assert "collect_evidence" in result["low_quality_steps"]
        assert "improve_quality" in result["recovery_options"]

    def test_detect_flow_interruption_missing_prerequisites(self, session_manager, sample_session):
        """Test flow interruption detection for missing prerequisites"""
        session_manager._active_sessions[sample_session.session_id] = sample_session
        
        # Set step results that skip prerequisites
        sample_session.step_results = {
            "multi_perspective_debate": {"result": "Debate completed"}  # Missing collect_evidence prerequisite
        }
        sample_session.updated_at = datetime.now()
        
        result = session_manager.detect_flow_interruption(sample_session.session_id)
        
        assert result is not None
        assert result["interrupted"] is True
        assert "missing_prerequisites" in result["reasons"]
        assert ("multi_perspective_debate", "collect_evidence") in result["missing_prerequisites"]
        assert "execute_missing_steps" in result["recovery_options"]

    def test_detect_flow_interruption_unexpected_step_sequence(self, session_manager, sample_session):
        """Test flow interruption detection for unexpected step sequence"""
        session_manager._active_sessions[sample_session.session_id] = sample_session
        
        # Set unexpected current step
        sample_session.step_results = {"decompose_problem": {"result": "Done"}}
        sample_session.current_step = "critical_evaluation"  # Should be collect_evidence
        sample_session.updated_at = datetime.now()
        
        result = session_manager.detect_flow_interruption(sample_session.session_id)
        
        assert result is not None
        assert result["interrupted"] is True
        assert "unexpected_step_sequence" in result["reasons"]
        assert result["expected_step"] == "collect_evidence"
        assert result["actual_step"] == "critical_evaluation"
        assert "correct_step_sequence" in result["recovery_options"]

    def test_detect_flow_interruption_session_not_found(self, session_manager, mock_db):
        """Test flow interruption detection when session not found"""
        # Ensure the session doesn't exist in active sessions
        session_manager._active_sessions.clear()
        
        # Mock database to return None for session lookup
        mock_db.get_session.return_value = None
        
        result = session_manager.detect_flow_interruption("nonexistent-session")
        
        assert result is not None
        assert result["interrupted"] is True
        assert result["reason"] == "session_not_found"
        assert result["recovery_needed"] is True

    def test_rollback_to_step_success(self, session_manager, sample_session, mock_db):
        """Test successful rollback to a specific step"""
        session_manager._active_sessions[sample_session.session_id] = sample_session
        
        # Add more completed steps
        sample_session.step_results = {
            "decompose_problem": {"result": "Step 1"},
            "collect_evidence": {"result": "Step 2"},
            "multi_perspective_debate": {"result": "Step 3"}
        }
        sample_session.quality_scores = {
            "decompose_problem": 0.8,
            "collect_evidence": 0.7,
            "multi_perspective_debate": 0.6
        }
        sample_session.current_step = "critical_evaluation"
        sample_session.step_number = 3
        
        # Mock database operations
        mock_db.update_session.return_value = True
        mock_db.add_session_step.return_value = 1
        mock_db.add_step_result.return_value = True
        
        result = session_manager.rollback_to_step(sample_session.session_id, "collect_evidence")
        
        assert result is True
        assert sample_session.current_step == "collect_evidence"
        assert sample_session.step_number == 2
        assert "multi_perspective_debate" not in sample_session.step_results
        assert "multi_perspective_debate" not in sample_session.quality_scores
        assert "rollback_history" in sample_session.context
        assert len(sample_session.context["rollback_history"]) == 1

    def test_rollback_to_step_session_not_found(self, session_manager):
        """Test rollback when session not found"""
        result = session_manager.rollback_to_step("nonexistent-session", "some_step")
        
        assert result is False

    def test_rollback_to_step_target_not_found(self, session_manager, sample_session):
        """Test rollback when target step not found"""
        session_manager._active_sessions[sample_session.session_id] = sample_session
        
        result = session_manager.rollback_to_step(sample_session.session_id, "nonexistent_step")
        
        assert result is False

    def test_create_recovery_checkpoint_success(self, session_manager, sample_session, mock_db):
        """Test successful creation of recovery checkpoint"""
        session_manager._active_sessions[sample_session.session_id] = sample_session
        
        # Mock database operations
        mock_db.add_session_step.return_value = 1
        mock_db.add_step_result.return_value = True
        
        checkpoint_id = session_manager.create_recovery_checkpoint(sample_session.session_id)
        
        assert checkpoint_id is not None
        assert checkpoint_id.startswith(f"{sample_session.session_id}_checkpoint_")
        assert "checkpoints" in sample_session.context
        assert len(sample_session.context["checkpoints"]) == 1
        
        checkpoint = sample_session.context["checkpoints"][0]
        assert checkpoint["checkpoint_id"] == checkpoint_id
        assert checkpoint["session_id"] == sample_session.session_id
        assert "session_state" in checkpoint

    def test_create_recovery_checkpoint_session_not_found(self, session_manager):
        """Test checkpoint creation when session not found"""
        checkpoint_id = session_manager.create_recovery_checkpoint("nonexistent-session")
        
        assert checkpoint_id is None

    def test_restore_from_checkpoint_success(self, session_manager, sample_session, mock_db):
        """Test successful restore from checkpoint"""
        session_manager._active_sessions[sample_session.session_id] = sample_session
        
        # Create a checkpoint first
        original_step = sample_session.current_step
        original_results = sample_session.step_results.copy()
        
        checkpoint_id = session_manager.create_recovery_checkpoint(sample_session.session_id)
        
        # Modify session state
        sample_session.current_step = "different_step"
        sample_session.step_results["new_step"] = {"result": "New result"}
        
        # Mock database operations
        mock_db.update_session.return_value = True
        
        result = session_manager.restore_from_checkpoint(sample_session.session_id, checkpoint_id)
        
        assert result is True
        assert sample_session.current_step == original_step
        assert sample_session.step_results == original_results
        assert "restored_from_checkpoint" in sample_session.context
        assert sample_session.context["restored_from_checkpoint"]["checkpoint_id"] == checkpoint_id

    def test_restore_from_checkpoint_session_not_found(self, session_manager):
        """Test restore when session not found"""
        result = session_manager.restore_from_checkpoint("nonexistent-session", "some-checkpoint")
        
        assert result is False

    def test_restore_from_checkpoint_checkpoint_not_found(self, session_manager, sample_session):
        """Test restore when checkpoint not found"""
        session_manager._active_sessions[sample_session.session_id] = sample_session
        
        result = session_manager.restore_from_checkpoint(sample_session.session_id, "nonexistent-checkpoint")
        
        assert result is False

    def test_get_expected_steps_for_flow(self, session_manager):
        """Test getting expected steps for different flow types"""
        comprehensive_steps = session_manager._get_expected_steps_for_flow("comprehensive_analysis")
        assert "decompose_problem" in comprehensive_steps
        assert "collect_evidence" in comprehensive_steps
        assert "reflection" in comprehensive_steps
        
        quick_steps = session_manager._get_expected_steps_for_flow("quick_analysis")
        assert "simple_decompose" in quick_steps
        assert "brief_reflection" in quick_steps
        
        unknown_steps = session_manager._get_expected_steps_for_flow("unknown_flow")
        assert unknown_steps == []

    def test_get_step_prerequisites(self, session_manager):
        """Test getting step prerequisites"""
        prereqs = session_manager._get_step_prerequisites("collect_evidence")
        assert "decompose_problem" in prereqs
        
        prereqs = session_manager._get_step_prerequisites("multi_perspective_debate")
        assert "collect_evidence" in prereqs
        
        prereqs = session_manager._get_step_prerequisites("decompose_problem")
        assert prereqs == []

    def test_get_expected_next_step(self, session_manager):
        """Test getting expected next step"""
        next_step = session_manager._get_expected_next_step("decompose_problem", "comprehensive_analysis")
        assert next_step == "collect_evidence"
        
        next_step = session_manager._get_expected_next_step("reflection", "comprehensive_analysis")
        assert next_step is None  # Last step
        
        next_step = session_manager._get_expected_next_step("unknown_step", "comprehensive_analysis")
        assert next_step is None

    def test_generate_recovery_options(self, session_manager):
        """Test generation of recovery options"""
        interruption_details = {
            "reasons": ["session_timeout", "quality_gate_failure"]
        }
        
        options = session_manager._generate_recovery_options(interruption_details)
        
        assert "resume_from_last_step" in options
        assert "improve_quality" in options
        assert "restart_flow" in options
        
        # Test with no specific reasons
        empty_details = {"reasons": []}
        options = session_manager._generate_recovery_options(empty_details)
        
        assert "retry_current_step" in options
        assert "rollback_to_previous" in options
        assert "restart_flow" in options

    def test_detect_flow_interruption_exception_handling(self, session_manager):
        """Test flow interruption detection with exception"""
        # Mock get_session to raise exception
        with patch.object(session_manager, 'get_session', side_effect=Exception("Database error")):
            result = session_manager.detect_flow_interruption("test-session")
            
            assert result is not None
            assert result["interrupted"] is True
            assert result["reason"] == "detection_error"
            assert "Database error" in result["error"]

    def test_rollback_database_failure_continues(self, session_manager, sample_session, mock_db):
        """Test that rollback continues even if database update fails"""
        session_manager._active_sessions[sample_session.session_id] = sample_session
        
        # Add completed steps
        sample_session.step_results = {
            "decompose_problem": {"result": "Step 1"},
            "collect_evidence": {"result": "Step 2"}
        }
        sample_session.current_step = "multi_perspective_debate"
        
        # Mock database to fail
        mock_db.update_session.side_effect = Exception("Database error")
        
        result = session_manager.rollback_to_step(sample_session.session_id, "decompose_problem")
        
        # Should still succeed with in-memory rollback
        assert result is True
        assert sample_session.current_step == "decompose_problem"
        assert "collect_evidence" not in sample_session.step_results

    def test_checkpoint_database_failure_continues(self, session_manager, sample_session, mock_db):
        """Test that checkpoint creation continues even if database storage fails"""
        session_manager._active_sessions[sample_session.session_id] = sample_session
        
        # Mock database to fail
        mock_db.add_session_step.side_effect = Exception("Database error")
        
        checkpoint_id = session_manager.create_recovery_checkpoint(sample_session.session_id)
        
        # Should still succeed with in-memory checkpoint
        assert checkpoint_id is not None
        assert "checkpoints" in sample_session.context
        assert len(sample_session.context["checkpoints"]) == 1

    @patch('src.mcps.deep_thinking.sessions.session_manager.logger')
    def test_interruption_detection_logging(self, mock_logger, session_manager, sample_session):
        """Test that interruption detection is properly logged"""
        session_manager._active_sessions[sample_session.session_id] = sample_session
        
        # Set up interruption condition
        sample_session.updated_at = datetime.now() - timedelta(minutes=35)
        
        session_manager.detect_flow_interruption(sample_session.session_id)
        
        # Verify warning was logged
        mock_logger.warning.assert_called()
        warning_call = mock_logger.warning.call_args[0][0]
        assert "Flow interruption detected" in warning_call

    @patch('src.mcps.deep_thinking.sessions.session_manager.logger')
    def test_rollback_logging(self, mock_logger, session_manager, sample_session):
        """Test that rollback operations are properly logged"""
        session_manager._active_sessions[sample_session.session_id] = sample_session
        
        sample_session.step_results = {
            "decompose_problem": {"result": "Step 1"},
            "collect_evidence": {"result": "Step 2"}
        }
        
        session_manager.rollback_to_step(sample_session.session_id, "decompose_problem")
        
        # Verify success logging
        mock_logger.info.assert_called()
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Successfully rolled back session" in call for call in info_calls)

    @patch('src.mcps.deep_thinking.sessions.session_manager.logger')
    def test_checkpoint_logging(self, mock_logger, session_manager, sample_session):
        """Test that checkpoint operations are properly logged"""
        session_manager._active_sessions[sample_session.session_id] = sample_session
        
        session_manager.create_recovery_checkpoint(sample_session.session_id)
        
        # Verify success logging
        mock_logger.info.assert_called()
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Created recovery checkpoint" in call for call in info_calls)