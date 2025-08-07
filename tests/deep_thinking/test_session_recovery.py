"""
Unit tests for Session Recovery functionality
Tests session recovery and state repair mechanisms
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from src.mcps.deep_thinking.config.exceptions import SessionNotFoundError
from src.mcps.deep_thinking.data.database import ThinkingDatabase
from src.mcps.deep_thinking.models.mcp_models import SessionState
from src.mcps.deep_thinking.sessions.session_manager import SessionManager


class TestSessionRecovery:
    """Test suite for session recovery functionality"""

    @pytest.fixture
    def mock_db(self):
        """Create mock database"""
        return Mock(spec=ThinkingDatabase)

    @pytest.fixture
    def session_manager(self, mock_db):
        """Create session manager with mock database"""
        with patch('src.mcps.deep_thinking.sessions.session_manager.ThinkingDatabase', return_value=mock_db):
            return SessionManager(db_path=":memory:")

    def test_recover_session_success(self, session_manager, mock_db):
        """Test successful session recovery"""
        session_id = "test-session-123"
        recovery_data = {
            "topic": "How to improve education quality?",
            "current_step": "collect_evidence",
            "completed_steps": ["decompose_problem"],
            "context": {
                "complexity": "moderate",
                "focus": "educational methods"
            },
            "flow_type": "comprehensive_analysis"
        }

        # Mock database operations
        mock_db.create_session.return_value = session_id
        mock_db.add_session_step.return_value = 1
        mock_db.add_step_result.return_value = True

        result = session_manager.recover_session(session_id, recovery_data)

        assert result is True
        
        # Verify database calls
        mock_db.create_session.assert_called_once()
        create_call_args = mock_db.create_session.call_args
        assert create_call_args[1]["topic"] == recovery_data["topic"]
        assert create_call_args[1]["session_type"] == recovery_data["flow_type"]
        assert create_call_args[1]["configuration"]["recovered"] is True

        # Verify step creation
        mock_db.add_session_step.assert_called_once()
        step_call_args = mock_db.add_session_step.call_args
        assert step_call_args[1]["step_name"] == "decompose_problem"
        assert step_call_args[1]["quality_score"] == 0.8

        # Verify recovery marker
        mock_db.add_step_result.assert_called_once()
        result_call_args = mock_db.add_step_result.call_args
        assert result_call_args[1]["result_type"] == "recovery"

    def test_recover_session_missing_topic(self, session_manager):
        """Test session recovery with missing topic"""
        session_id = "test-session-123"
        recovery_data = {
            "current_step": "collect_evidence",
            # Missing topic
        }

        result = session_manager.recover_session(session_id, recovery_data)

        assert result is False

    def test_recover_session_missing_current_step(self, session_manager):
        """Test session recovery with missing current step"""
        session_id = "test-session-123"
        recovery_data = {
            "topic": "Test topic",
            # Missing current_step
        }

        result = session_manager.recover_session(session_id, recovery_data)

        assert result is False

    def test_recover_session_database_failure(self, session_manager, mock_db):
        """Test session recovery when database creation fails"""
        session_id = "test-session-123"
        recovery_data = {
            "topic": "Test topic",
            "current_step": "collect_evidence"
        }

        # Mock database failure
        mock_db.create_session.return_value = None

        result = session_manager.recover_session(session_id, recovery_data)

        assert result is False

    def test_recover_session_with_multiple_completed_steps(self, session_manager, mock_db):
        """Test session recovery with multiple completed steps"""
        session_id = "test-session-123"
        recovery_data = {
            "topic": "Test topic",
            "current_step": "critical_evaluation",
            "completed_steps": [
                "decompose_problem",
                "collect_evidence", 
                "multi_perspective_debate"
            ],
            "context": {"complexity": "complex"}
        }

        # Mock database operations
        mock_db.create_session.return_value = session_id
        mock_db.add_session_step.return_value = 1
        mock_db.add_step_result.return_value = True

        result = session_manager.recover_session(session_id, recovery_data)

        assert result is True
        
        # Verify all steps were created
        assert mock_db.add_session_step.call_count == 3
        assert mock_db.add_step_result.call_count == 3

    def test_recover_session_exception_handling(self, session_manager, mock_db):
        """Test session recovery with exception"""
        session_id = "test-session-123"
        recovery_data = {
            "topic": "Test topic",
            "current_step": "collect_evidence"
        }

        # Mock database exception
        mock_db.create_session.side_effect = Exception("Database error")

        result = session_manager.recover_session(session_id, recovery_data)

        assert result is False

    def test_repair_session_state_success(self, session_manager, mock_db):
        """Test successful session state repair"""
        session_id = "test-session-123"
        
        # Create existing session
        existing_session = SessionState(
            session_id=session_id,
            topic="Original topic",
            current_step="decompose_problem",
            flow_type="comprehensive_analysis",
            context={"complexity": "simple"},
            status="active"
        )
        
        # Mock getting existing session
        session_manager._active_sessions[session_id] = existing_session
        
        repair_data = {
            "current_step": "collect_evidence",
            "context": {"complexity": "moderate", "focus": "new focus"},
            "step_results": {
                "decompose_problem": {
                    "result": "Fixed decomposition",
                    "quality_score": 0.9
                }
            }
        }

        # Mock database update
        mock_db.update_session.return_value = True

        result = session_manager.repair_session_state(session_id, repair_data)

        assert result is True
        
        # Verify session was updated
        updated_session = session_manager._active_sessions[session_id]
        assert updated_session.current_step == "collect_evidence"
        assert updated_session.context["complexity"] == "moderate"
        assert updated_session.context["focus"] == "new focus"
        assert "decompose_problem" in updated_session.step_results

        # Verify database update
        mock_db.update_session.assert_called_once()
        update_call_args = mock_db.update_session.call_args
        assert update_call_args[1]["configuration"]["repaired"] is True

    def test_repair_session_state_nonexistent_session(self, session_manager):
        """Test repairing non-existent session"""
        session_id = "nonexistent-session"
        repair_data = {
            "current_step": "collect_evidence"
        }

        result = session_manager.repair_session_state(session_id, repair_data)

        assert result is False

    def test_repair_session_state_database_failure(self, session_manager, mock_db):
        """Test session repair when database update fails"""
        session_id = "test-session-123"
        
        # Create existing session
        existing_session = SessionState(
            session_id=session_id,
            topic="Original topic",
            current_step="decompose_problem",
            flow_type="comprehensive_analysis",
            context={},
            status="active"
        )
        
        session_manager._active_sessions[session_id] = existing_session
        
        repair_data = {
            "current_step": "collect_evidence"
        }

        # Mock database failure
        mock_db.update_session.return_value = False

        result = session_manager.repair_session_state(session_id, repair_data)

        assert result is False

    def test_repair_session_state_exception_handling(self, session_manager, mock_db):
        """Test session repair with exception"""
        session_id = "test-session-123"
        
        # Create existing session
        existing_session = SessionState(
            session_id=session_id,
            topic="Original topic",
            current_step="decompose_problem",
            flow_type="comprehensive_analysis",
            context={},
            status="active"
        )
        
        session_manager._active_sessions[session_id] = existing_session
        
        repair_data = {
            "current_step": "collect_evidence"
        }

        # Mock database exception
        mock_db.update_session.side_effect = Exception("Database error")

        result = session_manager.repair_session_state(session_id, repair_data)

        assert result is False

    def test_recover_session_creates_proper_session_state(self, session_manager, mock_db):
        """Test that recovered session creates proper SessionState object"""
        session_id = "test-session-123"
        recovery_data = {
            "topic": "Test topic",
            "current_step": "collect_evidence",
            "completed_steps": ["decompose_problem"],
            "context": {"complexity": "moderate"},
            "flow_type": "quick_analysis"
        }

        # Mock database operations
        mock_db.create_session.return_value = session_id
        mock_db.add_session_step.return_value = 1
        mock_db.add_step_result.return_value = True

        result = session_manager.recover_session(session_id, recovery_data)

        assert result is True
        
        # Verify session is cached
        assert session_id in session_manager._active_sessions
        recovered_session = session_manager._active_sessions[session_id]
        
        assert recovered_session.topic == recovery_data["topic"]
        assert recovered_session.current_step == recovery_data["current_step"]
        assert recovered_session.flow_type == recovery_data["flow_type"]
        assert recovered_session.context == recovery_data["context"]
        assert recovered_session.step_number == 1  # One completed step
        assert "decompose_problem" in recovered_session.step_results

    def test_recover_session_with_different_database_id(self, session_manager, mock_db):
        """Test session recovery when database generates different ID"""
        original_session_id = "test-session-123"
        database_session_id = "db-generated-456"
        
        recovery_data = {
            "topic": "Test topic",
            "current_step": "collect_evidence"
        }

        # Mock database returning different ID
        mock_db.create_session.return_value = database_session_id
        mock_db.add_session_step.return_value = 1
        mock_db.add_step_result.return_value = True

        result = session_manager.recover_session(original_session_id, recovery_data)

        assert result is True
        
        # Verify session is cached with database ID
        assert database_session_id in session_manager._active_sessions
        assert original_session_id not in session_manager._active_sessions

    def test_recover_session_step_creation_failure(self, session_manager, mock_db):
        """Test session recovery when step creation fails"""
        session_id = "test-session-123"
        recovery_data = {
            "topic": "Test topic",
            "current_step": "collect_evidence",
            "completed_steps": ["decompose_problem"]
        }

        # Mock database operations - session creation succeeds, step creation fails
        mock_db.create_session.return_value = session_id
        mock_db.add_session_step.return_value = None  # Step creation fails

        result = session_manager.recover_session(session_id, recovery_data)

        # Should still succeed even if step creation fails
        assert result is True
        
        # Verify session is still cached
        assert session_id in session_manager._active_sessions

    def test_repair_session_partial_updates(self, session_manager, mock_db):
        """Test session repair with partial updates"""
        session_id = "test-session-123"
        
        # Create existing session
        existing_session = SessionState(
            session_id=session_id,
            topic="Original topic",
            current_step="decompose_problem",
            flow_type="comprehensive_analysis",
            context={"complexity": "simple", "existing_key": "existing_value"},
            status="active"
        )
        
        session_manager._active_sessions[session_id] = existing_session
        
        # Only update context, leave other fields unchanged
        repair_data = {
            "context": {"complexity": "moderate", "new_key": "new_value"}
        }

        # Mock database update
        mock_db.update_session.return_value = True

        result = session_manager.repair_session_state(session_id, repair_data)

        assert result is True
        
        # Verify partial updates
        updated_session = session_manager._active_sessions[session_id]
        assert updated_session.current_step == "decompose_problem"  # Unchanged
        assert updated_session.context["complexity"] == "moderate"  # Updated
        assert updated_session.context["new_key"] == "new_value"  # Added
        assert updated_session.context["existing_key"] == "existing_value"  # Preserved

    @patch('src.mcps.deep_thinking.sessions.session_manager.logger')
    def test_recovery_logging(self, mock_logger, session_manager, mock_db):
        """Test that recovery operations are properly logged"""
        session_id = "test-session-123"
        recovery_data = {
            "topic": "Test topic",
            "current_step": "collect_evidence"
        }

        # Mock successful recovery
        mock_db.create_session.return_value = session_id
        mock_db.add_session_step.return_value = 1
        mock_db.add_step_result.return_value = True

        session_manager.recover_session(session_id, recovery_data)

        # Verify success logging
        mock_logger.info.assert_called()
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Successfully recovered session" in call for call in info_calls)

    @patch('src.mcps.deep_thinking.sessions.session_manager.logger')
    def test_recovery_error_logging(self, mock_logger, session_manager, mock_db):
        """Test that recovery errors are properly logged"""
        session_id = "test-session-123"
        recovery_data = {
            "topic": "Test topic",
            "current_step": "collect_evidence"
        }

        # Mock database exception
        mock_db.create_session.side_effect = Exception("Database error")

        session_manager.recover_session(session_id, recovery_data)

        # Verify error logging
        mock_logger.error.assert_called()
        error_call = mock_logger.error.call_args[0][0]
        assert "Error recovering session" in error_call

    def test_determine_step_type_for_recovery(self, session_manager):
        """Test step type determination during recovery"""
        # This tests the _determine_step_type method indirectly
        session_id = "test-session-123"
        recovery_data = {
            "topic": "Test topic",
            "current_step": "collect_evidence",
            "completed_steps": ["decompose_problem", "collect_evidence", "multi_perspective_debate"]
        }

        # Mock database operations
        with patch.object(session_manager.db, 'create_session', return_value=session_id), \
             patch.object(session_manager.db, 'add_session_step', return_value=1) as mock_add_step, \
             patch.object(session_manager.db, 'add_step_result', return_value=True):
            
            result = session_manager.recover_session(session_id, recovery_data)
            
            assert result is True
            
            # Verify step types are determined correctly
            step_calls = mock_add_step.call_args_list
            assert len(step_calls) == 3
            
            # Each call should have step_type parameter
            for call in step_calls:
                assert 'step_type' in call[1]