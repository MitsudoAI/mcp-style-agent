"""
Integration test for analyze_step tool
"""

import pytest
from src.mcps.deep_thinking.tools.mcp_tools import MCPTools
from src.mcps.deep_thinking.models.mcp_models import (
    StartThinkingInput, NextStepInput, AnalyzeStepInput, MCPToolName
)
from src.mcps.deep_thinking.sessions.session_manager import SessionManager
from src.mcps.deep_thinking.templates.template_manager import TemplateManager
from src.mcps.deep_thinking.flows.flow_manager import FlowManager
from src.mcps.deep_thinking.data.database import ThinkingDatabase


class TestAnalyzeStepIntegration:
    """Integration tests for analyze_step tool with real components"""
    
    @pytest.fixture
    def session_manager(self):
        """Create session manager with in-memory database"""
        return SessionManager(":memory:")
    
    @pytest.fixture
    def template_manager(self):
        """Create template manager"""
        return TemplateManager()
    
    @pytest.fixture
    def flow_manager(self):
        """Create flow manager"""
        return FlowManager()
    
    @pytest.fixture
    def mcp_tools(self, session_manager, template_manager, flow_manager):
        """Create MCPTools with real components"""
        return MCPTools(session_manager, template_manager, flow_manager)
    
    def test_full_analyze_step_workflow(self, mcp_tools):
        """Test complete analyze_step workflow from start to analysis"""
        
        # Step 1: Start thinking session
        start_input = StartThinkingInput(
            topic="如何提高团队协作效率？",
            complexity="moderate",
            focus="团队管理"
        )
        
        start_result = mcp_tools.start_thinking(start_input)
        assert start_result.tool_name == MCPToolName.START_THINKING
        session_id = start_result.session_id
        
        # Step 2: Complete decomposition step
        decomposition_result = '''
        {
            "main_question": "如何提高团队协作效率？",
            "sub_questions": [
                {
                    "id": "1",
                    "question": "当前团队协作中存在哪些主要障碍？",
                    "priority": "high",
                    "search_keywords": ["团队协作", "沟通障碍", "协作工具"],
                    "expected_perspectives": ["管理者视角", "员工视角", "技术视角"]
                },
                {
                    "id": "2", 
                    "question": "有哪些有效的协作工具和方法？",
                    "priority": "high",
                    "search_keywords": ["协作工具", "项目管理", "沟通方法"],
                    "expected_perspectives": ["技术解决方案", "流程优化", "文化建设"]
                }
            ],
            "relationships": ["问题1的解决是问题2实施的前提"]
        }
        '''
        
        next_input = NextStepInput(
            session_id=session_id,
            step_result=decomposition_result
        )
        
        next_result = mcp_tools.next_step(next_input)
        assert next_result.tool_name == MCPToolName.NEXT_STEP
        
        # Step 3: Analyze the decomposition step
        analyze_input = AnalyzeStepInput(
            session_id=session_id,
            step_name="decompose_problem",
            step_result=decomposition_result,
            analysis_type="quality"
        )
        
        analyze_result = mcp_tools.analyze_step(analyze_input)
        
        # Debug: Print the result to see what's happening
        print(f"Analyze result tool_name: {analyze_result.tool_name}")
        print(f"Analyze result step: {analyze_result.step}")
        print(f"Analyze result context: {analyze_result.context}")
        
        # Verify analysis result
        assert analyze_result.tool_name == MCPToolName.ANALYZE_STEP
        assert analyze_result.session_id == session_id
        assert analyze_result.step == "analyze_decompose_problem"
        assert "问题分解" in analyze_result.prompt_template
        assert "完整性" in analyze_result.prompt_template
        assert "独立性" in analyze_result.prompt_template
        assert "可操作性" in analyze_result.prompt_template
        
        # Verify context contains analysis information
        assert analyze_result.context["analyzed_step"] == "decompose_problem"
        assert analyze_result.context["analysis_type"] == "quality"
        assert analyze_result.context["format_validated"] is True
        assert analyze_result.context["quality_threshold"] == 7.0
        
        # Verify metadata
        assert analyze_result.metadata["quality_check"] is True
        assert analyze_result.metadata["step_analyzed"] == "decompose_problem"
        assert analyze_result.metadata["analysis_template"] == "analyze_decomposition"
        assert analyze_result.metadata["format_validation_passed"] is True
        assert analyze_result.metadata["analysis_criteria_count"] == 5
    
    def test_analyze_step_format_validation_integration(self, mcp_tools):
        """Test format validation in real integration scenario"""
        
        # Start a session
        start_input = StartThinkingInput(topic="测试问题")
        start_result = mcp_tools.start_thinking(start_input)
        session_id = start_result.session_id
        
        # Try to analyze with invalid format
        invalid_decomposition = "这不是JSON格式的分解结果"
        
        analyze_input = AnalyzeStepInput(
            session_id=session_id,
            step_name="decompose_problem",
            step_result=invalid_decomposition,
            analysis_type="quality"
        )
        
        analyze_result = mcp_tools.analyze_step(analyze_input)
        
        # Verify format validation failure handling
        assert analyze_result.step == "format_validation_decompose_problem"
        assert analyze_result.context["format_validation_failed"] is True
        assert "格式验证失败" in analyze_result.prompt_template
        assert analyze_result.metadata["format_validation"] is False
        assert analyze_result.metadata["validation_issues_count"] > 0
    
    def test_analyze_step_different_step_types(self, mcp_tools):
        """Test analyzing different types of steps"""
        
        # Start session
        start_input = StartThinkingInput(topic="教育改革分析")
        start_result = mcp_tools.start_thinking(start_input)
        session_id = start_result.session_id
        
        # Test evidence collection analysis
        evidence_result = """
        证据来源1：
        - 标题：教育部2024年教育统计报告
        - 来源：http://www.moe.gov.cn/report2024
        - 可信度：9/10
        - 关键发现：全国教育质量整体提升，但地区差异仍然显著
        
        证据来源2：
        - 标题：北京师范大学教育研究
        - 来源：http://www.bnu.edu.cn/research
        - 可信度：8/10
        - 关键发现：师资力量是影响教育质量的关键因素
        """
        
        analyze_input = AnalyzeStepInput(
            session_id=session_id,
            step_name="collect_evidence",
            step_result=evidence_result,
            analysis_type="quality"
        )
        
        analyze_result = mcp_tools.analyze_step(analyze_input)
        
        # Verify evidence analysis
        assert analyze_result.step == "analyze_collect_evidence"
        assert "证据收集" in analyze_result.prompt_template
        assert "来源多样性" in analyze_result.prompt_template
        assert "可信度评估" in analyze_result.prompt_template
        assert analyze_result.metadata["analysis_template"] == "analyze_evidence"
    
    def test_analyze_step_quality_threshold_enforcement(self, mcp_tools):
        """Test quality threshold enforcement for different flow types"""
        
        # Test comprehensive analysis (higher threshold)
        start_input = StartThinkingInput(
            topic="复杂战略决策",
            flow_type="comprehensive_analysis"
        )
        start_result = mcp_tools.start_thinking(start_input)
        session_id = start_result.session_id
        
        analyze_input = AnalyzeStepInput(
            session_id=session_id,
            step_name="critical_evaluation",
            step_result="评估结果：准确性8分，逻辑性7分，相关性9分。总体质量良好。",
            analysis_type="quality"
        )
        
        analyze_result = mcp_tools.analyze_step(analyze_input)
        
        # Verify higher threshold for comprehensive analysis
        assert analyze_result.context["quality_threshold"] == 8.0
        
        # Test quick analysis (lower threshold)
        start_input_quick = StartThinkingInput(
            topic="简单问题分析",
            flow_type="quick_analysis"
        )
        start_result_quick = mcp_tools.start_thinking(start_input_quick)
        session_id_quick = start_result_quick.session_id
        
        analyze_input_quick = AnalyzeStepInput(
            session_id=session_id_quick,
            step_name="critical_evaluation",
            step_result="评估结果：准确性8分，逻辑性7分，相关性9分。总体质量良好。",
            analysis_type="quality"
        )
        
        analyze_result_quick = mcp_tools.analyze_step(analyze_input_quick)
        
        # Verify lower threshold for quick analysis
        assert analyze_result_quick.context["quality_threshold"] == 7.5
    
    def test_analyze_step_improvement_suggestions(self, mcp_tools):
        """Test improvement suggestions generation"""
        
        start_input = StartThinkingInput(topic="产品创新策略")
        start_result = mcp_tools.start_thinking(start_input)
        session_id = start_result.session_id
        
        # Provide a reflection result that should trigger improvement suggestions
        short_reflection = "简单的反思：学到了一些东西。"
        
        analyze_input = AnalyzeStepInput(
            session_id=session_id,
            step_name="reflection",
            step_result=short_reflection,
            analysis_type="quality"
        )
        
        analyze_result = mcp_tools.analyze_step(analyze_input)
        
        # Verify improvement suggestions are included
        assert analyze_result.context["improvement_suggestions_available"] is True
        
        # The template should contain improvement suggestions
        assert "improvement_suggestions" in analyze_result.prompt_template


if __name__ == "__main__":
    pytest.main([__file__])