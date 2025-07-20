"""
Unit tests for the complete_thinking MCP tool
"""

from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from src.mcps.deep_thinking.flows.flow_manager import FlowManager
from src.mcps.deep_thinking.models.mcp_models import (
    CompleteThinkingInput,
    MCPToolName,
    MCPToolOutput,
    SessionState,
)
from src.mcps.deep_thinking.sessions.session_manager import SessionManager
from src.mcps.deep_thinking.templates.template_manager import TemplateManager
from src.mcps.deep_thinking.tools.mcp_tools import MCPTools


class TestCompleteThinkingTool:
    """Test cases for the complete_thinking MCP tool"""

    @pytest.fixture
    def mock_session_manager(self):
        """Mock session manager"""
        mock = Mock(spec=SessionManager)
        return mock

    @pytest.fixture
    def mock_template_manager(self):
        """Mock template manager"""
        mock = Mock(spec=TemplateManager)
        return mock

    @pytest.fixture
    def mock_flow_manager(self):
        """Mock flow manager"""
        mock = Mock(spec=FlowManager)
        return mock

    @pytest.fixture
    def mcp_tools(self, mock_session_manager, mock_template_manager, mock_flow_manager):
        """Create MCPTools instance with mocked dependencies"""
        return MCPTools(
            session_manager=mock_session_manager,
            template_manager=mock_template_manager,
            flow_manager=mock_flow_manager,
        )

    @pytest.fixture
    def sample_session(self):
        """Create a sample session state"""
        created_time = datetime.now() - timedelta(minutes=30)
        updated_time = datetime.now()

        return SessionState(
            session_id="test-session-123",
            topic="如何提高教育质量？",
            current_step="reflection",
            step_number=5,
            flow_type="comprehensive_analysis",
            status="active",
            step_results={
                "decompose_problem": "问题已分解为5个子问题",
                "collect_evidence": "收集了10个证据来源",
                "multi_perspective_debate": "进行了三方辩论",
                "critical_evaluation": "完成了Paul-Elder评估",
                "reflection": "完成了苏格拉底式反思",
            },
            context={
                "complexity": "moderate",
                "focus": "教育改革",
                "domain_context": "教育政策分析",
            },
            quality_scores={
                "decompose_problem": 8.5,
                "collect_evidence": 7.8,
                "multi_perspective_debate": 9.2,
                "critical_evaluation": 8.0,
                "reflection": 8.7,
            },
            created_at=created_time,
            updated_at=updated_time,
        )

    @pytest.fixture
    def sample_thinking_trace(self):
        """Create a sample thinking trace"""
        return {
            "session_id": "test-session-123",
            "topic": "如何提高教育质量？",
            "flow_type": "comprehensive_analysis",
            "status": "active",
            "steps": [
                {
                    "step_name": "decompose_problem",
                    "step_type": "analysis",
                    "quality_score": 8.5,
                    "execution_time_ms": 1500,
                    "results": [],
                    "timestamp": "2024-01-01T10:00:00",
                },
                {
                    "step_name": "collect_evidence",
                    "step_type": "research",
                    "quality_score": 7.8,
                    "execution_time_ms": 2000,
                    "results": [],
                    "timestamp": "2024-01-01T10:05:00",
                },
            ],
            "quality_summary": {"decompose_problem": 8.5, "collect_evidence": 7.8},
            "total_duration": 1800,
        }

    def test_complete_thinking_success(
        self,
        mcp_tools,
        mock_session_manager,
        mock_template_manager,
        sample_session,
        sample_thinking_trace,
    ):
        """Test successful completion of thinking process"""
        # Setup mocks
        mock_session_manager.get_session.return_value = sample_session
        mock_session_manager.get_full_trace.return_value = sample_thinking_trace
        mock_session_manager.complete_session.return_value = True
        mock_template_manager.get_template.return_value = (
            "Comprehensive summary template"
        )

        # Create input
        input_data = CompleteThinkingInput(
            session_id="test-session-123", final_insights="教育质量提升需要系统性改革"
        )

        # Execute
        result = mcp_tools.complete_thinking(input_data)

        # Verify result structure
        assert isinstance(result, MCPToolOutput)
        assert result.tool_name == MCPToolName.COMPLETE_THINKING
        assert result.session_id == "test-session-123"
        assert result.step == "generate_final_report"
        assert result.prompt_template == "Comprehensive summary template"
        assert "生成详细的综合报告" in result.instructions

        # Verify context
        assert result.context["session_completed"] is True
        assert result.context["total_steps"] == 5
        assert "quality_metrics" in result.context
        assert "session_summary" in result.context
        assert result.context["thinking_trace_available"] is True

        # Verify metadata
        assert result.metadata["session_status"] == "completed"
        assert "completion_timestamp" in result.metadata
        assert "quality_summary" in result.metadata
        assert result.metadata["report_generation_ready"] is True

        # Verify session manager calls
        mock_session_manager.get_session.assert_called_once_with("test-session-123")
        mock_session_manager.get_full_trace.assert_called_once_with("test-session-123")
        mock_session_manager.complete_session.assert_called_once()

        # Verify template manager call
        mock_template_manager.get_template.assert_called_once()
        call_args = mock_template_manager.get_template.call_args
        assert (
            call_args[0][0] == "comprehensive_summary"
        )  # First argument should be template name

    def test_complete_thinking_with_final_insights(
        self,
        mcp_tools,
        mock_session_manager,
        mock_template_manager,
        sample_session,
        sample_thinking_trace,
    ):
        """Test completion with final insights provided"""
        # Setup mocks
        mock_session_manager.get_session.return_value = sample_session
        mock_session_manager.get_full_trace.return_value = sample_thinking_trace
        mock_session_manager.complete_session.return_value = True
        mock_template_manager.get_template.return_value = "Template with insights"

        # Create input with final insights
        final_insights = (
            "关键洞察：教育质量的提升需要技术、制度、文化三个层面的协同改革"
        )
        input_data = CompleteThinkingInput(
            session_id="test-session-123", final_insights=final_insights
        )

        # Execute
        result = mcp_tools.complete_thinking(input_data)

        # Verify final insights are included
        assert result.context["final_results"]["final_insights"] == final_insights

        # Verify template parameters include final insights
        template_call_args = mock_template_manager.get_template.call_args
        template_params = template_call_args[0][1]
        assert template_params["final_insights"] == final_insights

    def test_complete_thinking_session_not_found(
        self, mcp_tools, mock_session_manager, mock_template_manager
    ):
        """Test completion when session is not found"""
        # Setup mock to return None (session not found)
        mock_session_manager.get_session.return_value = None
        mock_template_manager.get_template.return_value = "Session recovery template"

        # Create input
        input_data = CompleteThinkingInput(session_id="nonexistent-session")

        # Execute
        result = mcp_tools.complete_thinking(input_data)

        # Verify error handling
        assert result.step == "session_recovery"
        assert result.context["error"] == "session_not_found"
        assert "会话已丢失" in result.instructions

    def test_complete_thinking_session_completion_failure(
        self,
        mcp_tools,
        mock_session_manager,
        mock_template_manager,
        sample_session,
        sample_thinking_trace,
    ):
        """Test handling of session completion failure"""
        # Setup mocks
        mock_session_manager.get_session.return_value = sample_session
        mock_session_manager.get_full_trace.return_value = sample_thinking_trace
        mock_session_manager.complete_session.return_value = False  # Completion fails
        mock_template_manager.get_template.return_value = "Template despite failure"

        # Create input
        input_data = CompleteThinkingInput(session_id="test-session-123")

        # Execute
        result = mcp_tools.complete_thinking(input_data)

        # Verify that report generation continues despite completion failure
        assert result.tool_name == MCPToolName.COMPLETE_THINKING
        assert result.context["completion_success"] is False
        assert "completion_warning" in result.context["final_results"]

    def test_quality_metrics_calculation(self, mcp_tools, sample_session):
        """Test comprehensive quality metrics calculation"""
        # Execute quality metrics calculation
        quality_metrics = mcp_tools._calculate_comprehensive_quality_metrics(
            sample_session
        )

        # Verify basic metrics
        assert quality_metrics["average_quality"] == 8.44  # (8.5+7.8+9.2+8.0+8.7)/5
        assert quality_metrics["total_steps"] == 5
        assert quality_metrics["high_quality_steps"] == 4  # scores >= 8.0

        # Verify quality distribution
        distribution = quality_metrics["quality_distribution"]
        assert distribution["excellent"] == 1  # score >= 9.0 (9.2)
        assert distribution["good"] == 4  # 7.0 <= score < 9.0
        assert distribution["acceptable"] == 0
        assert distribution["needs_improvement"] == 0

        # Verify overall assessment
        assert (
            quality_metrics["overall_assessment"] == "good"
        )  # avg 8.44 is >= 7.0 but < 8.5

        # Verify best and worst performing steps
        best_step, best_score = quality_metrics["best_performing_step"]
        assert best_step == "multi_perspective_debate"
        assert best_score == 9.2

        lowest_step, lowest_score = quality_metrics["lowest_performing_step"]
        assert lowest_step == "collect_evidence"
        assert lowest_score == 7.8

    def test_quality_metrics_no_data(self, mcp_tools):
        """Test quality metrics calculation with no quality data"""
        # Create session without quality scores
        session = SessionState(
            session_id="test-session",
            topic="Test topic",
            current_step="test",
            flow_type="test_flow",
            quality_scores={},  # No quality data
        )

        # Execute
        quality_metrics = mcp_tools._calculate_comprehensive_quality_metrics(session)

        # Verify handling of no data
        assert quality_metrics["average_quality"] == 0.0
        assert quality_metrics["quality_trend"] == "no_data"
        assert quality_metrics["overall_assessment"] == "insufficient_data"
        assert "No quality data available" in quality_metrics["improvement_areas"]

    def test_quality_trend_analysis(self, mcp_tools):
        """Test quality trend analysis"""
        # Test improving trend
        improving_scores = [6.0, 7.0, 8.0, 9.0]
        trend = mcp_tools._analyze_quality_trend(improving_scores)
        assert trend == "improving"

        # Test declining trend
        declining_scores = [9.0, 8.0, 7.0, 6.0]
        trend = mcp_tools._analyze_quality_trend(declining_scores)
        assert trend == "declining"

        # Test stable trend
        stable_scores = [7.5, 7.8, 7.6, 7.7]
        trend = mcp_tools._analyze_quality_trend(stable_scores)
        assert trend == "stable"

        # Test insufficient data
        single_score = [8.0]
        trend = mcp_tools._analyze_quality_trend(single_score)
        assert trend == "insufficient_data"

    def test_session_summary_generation(
        self, mcp_tools, mock_session_manager, sample_session
    ):
        """Test detailed session summary generation"""
        # Mock database responses
        mock_steps = [
            {
                "id": 1,
                "step_name": "decompose_problem",
                "step_type": "analysis",
                "quality_score": 8.5,
                "execution_time_ms": 1500,
                "created_at": "2024-01-01T10:00:00",
            },
            {
                "id": 2,
                "step_name": "collect_evidence",
                "step_type": "research",
                "quality_score": 7.8,
                "execution_time_ms": 2000,
                "created_at": "2024-01-01T10:05:00",
            },
        ]

        mock_results = [
            {"step_id": 1, "content": "Result 1"},
            {"step_id": 1, "content": "Result 2"},
            {"step_id": 2, "content": "Result 3"},
        ]

        # Create a mock database object
        mock_db = Mock()
        mock_db.get_session_steps.return_value = mock_steps
        mock_db.get_step_results.return_value = mock_results
        mock_session_manager.db = mock_db

        # Execute
        session_summary = mcp_tools._generate_detailed_session_summary(sample_session)

        # Verify summary structure
        assert session_summary["session_id"] == "test-session-123"
        assert session_summary["topic"] == "如何提高教育质量？"
        assert session_summary["flow_type"] == "comprehensive_analysis"
        assert session_summary["total_steps"] == 2
        assert session_summary["completion_status"] == "completed"

        # Verify detailed steps
        detailed_steps = session_summary["detailed_steps"]
        assert len(detailed_steps) == 2
        assert detailed_steps[0]["step_name"] == "decompose_problem"
        assert detailed_steps[0]["quality_score"] == 8.5
        assert detailed_steps[0]["results_count"] == 2
        assert detailed_steps[1]["step_name"] == "collect_evidence"
        assert detailed_steps[1]["results_count"] == 1

    def test_template_parameter_building(
        self, mcp_tools, sample_session, sample_thinking_trace
    ):
        """Test comprehensive template parameter building"""
        # Create quality metrics
        quality_metrics = {
            "average_quality": 8.44,
            "overall_assessment": "excellent",
            "improvement_areas": ["无需改进"],
            "best_performing_step": ("multi_perspective_debate", 9.2),
        }

        # Create session summary
        session_summary = {
            "session_duration": 30.0,
            "total_steps": 5,
            "detailed_steps": [],
        }

        # Execute
        params = mcp_tools._build_comprehensive_summary_params(
            sample_session,
            quality_metrics,
            session_summary,
            sample_thinking_trace,
            "Final insights",
        )

        # Verify key parameters
        assert params["topic"] == "如何提高教育质量？"
        assert params["flow_type"] == "comprehensive_analysis"
        assert params["session_duration"] == "30.0 分钟"
        assert params["total_steps"] == 5
        assert params["overall_assessment"] == "excellent"
        assert params["average_quality"] == 8.44
        assert params["final_insights"] == "Final insights"
        assert params["best_step"] == "multi_perspective_debate"
        assert "completion_timestamp" in params

    def test_completion_instructions_generation(self, mcp_tools, sample_session):
        """Test generation of completion instructions based on quality"""
        # Test excellent quality
        excellent_metrics = {"overall_assessment": "excellent"}
        instructions = mcp_tools._generate_completion_instructions(
            excellent_metrics, sample_session
        )
        assert "质量优秀" in instructions
        assert "核心洞察和创新观点" in instructions

        # Test good quality
        good_metrics = {"overall_assessment": "good"}
        instructions = mcp_tools._generate_completion_instructions(
            good_metrics, sample_session
        )
        assert "质量良好" in instructions

        # Test needs improvement
        poor_metrics = {
            "overall_assessment": "needs_improvement",
            "improvement_areas": ["decompose_problem", "collect_evidence"],
        }
        instructions = mcp_tools._generate_completion_instructions(
            poor_metrics, sample_session
        )
        assert "质量需要改进" in instructions
        assert "decompose_problem" in instructions

    def test_error_handling(
        self, mcp_tools, mock_session_manager, mock_template_manager
    ):
        """Test error handling in complete_thinking"""
        # Setup mock to raise exception
        mock_session_manager.get_session.side_effect = Exception("Database error")
        mock_template_manager.get_template.return_value = "Error recovery template"

        # Create input
        input_data = CompleteThinkingInput(session_id="test-session")

        # Execute
        result = mcp_tools.complete_thinking(input_data)

        # Verify error handling
        assert result.step == "error_recovery"
        assert result.context["error"] is True
        assert result.context["failed_tool"] == "complete_thinking"
        assert "Database error" in result.context["error_message"]

    @pytest.mark.parametrize(
        "quality_scores,expected_assessment",
        [
            ({"step1": 9.5, "step2": 9.0}, "excellent"),
            ({"step1": 8.0, "step2": 7.5}, "good"),
            ({"step1": 6.0, "step2": 5.5}, "acceptable"),
            ({"step1": 4.0, "step2": 3.5}, "needs_improvement"),
        ],
    )
    def test_overall_assessment_determination(
        self, mcp_tools, quality_scores, expected_assessment
    ):
        """Test overall assessment determination for different quality levels"""
        # Create session with specific quality scores
        session = SessionState(
            session_id="test",
            topic="Test",
            current_step="test",
            flow_type="test",
            quality_scores=quality_scores,
        )

        # Calculate metrics
        metrics = mcp_tools._calculate_comprehensive_quality_metrics(session)

        # Verify assessment
        assert metrics["overall_assessment"] == expected_assessment

    def test_quality_consistency_calculation(self, mcp_tools):
        """Test quality consistency calculation"""
        # Test high consistency (low variance)
        consistent_scores = [8.0, 8.1, 7.9, 8.0, 8.1]
        consistency = mcp_tools._calculate_quality_consistency(consistent_scores)
        assert consistency > 0.9  # High consistency

        # Test low consistency (high variance)
        inconsistent_scores = [3.0, 9.0, 5.0, 8.0, 2.0]
        consistency = mcp_tools._calculate_quality_consistency(inconsistent_scores)
        assert consistency < 0.5  # Low consistency

        # Test single score
        single_score = [8.0]
        consistency = mcp_tools._calculate_quality_consistency(single_score)
        assert consistency == 1.0  # Perfect consistency for single score
