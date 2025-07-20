"""
Unit tests for the analyze_step MCP tool
"""

from unittest.mock import Mock

import pytest

from src.mcps.deep_thinking.flows.flow_manager import FlowManager
from src.mcps.deep_thinking.models.mcp_models import (
    AnalyzeStepInput,
    MCPToolName,
    MCPToolOutput,
    SessionState,
)
from src.mcps.deep_thinking.sessions.session_manager import SessionManager
from src.mcps.deep_thinking.templates.template_manager import TemplateManager
from src.mcps.deep_thinking.tools.mcp_tools import MCPTools


class TestAnalyzeStepTool:
    """Test cases for analyze_step MCP tool"""

    @pytest.fixture
    def mock_session_manager(self):
        """Mock session manager"""
        manager = Mock(spec=SessionManager)
        return manager

    @pytest.fixture
    def mock_template_manager(self):
        """Mock template manager"""
        manager = Mock(spec=TemplateManager)
        return manager

    @pytest.fixture
    def mock_flow_manager(self):
        """Mock flow manager"""
        manager = Mock(spec=FlowManager)
        return manager

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
        """Sample session state"""
        return SessionState(
            session_id="test-session-123",
            topic="如何提高教育质量？",
            current_step="decompose_problem",
            flow_type="comprehensive_analysis",
            context={
                "complexity": "moderate",
                "focus": "教育改革",
                "domain_context": "教育领域分析",
            },
            step_results={
                "decompose_problem": {
                    "result": '{"main_question": "如何提高教育质量？", "sub_questions": [...]}',
                    "quality_score": 8.5,
                }
            },
            quality_scores={"decompose_problem": 8.5},
        )

    def test_analyze_step_decomposition_success(
        self, mcp_tools, mock_session_manager, mock_template_manager, sample_session
    ):
        """Test successful analysis of decomposition step"""
        # Setup
        input_data = AnalyzeStepInput(
            session_id="test-session-123",
            step_name="decompose_problem",
            step_result='{"main_question": "如何提高教育质量？", "sub_questions": [{"id": "1", "question": "当前教育体系存在哪些问题？", "priority": "high", "search_keywords": ["教育问题"]}], "relationships": []}',
            analysis_type="quality",
        )

        mock_session_manager.get_session.return_value = sample_session
        mock_template_manager.get_template.return_value = (
            "# 步骤质量分析：问题分解\n请分析以下问题分解结果..."
        )

        # Execute
        result = mcp_tools.analyze_step(input_data)

        # Verify
        assert isinstance(result, MCPToolOutput)
        assert result.tool_name == MCPToolName.ANALYZE_STEP
        assert result.session_id == "test-session-123"
        assert result.step == "analyze_decompose_problem"
        assert "问题分解" in result.prompt_template
        assert result.context["analyzed_step"] == "decompose_problem"
        assert result.context["format_validated"] is True
        assert result.metadata["quality_check"] is True
        assert result.metadata["format_validation_passed"] is True

        # Verify template was called with correct parameters
        mock_template_manager.get_template.assert_called_once()
        template_call = mock_template_manager.get_template.call_args
        assert template_call[0][0] == "analyze_decomposition"
        template_params = template_call[0][1]
        assert "step_result" in template_params
        assert "original_topic" in template_params
        assert template_params["original_topic"] == "如何提高教育质量？"

    def test_analyze_step_evidence_collection(
        self, mcp_tools, mock_session_manager, mock_template_manager, sample_session
    ):
        """Test analysis of evidence collection step"""
        # Setup
        input_data = AnalyzeStepInput(
            session_id="test-session-123",
            step_name="collect_evidence",
            step_result="证据来源1：教育部报告\n来源：http://example.com\n可信度：8/10\n关键发现：教育质量需要系统性改进，师资力量是关键因素，需要加强教师培训和提高教师待遇。同时，教育资源分配不均也是重要问题，需要政策支持来缩小城乡教育差距。",
            analysis_type="quality",
        )

        sample_session.current_step = "collect_evidence"
        mock_session_manager.get_session.return_value = sample_session
        mock_template_manager.get_template.return_value = (
            "# 步骤质量分析：证据收集\n请分析以下证据收集结果..."
        )

        # Execute
        result = mcp_tools.analyze_step(input_data)

        # Verify
        assert result.step == "analyze_collect_evidence"
        assert result.context["analyzed_step"] == "collect_evidence"

        # Verify correct template was used
        template_call = mock_template_manager.get_template.call_args
        assert template_call[0][0] == "analyze_evidence"

    def test_analyze_step_debate_analysis(
        self, mcp_tools, mock_session_manager, mock_template_manager, sample_session
    ):
        """Test analysis of multi-perspective debate step"""
        # Setup
        input_data = AnalyzeStepInput(
            session_id="test-session-123",
            step_name="multi_perspective_debate",
            step_result="支持方观点：教育改革势在必行，当前教育体系存在明显问题，需要系统性改革。论据：教育质量下降、学生负担过重、创新能力不足。\n反对方观点：改革需要谨慎推进，急进改革可能带来负面影响。论据：教育改革风险高、需要稳定过渡、现有体系有其合理性。\n中立分析：改革和稳定需要平衡，应该渐进式改革。",
            analysis_type="quality",
        )

        sample_session.current_step = "multi_perspective_debate"
        mock_session_manager.get_session.return_value = sample_session
        mock_template_manager.get_template.return_value = (
            "# 步骤质量分析：多角度辩论\n请分析以下辩论结果..."
        )

        # Execute
        result = mcp_tools.analyze_step(input_data)

        # Verify
        assert result.step == "analyze_multi_perspective_debate"
        template_call = mock_template_manager.get_template.call_args
        assert template_call[0][0] == "analyze_debate"

    def test_analyze_step_format_validation_failure(
        self, mcp_tools, mock_session_manager, mock_template_manager, sample_session
    ):
        """Test format validation failure handling"""
        # Setup - invalid JSON format for decomposition
        input_data = AnalyzeStepInput(
            session_id="test-session-123",
            step_name="decompose_problem",
            step_result="这不是JSON格式的结果",
            analysis_type="quality",
        )

        mock_session_manager.get_session.return_value = sample_session
        mock_template_manager.get_template.return_value = (
            "# 格式验证失败\n步骤结果的格式不符合要求..."
        )

        # Execute
        result = mcp_tools.analyze_step(input_data)

        # Verify format validation failure handling
        assert result.step == "format_validation_decompose_problem"
        assert result.context["format_validation_failed"] is True
        assert result.metadata["format_validation"] is False
        assert "格式验证失败" in result.prompt_template

        # Verify format validation template was used
        template_call = mock_template_manager.get_template.call_args
        assert template_call[0][0] == "format_validation_failed"

    def test_analyze_step_session_not_found(
        self, mcp_tools, mock_session_manager, mock_template_manager
    ):
        """Test handling of session not found error"""
        # Setup
        input_data = AnalyzeStepInput(
            session_id="nonexistent-session",
            step_name="decompose_problem",
            step_result="some result",
            analysis_type="quality",
        )

        mock_session_manager.get_session.return_value = None
        mock_template_manager.get_template.return_value = (
            "# 会话恢复\n抱歉，之前的思考会话似乎中断了..."
        )

        # Execute
        result = mcp_tools.analyze_step(input_data)

        # Verify session recovery handling
        assert result.step == "session_recovery"
        assert result.context["error"] == "session_not_found"
        assert result.metadata["error_recovery"] is True

    def test_analyze_step_quality_threshold_calculation(
        self, mcp_tools, mock_session_manager, mock_template_manager, sample_session
    ):
        """Test quality threshold calculation for different steps and flow types"""
        # Setup
        input_data = AnalyzeStepInput(
            session_id="test-session-123",
            step_name="critical_evaluation",
            step_result="评估结果：准确性评分8/10，逻辑性评分7/10，相关性评分9/10。总体分析质量良好，建议在逻辑推理方面进一步加强。改进建议：增加更多证据支撑，完善论证结构。",
            analysis_type="quality",
        )

        mock_session_manager.get_session.return_value = sample_session
        mock_template_manager.get_template.return_value = "分析模板"

        # Execute
        result = mcp_tools.analyze_step(input_data)

        # Verify quality threshold is set correctly
        assert (
            result.context["quality_threshold"] == 8.0
        )  # critical_evaluation threshold

        # Test with quick_analysis flow type
        sample_session.flow_type = "quick_analysis"
        result = mcp_tools.analyze_step(input_data)
        assert (
            result.context["quality_threshold"] == 7.5
        )  # reduced threshold for quick analysis

    def test_analyze_step_improvement_suggestions_generation(
        self, mcp_tools, mock_session_manager, mock_template_manager, sample_session
    ):
        """Test improvement suggestions generation"""
        # Setup - short evidence collection result
        input_data = AnalyzeStepInput(
            session_id="test-session-123",
            step_name="collect_evidence",
            step_result="证据来源：教育部报告。可信度：8/10。简短的证据内容，缺少详细分析和多个来源。",  # Should trigger improvement suggestions
            analysis_type="quality",
        )

        mock_session_manager.get_session.return_value = sample_session
        mock_template_manager.get_template.return_value = (
            "分析模板 {improvement_suggestions}"
        )

        # Execute
        result = mcp_tools.analyze_step(input_data)

        # Verify improvement suggestions were generated (if not format validation failure)
        if result.step.startswith("analyze_"):
            assert result.context["improvement_suggestions_available"] is True

            # Check that template was called with improvement suggestions
            template_call = mock_template_manager.get_template.call_args
            template_params = template_call[0][1]
            assert "improvement_suggestions" in template_params
            assert (
                "应包含具体的网络来源链接" in template_params["improvement_suggestions"]
            )
        else:
            # Format validation failed, check that it was handled properly
            assert result.step.startswith("format_validation_")
            assert result.context["format_validation_failed"] is True

    def test_analyze_step_different_analysis_types(
        self, mcp_tools, mock_session_manager, mock_template_manager, sample_session
    ):
        """Test different analysis types"""
        # Test quality analysis
        input_data = AnalyzeStepInput(
            session_id="test-session-123",
            step_name="decompose_problem",
            step_result='{"main_question": "test", "sub_questions": [], "relationships": []}',
            analysis_type="quality",
        )

        mock_session_manager.get_session.return_value = sample_session
        mock_template_manager.get_template.return_value = "质量分析模板"

        result = mcp_tools.analyze_step(input_data)
        if result.step.startswith("analyze_"):
            assert result.context["analysis_type"] == "quality"

        # Test format analysis
        input_data.analysis_type = "format"
        result = mcp_tools.analyze_step(input_data)
        if result.step.startswith("analyze_"):
            assert result.context["analysis_type"] == "format"

    def test_analyze_step_metadata_completeness(
        self, mcp_tools, mock_session_manager, mock_template_manager, sample_session
    ):
        """Test that all required metadata is included"""
        # Setup
        input_data = AnalyzeStepInput(
            session_id="test-session-123",
            step_name="reflection",
            step_result="深度反思结果：通过这次思考过程，我学到了系统性分析问题的重要性。反思我的思维过程，发现在证据收集阶段还可以更加全面。洞察：多角度思考能够避免单一视角的局限性。改进方向：需要加强批判性思维能力。",
            analysis_type="quality",
        )

        mock_session_manager.get_session.return_value = sample_session
        mock_template_manager.get_template.return_value = "反思分析模板"

        # Execute
        result = mcp_tools.analyze_step(input_data)

        # Verify all required metadata fields
        required_metadata = [
            "quality_check",
            "step_analyzed",
            "analysis_template",
            "quality_threshold",
            "format_validation_passed",
            "analysis_criteria_count",
            "improvement_suggestions_generated",
        ]

        for field in required_metadata:
            assert field in result.metadata, f"Missing metadata field: {field}"

        assert result.metadata["quality_check"] is True
        assert result.metadata["step_analyzed"] == "reflection"
        assert result.metadata["analysis_template"] == "analyze_reflection"
        assert result.metadata["analysis_criteria_count"] == 5

    def test_analyze_step_error_handling(
        self, mcp_tools, mock_session_manager, mock_template_manager
    ):
        """Test error handling in analyze_step"""
        # Setup - simulate session manager error
        input_data = AnalyzeStepInput(
            session_id="test-session-123",
            step_name="decompose_problem",
            step_result="test result",
            analysis_type="quality",
        )

        mock_session_manager.get_session.side_effect = Exception("Database error")
        mock_template_manager.get_template.return_value = "错误恢复模板"

        # Execute
        result = mcp_tools.analyze_step(input_data)

        # Verify error handling
        assert result.step == "error_recovery"
        assert result.context["error"] is True
        assert result.context["failed_tool"] == "analyze_step"
        assert result.metadata["error_recovery"] is True
        assert result.metadata["original_tool"] == "analyze_step"


