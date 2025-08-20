"""
Tests for the Reflection Template
"""

import json
import pytest

from src.mcps.deep_thinking.templates.template_manager import TemplateManager


class TestReflectionTemplate:
    """Test the reflection template functionality"""

    @pytest.fixture
    def template_manager(self):
        """Create a template manager for testing"""
        return TemplateManager()

    def test_reflection_template_exists(self, template_manager):
        """Test that the reflection template exists"""
        templates = template_manager.list_templates()
        assert "reflection" in templates

    def test_reflection_template_complexity_adaptation_high(self, template_manager):
        """Test that the template adapts to high complexity"""
        template = template_manager.get_template(
            "reflection",
            {
                "topic": "人工智能的伦理影响",
                "thinking_history": "已分析了技术、社会和伦理多个维度",
                "current_conclusions": "需要平衡创新与监管，建立伦理框架",
                "complexity": "high",
            },
        )

        # Check that high complexity elements are included
        assert "深度思考：高级苏格拉底式反思" in template
        assert "**反思复杂度**: 高" in template
        assert "苏格拉底式反思框架" in template

        # Check that all reflection categories are included with detailed content
        assert "1. 认识论反思 (Epistemological Reflection) - 权重: 20%" in template
        assert "2. 逻辑推理反思 (Logical Reasoning Reflection) - 权重: 20%" in template
        assert "3. 认知偏见反思 (Cognitive Bias Reflection) - 权重: 20%" in template
        assert (
            "4. 思维广度反思 (Breadth of Thinking Reflection) - 权重: 15%" in template
        )
        assert "5. 思维深度反思 (Depth of Thinking Reflection) - 权重: 15%" in template
        assert (
            "6. 实践应用反思 (Practical Application Reflection) - 权重: 10%" in template
        )

        # Check that detailed subcategories are included
        assert "知识来源与质量" in template
        assert "假设检验" in template
        assert "推理结构分析" in template
        assert "替代解释探索" in template
        assert "偏见识别" in template
        assert "情绪影响" in template
        assert "多角度思考" in template
        assert "跨学科整合" in template
        assert "问题层次分析" in template
        assert "创新与突破" in template
        assert "实用价值评估" in template
        assert "行动计划" in template

        # Check that meta-cognitive assessment is included
        assert "元认知综合评估" in template
        assert "思维过程整体评估" in template
        assert "元认知能力评估" in template
        assert "持续改进计划" in template

    def test_reflection_template_complexity_adaptation_medium(self, template_manager):
        """Test that the template adapts to medium complexity"""
        template = template_manager.get_template(
            "reflection",
            {
                "topic": "远程工作的效率与挑战",
                "thinking_history": "分析了技术、沟通和管理因素",
                "current_conclusions": "需要平衡自主性与协作，建立清晰流程",
                "complexity": "medium",
            },
        )

        # Check that medium complexity elements are included
        assert "深度思考：苏格拉底式反思" in template
        assert "**反思复杂度**: 中等" in template
        assert "苏格拉底式提问框架" in template

        # Check that all reflection categories are included with moderate detail
        assert "🤔 过程反思 (Process Reflection)" in template
        assert "🎯 结果反思 (Outcome Reflection)" in template
        assert "🧠 元认知反思 (Metacognitive Reflection)" in template

        # Check that subcategories are included
        assert "1. 思维路径审视" in template
        assert "2. 视角全面性" in template
        assert "3. 证据质量" in template
        assert "4. 假设检验" in template
        assert "5. 结论确定性" in template
        assert "6. 风险评估" in template
        assert "7. 替代解释" in template
        assert "8. 实际应用" in template
        assert "9. 思维模式" in template
        assert "10. 认知偏见" in template
        assert "11. 学习收获" in template
        assert "12. 改进方向" in template

        # Check that assessment sections are included
        assert "反思综合评估" in template
        assert "思维过程评估" in template
        assert "元认知能力评估" in template
        assert "持续改进计划" in template
        assert "最终总结" in template

    def test_reflection_template_complexity_adaptation_low(self, template_manager):
        """Test that the template adapts to low complexity"""
        template = template_manager.get_template(
            "reflection",
            {
                "topic": "个人时间管理策略",
                "thinking_history": "分析了常见时间管理方法",
                "current_conclusions": "需要根据个人习惯定制方法",
                "complexity": "low",
            },
        )

        # Check that low complexity elements are included
        assert "深度思考：基础反思引导" in template
        assert "**反思复杂度**: 低" in template
        assert "苏格拉底式基础提问" in template

        # Check that simplified categories are included
        assert "思考过程反思" in template
        assert "结论质量反思" in template
        assert "自我认知反思" in template

        # Check that simplified subcategories are included
        assert "1. 思维路径" in template
        assert "2. 证据评估" in template
        assert "3. 多角度思考" in template
        assert "4. 结论可靠性" in template
        assert "5. 替代可能性" in template
        assert "6. 应用价值" in template
        assert "7. 思维习惯" in template
        assert "8. 学习收获" in template
        assert "9. 改进方向" in template

        # Check that simplified assessment is included
        assert "总体评估" in template
        assert "思维质量评分" in template
        assert "最终总结" in template

    def test_reflection_template_parameter_handling(self, template_manager):
        """Test that the template handles all required parameters"""
        template = template_manager.get_template(
            "reflection",
            {
                "topic": "测试主题",
                "thinking_history": "测试思考历程",
                "current_conclusions": "测试结论",
                "complexity": "medium",
            },
        )

        # Check that parameters are correctly inserted
        assert "**思考主题**: 测试主题" in template
        assert "**思考历程**: 测试思考历程" in template
        assert "**当前结论**: 测试结论" in template
        assert "**反思复杂度**: 中等" in template

    def test_reflection_template_missing_parameters(self, template_manager):
        """Test that the template handles missing parameters gracefully"""
        template = template_manager.get_template(
            "reflection",
            {
                "topic": "测试主题"
                # Missing thinking_history, current_conclusions, and complexity
            },
        )

        # Check that missing parameters are handled gracefully
        assert "**思考主题**: 测试主题" in template
        assert "**思考历程**: [thinking_history]" in template
        assert "**当前结论**: [current_conclusions]" in template
        # Default complexity should be medium
        assert "**反思复杂度**: 中等" in template

    def test_reflection_template_json_format(self, template_manager):
        """Test that the template includes proper JSON format specification"""
        template = template_manager.get_template(
            "reflection",
            {
                "topic": "测试主题",
                "thinking_history": "测试思考历程",
                "current_conclusions": "测试结论",
                "complexity": "medium",
            },
        )

        # Check that JSON format is specified
        assert "## JSON输出格式" in template
        assert "```json" in template
        assert "reflection_topic" in template
        assert "thinking_process_summary" in template
        assert "process_reflection" in template
        assert "outcome_reflection" in template
        assert "metacognitive_reflection" in template
        assert "overall_assessment" in template
        assert "improvement_plan" in template
        assert "final_summary" in template


if __name__ == "__main__":
    pytest.main([__file__])
