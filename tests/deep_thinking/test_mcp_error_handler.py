"""
Unit tests for MCP Error Handler
Tests comprehensive error handling for MCP tools
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from src.mcps.deep_thinking.config.exceptions import (
    MCPFormatValidationError,
    MCPQualityGateError,
    MCPSessionRecoveryError,
    MCPToolError,
    MCPToolExecutionError,
    SessionNotFoundError,
    SessionStateError,
    TemplateError,
)
from src.mcps.deep_thinking.models.mcp_models import MCPToolName, MCPToolOutput
from src.mcps.deep_thinking.sessions.session_manager import SessionManager
from src.mcps.deep_thinking.templates.template_manager import TemplateManager
from src.mcps.deep_thinking.tools.mcp_error_handler import MCPErrorHandler


class TestMCPErrorHandler:
    """Test suite for MCP Error Handler"""

    @pytest.fixture
    def mock_session_manager(self):
        """Create mock session manager"""
        return Mock(spec=SessionManager)

    @pytest.fixture
    def mock_template_manager(self):
        """Create mock template manager"""
        return Mock(spec=TemplateManager)

    @pytest.fixture
    def error_handler(self, mock_session_manager, mock_template_manager):
        """Create error handler instance"""
        return MCPErrorHandler(mock_session_manager, mock_template_manager)

    def test_error_handler_initialization(self, error_handler):
        """Test error handler initializes correctly"""
        assert error_handler.session_manager is not None
        assert error_handler.template_manager is not None
        assert error_handler.error_recovery_templates is not None
        assert len(error_handler.error_recovery_templates) > 0

    def test_classify_error_session_not_found(self, error_handler):
        """Test error classification for session not found"""
        error = SessionNotFoundError("Session not found", session_id="test-123")
        error_type = error_handler._classify_error(error)
        assert error_type == "session_not_found"

    def test_classify_error_session_state(self, error_handler):
        """Test error classification for session state error"""
        error = SessionStateError("Invalid session state", session_id="test-123")
        error_type = error_handler._classify_error(error)
        assert error_type == "session_state_error"

    def test_classify_error_template_missing(self, error_handler):
        """Test error classification for template error"""
        error = TemplateError("Template not found", template_name="test_template")
        error_type = error_handler._classify_error(error)
        assert error_type == "template_missing"

    def test_classify_error_format_validation(self, error_handler):
        """Test error classification for format validation"""
        error = Exception("Format validation failed")
        error_type = error_handler._classify_error(error)
        assert error_type == "invalid_step_result"

    def test_classify_error_quality_gate(self, error_handler):
        """Test error classification for quality gate failure"""
        error = Exception("Quality gate failed")
        error_type = error_handler._classify_error(error)
        assert error_type == "quality_gate_failed"

    def test_classify_error_flow_interrupted(self, error_handler):
        """Test error classification for flow interruption"""
        error = Exception("Flow interrupted")
        error_type = error_handler._classify_error(error)
        assert error_type == "flow_interrupted"

    def test_classify_error_session_timeout(self, error_handler):
        """Test error classification for session timeout"""
        error = Exception("Session timeout occurred")
        error_type = error_handler._classify_error(error)
        assert error_type == "session_timeout"

    def test_classify_error_generic(self, error_handler):
        """Test error classification for generic error"""
        error = Exception("Some random error")
        error_type = error_handler._classify_error(error)
        assert error_type == "generic_error"

    def test_handle_session_not_found_error(self, error_handler):
        """Test handling session not found error"""
        session_id = "test-session-123"
        error = SessionNotFoundError("Session not found", session_id=session_id)
        
        result = error_handler.handle_mcp_error(
            tool_name="test_tool",
            error=error,
            session_id=session_id,
            context={}
        )
        
        assert isinstance(result, MCPToolOutput)
        assert result.session_id == session_id
        assert result.step == "session_recovery"
        assert result.tool_name == MCPToolName.START_THINKING
        assert "会话恢复" in result.prompt_template
        assert result.context["error_type"] == "session_not_found"
        assert result.context["recovery_mode"] is True
        assert result.metadata["error_recovery"] is True

    def test_handle_format_validation_error(self, error_handler):
        """Test handling format validation error"""
        session_id = "test-session-123"
        step_name = "decompose_problem"
        error = MCPFormatValidationError(
            "Format validation failed",
            step_name=step_name,
            expected_format="JSON format"
        )
        
        context = {
            "step_name": step_name,
            "format_issues": ["Missing JSON format", "Invalid structure"],
            "expected_format": "JSON format with required fields"
        }
        
        result = error_handler.handle_mcp_error(
            tool_name="format_validator",
            error=error,
            session_id=session_id,
            context=context
        )
        
        assert isinstance(result, MCPToolOutput)
        assert result.session_id == session_id
        assert result.step == f"fix_format_{step_name}"
        assert result.tool_name == MCPToolName.NEXT_STEP
        assert "格式修正指导" in result.prompt_template
        assert result.context["error_type"] == "format_validation_failed"
        assert result.context["step_name"] == step_name
        assert result.metadata["format_correction_required"] is True

    def test_handle_template_missing_error(self, error_handler):
        """Test handling template missing error"""
        session_id = "test-session-123"
        template_name = "missing_template"
        step_name = "test_step"
        error = TemplateError("Template not found", template_name=template_name)
        
        context = {
            "template_name": template_name,
            "step_name": step_name
        }
        
        result = error_handler.handle_mcp_error(
            tool_name="template_manager",
            error=error,
            session_id=session_id,
            context=context
        )
        
        assert isinstance(result, MCPToolOutput)
        assert result.session_id == session_id
        assert result.step == f"generic_{step_name}"
        assert result.tool_name == MCPToolName.NEXT_STEP
        assert "模板缺失处理" in result.prompt_template
        assert result.context["error_type"] == "template_missing"
        assert result.context["using_generic_template"] is True
        assert result.metadata["fallback_template_used"] is True

    def test_handle_flow_interruption_error(self, error_handler):
        """Test handling flow interruption error"""
        session_id = "test-session-123"
        current_step = "evidence_collection"
        completed_steps = ["decompose_problem", "collect_evidence"]
        
        context = {
            "current_step": current_step,
            "completed_steps": completed_steps,
            "quality_status": "good"
        }
        
        error = Exception("Flow interrupted")
        
        result = error_handler.handle_mcp_error(
            tool_name="flow_manager",
            error=error,
            session_id=session_id,
            context=context
        )
        
        assert isinstance(result, MCPToolOutput)
        assert result.session_id == session_id
        assert result.step == "flow_recovery"
        assert result.tool_name == MCPToolName.NEXT_STEP
        assert "流程恢复" in result.prompt_template
        assert result.context["error_type"] == "flow_interrupted"
        assert result.context["current_step"] == current_step
        assert result.context["completed_steps"] == completed_steps
        assert result.metadata["flow_state_preserved"] is True

    def test_handle_quality_gate_failure(self, error_handler):
        """Test handling quality gate failure"""
        session_id = "test-session-123"
        step_name = "critical_evaluation"
        quality_score = 5.5
        quality_threshold = 7.0
        quality_issues = ["Insufficient depth", "Weak evidence"]
        
        context = {
            "step_name": step_name,
            "quality_score": quality_score,
            "quality_threshold": quality_threshold,
            "quality_issues": quality_issues
        }
        
        error = MCPQualityGateError(
            "Quality gate failed",
            step_name=step_name,
            quality_score=quality_score,
            quality_threshold=quality_threshold
        )
        
        result = error_handler.handle_mcp_error(
            tool_name="quality_gate",
            error=error,
            session_id=session_id,
            context=context
        )
        
        assert isinstance(result, MCPToolOutput)
        assert result.session_id == session_id
        assert result.step == f"improve_{step_name}"
        assert result.tool_name == MCPToolName.ANALYZE_STEP
        assert "质量改进指导" in result.prompt_template
        assert result.context["error_type"] == "quality_gate_failed"
        assert result.context["quality_score"] == quality_score
        assert result.context["quality_threshold"] == quality_threshold
        assert result.metadata["quality_improvement_required"] is True

    def test_handle_session_timeout_error(self, error_handler):
        """Test handling session timeout error"""
        session_id = "test-session-123"
        timeout_duration = "30 minutes"
        last_activity = "2024-01-01 10:00:00"
        
        context = {
            "timeout_duration": timeout_duration,
            "last_activity": last_activity
        }
        
        error = Exception("Session timeout occurred")
        
        result = error_handler.handle_mcp_error(
            tool_name="session_manager",
            error=error,
            session_id=session_id,
            context=context
        )
        
        assert isinstance(result, MCPToolOutput)
        assert result.session_id == session_id
        assert result.step == "timeout_recovery"
        assert result.tool_name == MCPToolName.START_THINKING
        assert "会话超时恢复" in result.prompt_template
        assert result.context["error_type"] == "session_timeout"
        assert result.context["timeout_duration"] == timeout_duration
        assert result.metadata["timeout_recovery_available"] is True

    def test_handle_generic_error(self, error_handler):
        """Test handling generic error"""
        session_id = "test-session-123"
        tool_name = "test_tool"
        error = Exception("Some unexpected error")
        
        result = error_handler.handle_mcp_error(
            tool_name=tool_name,
            error=error,
            session_id=session_id,
            context={}
        )
        
        assert isinstance(result, MCPToolOutput)
        assert result.session_id == session_id
        assert result.step == "error_recovery"
        assert result.tool_name == MCPToolName.NEXT_STEP
        assert "系统错误恢复" in result.prompt_template
        assert result.context["error_type"] == "generic_error"
        assert result.context["original_tool"] == tool_name
        assert result.metadata["fallback_recovery"] is True

    def test_fallback_response_when_handler_fails(self, error_handler):
        """Test fallback response when error handler itself fails"""
        session_id = "test-session-123"
        tool_name = "test_tool"
        error = Exception("Original error")
        
        # Mock the error handler to raise an exception
        with patch.object(error_handler, '_classify_error', side_effect=Exception("Handler failed")):
            result = error_handler.handle_mcp_error(
                tool_name=tool_name,
                error=error,
                session_id=session_id,
                context={}
            )
            
            assert isinstance(result, MCPToolOutput)
            assert result.session_id == session_id
            assert result.step == "emergency_recovery"
            assert result.tool_name == MCPToolName.START_THINKING
            assert "系统恢复模式" in result.prompt_template
            assert result.context["recovery_mode"] == "emergency"
            assert result.metadata["emergency_mode"] is True
            assert result.metadata["handler_failed"] is True

    def test_recover_session_state_success(self, error_handler, mock_session_manager):
        """Test successful session state recovery"""
        session_id = "test-session-123"
        recovery_data = {
            "topic": "Test topic",
            "current_step": "evidence_collection",
            "completed_steps": ["decompose_problem"],
            "context": {"complexity": "moderate"}
        }
        
        mock_session_manager.recover_session.return_value = True
        
        result = error_handler.recover_session_state(session_id, recovery_data)
        
        assert result is True
        mock_session_manager.recover_session.assert_called_once_with(session_id, recovery_data)

    def test_recover_session_state_failure(self, error_handler, mock_session_manager):
        """Test failed session state recovery"""
        session_id = "test-session-123"
        recovery_data = {
            "topic": "Test topic",
            "current_step": "evidence_collection"
        }
        
        mock_session_manager.recover_session.return_value = False
        
        result = error_handler.recover_session_state(session_id, recovery_data)
        
        assert result is False
        mock_session_manager.recover_session.assert_called_once_with(session_id, recovery_data)

    def test_recover_session_state_invalid_data(self, error_handler):
        """Test session recovery with invalid data"""
        session_id = "test-session-123"
        recovery_data = {}  # Missing required fields
        
        result = error_handler.recover_session_state(session_id, recovery_data)
        
        assert result is False

    def test_recover_session_state_exception(self, error_handler, mock_session_manager):
        """Test session recovery with exception"""
        session_id = "test-session-123"
        recovery_data = {
            "topic": "Test topic",
            "current_step": "evidence_collection"
        }
        
        mock_session_manager.recover_session.side_effect = Exception("Recovery failed")
        
        result = error_handler.recover_session_state(session_id, recovery_data)
        
        assert result is False

    def test_format_improvement_suggestions(self, error_handler):
        """Test format improvement suggestions generation"""
        suggestions = error_handler._generate_format_improvement_suggestions("decompose_problem")
        assert "JSON格式" in suggestions
        assert "main_question" in suggestions
        
        suggestions = error_handler._generate_format_improvement_suggestions("collect_evidence")
        assert "证据来源" in suggestions
        assert "可信度评估" in suggestions
        
        suggestions = error_handler._generate_format_improvement_suggestions("unknown_step")
        assert "请参考步骤要求" in suggestions

    def test_format_hints(self, error_handler):
        """Test format hints generation"""
        hint = error_handler._get_format_hint("decompose_problem")
        assert "JSON格式" in hint
        
        hint = error_handler._get_format_hint("collect_evidence")
        assert "结构化列出证据" in hint
        
        hint = error_handler._get_format_hint("unknown_step")
        assert "参考文档" in hint

    def test_progress_summary_generation(self, error_handler):
        """Test progress summary generation"""
        completed_steps = ["decompose_problem", "collect_evidence", "multi_perspective_debate"]
        summary = error_handler._generate_progress_summary(completed_steps)
        
        assert "问题分解" in summary
        assert "证据收集" in summary
        assert "多角度辩论" in summary
        
        # Test empty steps
        summary = error_handler._generate_progress_summary([])
        assert "尚未完成任何步骤" in summary

    def test_next_step_recommendations(self, error_handler):
        """Test next step recommendations"""
        recommendation = error_handler._get_next_step_recommendation("decompose_problem")
        assert "证据收集" in recommendation
        
        recommendation = error_handler._get_next_step_recommendation("collect_evidence")
        assert "多角度辩论" in recommendation
        
        recommendation = error_handler._get_next_step_recommendation("reflection")
        assert "最终报告" in recommendation
        
        recommendation = error_handler._get_next_step_recommendation("unknown_step")
        assert "继续下一步" in recommendation

    def test_improvement_suggestions_generation(self, error_handler):
        """Test improvement suggestions for different aspects"""
        depth_suggestions = error_handler._get_depth_improvement_suggestions("decompose_problem")
        assert "深入分析" in depth_suggestions
        
        logic_suggestions = error_handler._get_logic_improvement_suggestions("any_step")
        assert "推理过程清晰" in logic_suggestions
        
        evidence_suggestions = error_handler._get_evidence_improvement_suggestions("any_step")
        assert "补充更多可靠证据" in evidence_suggestions
        
        breadth_suggestions = error_handler._get_breadth_improvement_suggestions("any_step")
        assert "考虑更多角度" in breadth_suggestions

    @patch('src.mcps.deep_thinking.tools.mcp_error_handler.logger')
    def test_error_logging(self, mock_logger, error_handler):
        """Test that errors are properly logged"""
        session_id = "test-session-123"
        error = Exception("Test error")
        
        error_handler.handle_mcp_error(
            tool_name="test_tool",
            error=error,
            session_id=session_id,
            context={}
        )
        
        # Verify error was logged
        mock_logger.error.assert_called()
        call_args = mock_logger.error.call_args[0][0]
        assert "MCP tool error" in call_args
        assert "test_tool" in call_args

    def test_error_recovery_templates_completeness(self, error_handler):
        """Test that all required error recovery templates are present"""
        required_templates = [
            "session_not_found",
            "invalid_step_result", 
            "template_missing",
            "flow_interrupted",
            "quality_gate_failed",
            "session_timeout"
        ]
        
        for template_name in required_templates:
            assert template_name in error_handler.error_recovery_templates
            template_content = error_handler.error_recovery_templates[template_name]
            assert len(template_content) > 0
            assert "{" in template_content  # Should have template parameters

    def test_error_context_preservation(self, error_handler):
        """Test that error context is preserved in recovery responses"""
        session_id = "test-session-123"
        original_context = {
            "step_name": "test_step",
            "custom_data": "important_info",
            "user_preference": "detailed_analysis"
        }
        
        error = Exception("Test error")
        
        result = error_handler.handle_mcp_error(
            tool_name="test_tool",
            error=error,
            session_id=session_id,
            context=original_context
        )
        
        # Verify context is preserved and enhanced
        assert result.context["original_tool"] == "test_tool"
        assert result.context["recovery_mode"] is True
        assert "recovery_options" in result.context