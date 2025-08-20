"""
Integration tests for MCP Tools with Error Handling
Tests the integration between MCP tools and error handling system
"""

import pytest
from unittest.mock import Mock, patch

from src.mcps.deep_thinking.config.exceptions import (
    MCPFormatValidationError,
    SessionNotFoundError,
    TemplateError,
)
from src.mcps.deep_thinking.flows.flow_manager import FlowManager
from src.mcps.deep_thinking.models.mcp_models import (
    AnalyzeStepInput,
    CompleteThinkingInput,
    MCPToolName,
    NextStepInput,
    StartThinkingInput,
)
from src.mcps.deep_thinking.sessions.session_manager import SessionManager
from src.mcps.deep_thinking.templates.template_manager import TemplateManager
from src.mcps.deep_thinking.tools.mcp_tools import MCPTools


class TestMCPToolsErrorIntegration:
    """Test suite for MCP tools error handling integration"""

    @pytest.fixture
    def mock_session_manager(self):
        """Create mock session manager"""
        return Mock(spec=SessionManager)

    @pytest.fixture
    def mock_template_manager(self):
        """Create mock template manager"""
        return Mock(spec=TemplateManager)

    @pytest.fixture
    def mock_flow_manager(self):
        """Create mock flow manager"""
        return Mock(spec=FlowManager)

    @pytest.fixture
    def mcp_tools(self, mock_session_manager, mock_template_manager, mock_flow_manager):
        """Create MCP tools instance with mocked dependencies"""
        return MCPTools(mock_session_manager, mock_template_manager, mock_flow_manager)

    def test_start_thinking_error_handling(self, mcp_tools, mock_session_manager):
        """Test start_thinking tool error handling"""
        input_data = StartThinkingInput(
            topic="Test topic", complexity="moderate", focus="test focus"
        )

        # Mock session manager to raise exception
        mock_session_manager.create_session.side_effect = Exception(
            "Database connection failed"
        )

        result = mcp_tools.start_thinking(input_data)

        # Should return error recovery response
        assert result.tool_name == MCPToolName.NEXT_STEP
        assert result.step == "error_recovery"
        assert "系统错误恢复" in result.prompt_template
        assert result.context["error_type"] == "generic_error"
        assert result.metadata["error_recovery"] is True

    def test_next_step_session_not_found_error(self, mcp_tools, mock_session_manager):
        """Test next_step tool with session not found error"""
        input_data = NextStepInput(
            session_id="nonexistent-session", step_result="Some result"
        )

        # Mock session manager to raise SessionNotFoundError
        mock_session_manager.get_session.side_effect = SessionNotFoundError(
            "Session not found", session_id="nonexistent-session"
        )

        result = mcp_tools.next_step(input_data)

        # Should return session recovery response
        assert result.tool_name == MCPToolName.START_THINKING
        assert result.step == "session_recovery"
        assert "会话恢复" in result.prompt_template
        assert result.context["error_type"] == "session_not_found"
        assert result.metadata["error_recovery"] is True

    def test_next_step_template_error_handling(
        self, mcp_tools, mock_session_manager, mock_template_manager
    ):
        """Test next_step tool with template error"""
        from src.mcps.deep_thinking.models.mcp_models import SessionState

        input_data = NextStepInput(session_id="test-session", step_result="Some result")

        # Mock session exists
        mock_session = SessionState(
            session_id="test-session",
            topic="Test topic",
            current_step="decompose_problem",
            flow_type="comprehensive_analysis",
        )
        mock_session_manager.get_session.return_value = mock_session
        mock_session_manager.add_step_result.return_value = True
        mock_session_manager.update_session_step.return_value = True

        # Mock template manager to raise TemplateError
        mock_template_manager.get_template.side_effect = TemplateError(
            "Template not found", template_name="missing_template"
        )

        result = mcp_tools.next_step(input_data)

        # Should return error recovery response
        assert result.tool_name == MCPToolName.NEXT_STEP
        assert result.step == "error_recovery"
        assert "系统错误恢复" in result.prompt_template
        assert result.context["error_type"] == "generic_error"
        assert result.metadata["error_recovery"] is True

    def test_analyze_step_session_not_found(self, mcp_tools, mock_session_manager):
        """Test analyze_step tool with session not found"""
        input_data = AnalyzeStepInput(
            session_id="nonexistent-session",
            step_name="decompose_problem",
            step_result="Some result",
        )

        # Mock session not found
        mock_session_manager.get_session.return_value = None

        result = mcp_tools.analyze_step(input_data)

        # Should return session recovery response
        assert result.tool_name == MCPToolName.START_THINKING
        assert result.step == "session_recovery"
        assert "会话恢复" in result.prompt_template
        assert result.context["error_type"] == "session_not_found"

    def test_analyze_step_format_validation_failure(
        self, mcp_tools, mock_session_manager
    ):
        """Test analyze_step tool with format validation failure"""
        from src.mcps.deep_thinking.models.mcp_models import SessionState

        input_data = AnalyzeStepInput(
            session_id="test-session",
            step_name="decompose_problem",
            step_result="Invalid format result",
        )

        # Mock session exists
        mock_session = SessionState(
            session_id="test-session",
            topic="Test topic",
            current_step="decompose_problem",
            flow_type="comprehensive_analysis",
        )
        mock_session_manager.get_session.return_value = mock_session

        # Mock format validation to fail
        with patch.object(mcp_tools, "_validate_step_format") as mock_validate:
            mock_validate.return_value = {
                "valid": False,
                "issues": ["Missing JSON format", "Invalid structure"],
                "expected_format": "JSON format with required fields",
                "format_requirements": "Must include main_question and sub_questions",
            }

            result = mcp_tools.analyze_step(input_data)

            # Should return format validation error recovery
            assert result.tool_name == MCPToolName.NEXT_STEP
            assert result.step == "fix_format_decompose_problem"
            assert "格式修正指导" in result.prompt_template
            assert result.context["error_type"] == "format_validation_failed"
            assert result.metadata["format_correction_required"] is True

    def test_complete_thinking_session_not_found(self, mcp_tools, mock_session_manager):
        """Test complete_thinking tool with session not found"""
        input_data = CompleteThinkingInput(
            session_id="nonexistent-session", final_insights="Some insights"
        )

        # Mock session not found
        mock_session_manager.get_session.return_value = None

        result = mcp_tools.complete_thinking(input_data)

        # Should return session recovery response
        assert result.tool_name == MCPToolName.START_THINKING
        assert result.step == "session_recovery"
        assert "会话恢复" in result.prompt_template
        assert result.context["error_type"] == "session_not_found"

    def test_complete_thinking_database_error(
        self, mcp_tools, mock_session_manager, mock_template_manager
    ):
        """Test complete_thinking tool with database error"""
        from src.mcps.deep_thinking.models.mcp_models import SessionState

        input_data = CompleteThinkingInput(
            session_id="test-session", final_insights="Some insights"
        )

        # Mock session exists
        mock_session = SessionState(
            session_id="test-session",
            topic="Test topic",
            current_step="reflection",
            flow_type="comprehensive_analysis",
        )
        mock_session_manager.get_session.return_value = mock_session

        # Mock database error during completion
        mock_session_manager.complete_session.side_effect = Exception("Database error")

        result = mcp_tools.complete_thinking(input_data)

        # Should return error recovery response
        assert result.tool_name == MCPToolName.NEXT_STEP
        assert result.step == "error_recovery"
        assert "系统错误恢复" in result.prompt_template
        assert result.context["error_type"] == "generic_error"

    def test_error_handler_initialization_in_mcp_tools(self, mcp_tools):
        """Test that error handler is properly initialized in MCP tools"""
        assert hasattr(mcp_tools, "error_handler")
        assert mcp_tools.error_handler is not None
        assert mcp_tools.error_handler.session_manager == mcp_tools.session_manager
        assert mcp_tools.error_handler.template_manager == mcp_tools.template_manager

    def test_error_context_propagation(self, mcp_tools, mock_session_manager):
        """Test that error context is properly propagated through error handling"""
        input_data = StartThinkingInput(
            topic="Complex analysis topic",
            complexity="complex",
            focus="detailed analysis",
        )

        # Mock session manager to raise exception
        mock_session_manager.create_session.side_effect = Exception(
            "Specific error message"
        )

        result = mcp_tools.start_thinking(input_data)

        # Verify error context is preserved
        assert result.context["error_type"] == "generic_error"
        assert result.context["original_tool"] == "start_thinking"
        assert "Complex analysis topic" in str(
            result.context
        )  # Topic should be in context

    def test_multiple_error_scenarios_in_sequence(
        self, mcp_tools, mock_session_manager, mock_template_manager
    ):
        """Test handling multiple error scenarios in sequence"""
        from src.mcps.deep_thinking.models.mcp_models import SessionState

        # First call - session not found
        input_data1 = NextStepInput(
            session_id="nonexistent-session", step_result="Some result"
        )
        mock_session_manager.get_session.return_value = None

        result1 = mcp_tools.next_step(input_data1)
        assert result1.context["error_type"] == "session_not_found"

        # Second call - template error
        input_data2 = NextStepInput(
            session_id="test-session", step_result="Some result"
        )
        mock_session = SessionState(
            session_id="test-session",
            topic="Test topic",
            current_step="decompose_problem",
            flow_type="comprehensive_analysis",
        )
        mock_session_manager.get_session.return_value = mock_session
        mock_session_manager.add_step_result.return_value = True
        mock_session_manager.update_session_step.return_value = True
        mock_template_manager.get_template.side_effect = TemplateError("Template error")

        result2 = mcp_tools.next_step(input_data2)
        assert result2.context["error_type"] == "generic_error"

        # Verify each error was handled independently
        assert result1.session_id != result2.session_id or result1.step != result2.step

    def test_error_recovery_with_session_recovery_functionality(
        self, mcp_tools, mock_session_manager
    ):
        """Test error recovery integrates with session recovery functionality"""
        session_id = "test-session-123"

        # Test session recovery through error handler
        recovery_data = {
            "topic": "Test topic",
            "current_step": "collect_evidence",
            "completed_steps": ["decompose_problem"],
        }

        # Mock successful recovery
        mock_session_manager.recover_session.return_value = True

        result = mcp_tools.error_handler.recover_session_state(
            session_id, recovery_data
        )

        assert result is True
        mock_session_manager.recover_session.assert_called_once_with(
            session_id, recovery_data
        )

    def test_error_logging_integration(self, mcp_tools, mock_session_manager):
        """Test that errors are properly logged through the integration"""
        input_data = StartThinkingInput(topic="Test topic", complexity="moderate")

        # Mock session manager to raise exception
        mock_session_manager.create_session.side_effect = Exception(
            "Test error for logging"
        )

        with patch(
            "src.mcps.deep_thinking.tools.mcp_error_handler.logger"
        ) as mock_logger:
            result = mcp_tools.start_thinking(input_data)

            # Verify error was logged
            mock_logger.error.assert_called()
            log_call = mock_logger.error.call_args[0][0]
            assert "MCP tool error" in log_call
            assert "start_thinking" in log_call

    def test_error_recovery_preserves_original_intent(
        self, mcp_tools, mock_session_manager
    ):
        """Test that error recovery preserves the original user intent"""
        input_data = NextStepInput(
            session_id="test-session",
            step_result="Detailed analysis result with specific insights",
        )

        # Mock session not found
        mock_session_manager.get_session.side_effect = SessionNotFoundError(
            "Session not found", session_id="test-session"
        )

        result = mcp_tools.next_step(input_data)

        # Verify recovery response maintains context about original intent
        assert result.context["original_session_id"] == "test-session"
        assert result.context["recovery_mode"] is True
        assert "recovery_options" in result.context

    def test_fallback_error_handling_when_error_handler_fails(
        self, mcp_tools, mock_session_manager
    ):
        """Test fallback behavior when error handler itself fails"""
        input_data = StartThinkingInput(topic="Test topic", complexity="moderate")

        # Mock session manager to raise exception
        mock_session_manager.create_session.side_effect = Exception("Original error")

        # Mock error handler to also fail
        with patch.object(
            mcp_tools.error_handler,
            "handle_mcp_error",
            side_effect=Exception("Handler failed"),
        ):
            result = mcp_tools.start_thinking(input_data)

            # Should still return a valid response (fallback)
            assert result.tool_name == MCPToolName.START_THINKING
            assert result.step == "emergency_recovery"
            assert "系统恢复模式" in result.prompt_template
            assert result.metadata["emergency_mode"] is True

    def test_error_recovery_response_format_consistency(
        self, mcp_tools, mock_session_manager
    ):
        """Test that all error recovery responses follow consistent format"""
        test_cases = [
            # Session not found
            (
                NextStepInput(session_id="missing", step_result="result"),
                SessionNotFoundError("Not found", session_id="missing"),
            ),
            # Generic error
            (
                StartThinkingInput(topic="test", complexity="moderate"),
                Exception("Generic error"),
            ),
        ]

        for input_data, error in test_cases:
            # Mock appropriate error
            if isinstance(error, SessionNotFoundError):
                mock_session_manager.get_session.side_effect = error
            else:
                mock_session_manager.create_session.side_effect = error

            # Map input class names to method names
            method_mapping = {
                "NextStepInput": "next_step",
                "StartThinkingInput": "start_thinking",
                "AnalyzeStepInput": "analyze_step",
                "CompleteThinkingInput": "complete_thinking",
            }
            method_name = method_mapping.get(input_data.__class__.__name__)
            if method_name:
                result = getattr(mcp_tools, method_name)(input_data)
            else:
                continue  # Skip unknown input types

            # Verify consistent response format
            assert hasattr(result, "tool_name")
            assert hasattr(result, "session_id")
            assert hasattr(result, "step")
            assert hasattr(result, "prompt_template")
            assert hasattr(result, "instructions")
            assert hasattr(result, "context")
            assert hasattr(result, "next_action")
            assert hasattr(result, "metadata")

            # Verify error recovery metadata
            assert result.metadata.get("error_recovery") is True
            assert "error_type" in result.context

            # Reset mocks for next iteration
            mock_session_manager.reset_mock()
            mock_session_manager.get_session.side_effect = None
            mock_session_manager.create_session.side_effect = None
