"""
Tests for the Bias Detection Template
"""

import json
import pytest

from src.mcps.deep_thinking.templates.template_manager import TemplateManager


class TestBiasDetectionTemplate:
    """Test the bias detection template functionality"""

    @pytest.fixture
    def template_manager(self):
        """Create a template manager for testing"""
        return TemplateManager()

    def test_bias_detection_template_exists(self, template_manager):
        """Test that the bias detection template exists"""
        templates = template_manager.list_templates()
        assert "bias_detection" in templates

    def test_bias_detection_template_complexity_adaptation_high(self, template_manager):
        """Test that the template adapts to high complexity"""
        template = template_manager.get_template(
            "bias_detection",
            {
                "content": "人工智能对就业市场的影响分析报告",
                "context": "技术变革与劳动力市场",
                "complexity": "high"
            }
        )
        
        # Check that high complexity elements are included
        assert "深度思考：高级认知偏见检测" in template
        assert "**分析复杂度**: 高" in template
        assert "认知偏见全面检测框架" in template
        
        # Check that all bias categories are included
        assert "信息处理偏见 (Information Processing Biases)" in template
        assert "自我认知偏见 (Self-Perception Biases)" in template
        assert "群体思维偏见 (Group Thinking Biases)" in template
        assert "决策偏见 (Decision-Making Biases)" in template
        
        # Check that detailed biases are included
        assert "确认偏误 (Confirmation Bias)" in template
        assert "锚定效应 (Anchoring Bias)" in template
        assert "可得性启发 (Availability Heuristic)" in template
        assert "代表性启发 (Representativeness Heuristic)" in template
        assert "过度自信 (Overconfidence Bias)" in template
        assert "后见之明偏误 (Hindsight Bias)" in template
        assert "光环效应 (Halo Effect)" in template
        assert "从众效应 (Bandwagon Effect)" in template
        assert "内群体偏见 (In-group Bias)" in template
        assert "沉没成本谬误 (Sunk Cost Fallacy)" in template
        assert "框架效应 (Framing Effect)" in template
        assert "认知失调 (Cognitive Dissonance)" in template
        
        # Check that meta-analysis is included
        assert "偏见检测元分析" in template
        assert "本次偏见分析本身可能存在的偏见" in template

    def test_bias_detection_template_complexity_adaptation_medium(self, template_manager):
        """Test that the template adapts to medium complexity"""
        template = template_manager.get_template(
            "bias_detection",
            {
                "content": "远程工作对团队协作的影响",
                "context": "组织管理与工作模式",
                "complexity": "medium"
            }
        )
        
        # Check that medium complexity elements are included
        assert "深度思考：认知偏见检测" in template
        assert "**分析复杂度**: 中等" in template
        assert "常见认知偏见检查清单" in template
        
        # Check that main categories are included
        assert "1. 信息处理偏见" in template
        assert "2. 自我认知偏见" in template
        assert "3. 群体思维偏见" in template
        assert "4. 决策偏见" in template
        
        # Check that common biases are included
        assert "确认偏误 (Confirmation Bias)" in template
        assert "锚定效应 (Anchoring Bias)" in template
        assert "可得性启发 (Availability Heuristic)" in template
        assert "代表性启发 (Representativeness Heuristic)" in template
        assert "过度自信 (Overconfidence Bias)" in template
        assert "后见之明偏误 (Hindsight Bias)" in template
        assert "从众效应 (Bandwagon Effect)" in template
        assert "内群体偏见 (In-group Bias)" in template
        assert "沉没成本谬误 (Sunk Cost Fallacy)" in template

    def test_bias_detection_template_complexity_adaptation_low(self, template_manager):
        """Test that the template adapts to low complexity"""
        template = template_manager.get_template(
            "bias_detection",
            {
                "content": "如何提高个人学习效率",
                "context": "个人发展与学习方法",
                "complexity": "low"
            }
        )
        
        # Check that low complexity elements are included
        assert "深度思考：基础认知偏见检测" in template
        assert "**分析复杂度**: 低" in template
        assert "常见认知偏见检查清单" in template
        
        # Check that the format is simpler
        assert "检测结果：存在/不存在，证据：" in template
        assert "缓解建议：" in template
        
        # Check that common biases are included
        assert "🔍 确认偏误 (Confirmation Bias)" in template
        assert "⚓ 锚定效应 (Anchoring Bias)" in template
        assert "📊 可得性启发 (Availability Heuristic)" in template
        assert "🎯 代表性启发 (Representativeness Heuristic)" in template
        assert "💪 过度自信 (Overconfidence Bias)" in template
        assert "🔄 后见之明偏误 (Hindsight Bias)" in template

    def test_bias_detection_template_parameter_handling(self, template_manager):
        """Test that the template handles all required parameters"""
        template = template_manager.get_template(
            "bias_detection",
            {
                "content": "测试内容",
                "context": "测试背景",
                "complexity": "medium"
            }
        )
        
        # Check that parameters are correctly inserted
        assert "**分析内容**: 测试内容" in template
        assert "**分析背景**: 测试背景" in template
        assert "**分析复杂度**: 中等" in template

    def test_bias_detection_template_missing_parameters(self, template_manager):
        """Test that the template handles missing parameters gracefully"""
        template = template_manager.get_template(
            "bias_detection",
            {
                "content": "测试内容"
                # Missing context and complexity
            }
        )
        
        # Check that missing parameters are handled gracefully
        assert "**分析内容**: 测试内容" in template
        assert "**分析背景**: [context]" in template
        # Default complexity should be medium
        assert "**分析复杂度**: 中等" in template

    def test_bias_detection_json_format(self, template_manager):
        """Test that the template includes proper JSON format specification"""
        template = template_manager.get_template(
            "bias_detection",
            {
                "content": "测试内容",
                "context": "测试背景",
                "complexity": "medium"
            }
        )
        
        # Check that JSON format is specified
        assert "## JSON输出格式" in template
        assert "```json" in template
        assert "analysis_subject" in template
        assert "analysis_context" in template
        assert "bias_detection" in template
        assert "overall_assessment" in template


if __name__ == "__main__":
    pytest.main([__file__])