class TestAnalyzeStepFormatValidation:
    """Test format validation functionality"""

    @pytest.fixture
    def mcp_tools(self):
        """Create MCPTools instance for format validation tests"""
        session_manager = Mock(spec=SessionManager)
        template_manager = Mock(spec=TemplateManager)
        flow_manager = Mock(spec=FlowManager)
        return MCPTools(session_manager, template_manager, flow_manager)

    def test_validate_decomposition_format_valid(self, mcp_tools):
        """Test valid decomposition format validation"""
        valid_result = """
        {
            "main_question": "如何提高教育质量？",
            "sub_questions": [
                {
                    "id": "1",
                    "question": "当前教育体系存在哪些问题？",
                    "priority": "high",
                    "search_keywords": ["教育问题", "教育体系"]
                }
            ],
            "relationships": ["问题1是问题2的前提"]
        }
        """

        validation = mcp_tools._validate_decomposition_format(valid_result)
        assert validation["valid"] is True
        assert len(validation["issues"]) == 0

    def test_validate_decomposition_format_invalid(self, mcp_tools):
        """Test invalid decomposition format validation"""
        invalid_result = "这不是JSON格式"

        validation = mcp_tools._validate_decomposition_format(invalid_result)
        assert validation["valid"] is False
        assert "结果应为JSON格式" in validation["issues"]
        assert "缺少必需字段: main_question" in validation["issues"]

    def test_validate_evidence_format_valid(self, mcp_tools):
        """Test valid evidence format validation"""
        valid_result = """
        证据来源1：
        - 标题：教育质量研究报告
        - 来源：https://example.com/report
        - 可信度：8/10
        - 关键发现：教育质量需要系统性改进
        
        证据来源2：
        - 标题：专家访谈
        - 来源：https://example.com/interview
        - 可信度：9/10
        - 关键发现：师资力量是关键因素
        """

        validation = mcp_tools._validate_evidence_format(valid_result)
        assert validation["valid"] is True
        assert len(validation["issues"]) == 0

    def test_validate_evidence_format_invalid(self, mcp_tools):
        """Test invalid evidence format validation"""
        invalid_result = "简短证据"

        validation = mcp_tools._validate_evidence_format(invalid_result)
        assert validation["valid"] is False
        assert "应包含证据来源信息" in validation["issues"]
        assert "应包含可信度评估" in validation["issues"]
        assert any("证据收集结果过于简短" in issue for issue in validation["issues"])

    def test_validate_debate_format_valid(self, mcp_tools):
        """Test valid debate format validation"""
        valid_result = """
        支持方观点：
        - 核心论点：教育改革势在必行
        - 论据：当前教育体系存在明显问题
        
        反对方观点：
        - 核心论点：改革需要谨慎推进
        - 论据：急进改革可能带来负面影响
        
        中立分析：
        - 平衡观点：改革和稳定需要平衡
        """

        validation = mcp_tools._validate_debate_format(valid_result)
        assert validation["valid"] is True
        assert len(validation["issues"]) == 0

    def test_validate_debate_format_invalid(self, mcp_tools):
        """Test invalid debate format validation"""
        invalid_result = "单一观点，没有辩论"

        validation = mcp_tools._validate_debate_format(invalid_result)
        assert validation["valid"] is False
        assert "应包含多个不同角度的观点" in validation["issues"]
        assert "应包含具体的论据和推理" in validation["issues"]


