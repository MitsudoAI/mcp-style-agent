"""
Direct tests for the Bias Detection Template
"""

import pytest

from src.mcps.deep_thinking.templates.bias_detection_template import (
    get_bias_detection_template,
    get_high_complexity_template,
    get_medium_complexity_template,
    get_low_complexity_template,
)


class TestBiasDetectionTemplateDirect:
    """Test the bias detection template functions directly"""

    def test_get_bias_detection_template_high(self):
        """Test that the template returns high complexity template when requested"""
        template = get_bias_detection_template(
            {
                "content": "人工智能对就业市场的影响分析报告",
                "context": "技术变革与劳动力市场",
                "complexity": "high",
            }
        )

        # Check that high complexity elements are included
        assert "深度思考：高级认知偏见检测" in template
        assert "**分析复杂度**: 高" in template
        assert "认知偏见全面检测框架" in template
        assert "1. 信息处理偏见" in template
        assert "2. 自我认知偏见" in template
        assert "3. 群体思维偏见" in template
        assert "```json" in template

    def test_get_bias_detection_template_medium(self):
        """Test that the template returns medium complexity template when requested"""
        template = get_bias_detection_template(
            {
                "content": "远程工作对团队协作的影响",
                "context": "组织管理与工作模式",
                "complexity": "medium",
            }
        )

        # Check that medium complexity elements are included
        assert "深度思考：认知偏见检测" in template
        assert "**分析复杂度**: 中等" in template
        assert "常见认知偏见检查清单" in template
        assert "1. 信息处理偏见" in template
        assert "2. 自我认知偏见" in template
        assert "3. 群体思维偏见" in template
        assert "```json" in template

    def test_get_bias_detection_template_low(self):
        """Test that the template returns low complexity template when requested"""
        template = get_bias_detection_template(
            {
                "content": "如何提高个人学习效率",
                "context": "个人发展与学习方法",
                "complexity": "low",
            }
        )

        # Check that low complexity elements are included
        assert "深度思考：基础认知偏见检测" in template
        assert "**分析复杂度**: 低" in template
        assert "常见认知偏见检查清单" in template
        assert "🔍 确认偏误" in template
        assert "⚓ 锚定效应" in template
        assert "```json" in template

    def test_get_bias_detection_template_default(self):
        """Test that the template defaults to medium complexity when not specified"""
        template = get_bias_detection_template(
            {"content": "测试内容", "context": "测试背景"}
        )

        # Check that medium complexity elements are included
        assert "深度思考：认知偏见检测" in template
        assert "**分析复杂度**: 中等" in template
        assert "常见认知偏见检查清单" in template
        assert "1. 信息处理偏见" in template
        assert "2. 自我认知偏见" in template
        assert "3. 群体思维偏见" in template
        assert "```json" in template

    def test_get_bias_detection_template_missing_parameters(self):
        """Test that the template handles missing parameters gracefully"""
        template = get_bias_detection_template({"content": "测试内容"})

        # Check that missing parameters are handled gracefully
        assert "**分析内容**: 测试内容" in template
        assert "**分析背景**: [context]" in template
        assert "**分析复杂度**: 中等" in template
        assert "```json" in template


if __name__ == "__main__":
    pytest.main([__file__])