class TestAnalyzeStepQualityGates:
    """Test quality gate functionality"""

    @pytest.fixture
    def mcp_tools(self):
        """Create MCPTools instance for quality gate tests"""
        session_manager = Mock(spec=SessionManager)
        template_manager = Mock(spec=TemplateManager)
        flow_manager = Mock(spec=FlowManager)
        return MCPTools(session_manager, template_manager, flow_manager)

    def test_quality_threshold_by_step_type(self, mcp_tools):
        """Test quality thresholds for different step types"""
        # Test different step types
        assert (
            mcp_tools._get_quality_threshold(
                "decompose_problem", "comprehensive_analysis"
            )
            == 7.0
        )
        assert (
            mcp_tools._get_quality_threshold(
                "collect_evidence", "comprehensive_analysis"
            )
            == 7.5
        )
        assert (
            mcp_tools._get_quality_threshold(
                "critical_evaluation", "comprehensive_analysis"
            )
            == 8.0
        )
        assert (
            mcp_tools._get_quality_threshold("reflection", "comprehensive_analysis")
            == 7.0
        )

    def test_quality_threshold_by_flow_type(self, mcp_tools):
        """Test quality thresholds for different flow types"""
        # Test flow type adjustments
        assert (
            mcp_tools._get_quality_threshold("decompose_problem", "quick_analysis")
            == 6.5
        )
        assert (
            mcp_tools._get_quality_threshold("critical_evaluation", "quick_analysis")
            == 7.5
        )

    def test_improvement_suggestions_generation(self, mcp_tools):
        """Test improvement suggestions for different scenarios"""
        context = {"complexity": "moderate"}

        # Test decomposition suggestions
        short_decomp = "简短分解"
        suggestions = mcp_tools._generate_improvement_suggestions(
            "decompose_problem", short_decomp, context
        )
        assert "问题分解应更加详细" in suggestions
        assert "应为每个子问题设定优先级" in suggestions

        # Test evidence collection suggestions
        short_evidence = "简短证据"
        suggestions = mcp_tools._generate_improvement_suggestions(
            "collect_evidence", short_evidence, context
        )
        assert "应包含具体的网络来源链接" in suggestions
        assert "应收集更多不同来源的证据" in suggestions

        # Test reflection suggestions
        short_reflection = "简短反思"
        suggestions = mcp_tools._generate_improvement_suggestions(
            "reflection", short_reflection, context
        )
        assert "反思应更加深入和详细" in suggestions


if __name__ == "__main__":
    pytest.main([__file__])
