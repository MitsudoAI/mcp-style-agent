"""
Tests for the Innovation Thinking Template
"""

import json
import pytest

from src.mcps.deep_thinking.templates.template_manager import TemplateManager


class TestInnovationTemplate:
    """Test the innovation thinking template functionality"""

    @pytest.fixture
    def template_manager(self):
        """Create a template manager for testing"""
        return TemplateManager()

    def test_innovation_template_exists(self, template_manager):
        """Test that the innovation template exists"""
        templates = template_manager.list_templates()
        assert "innovation" in templates

    def test_innovation_template_complexity_adaptation_high(self, template_manager):
        """Test that the template adapts to high complexity"""
        template = template_manager.get_template(
            "innovation",
            {
                "concept": "智能家居系统",
                "direction": "提高能源效率和用户体验",
                "constraints": "成本控制，兼容现有设备",
                "method": "scamper",
                "complexity": "high",
            },
        )

        # Check that high complexity elements are included
        assert "深度思考：高级创新思维激发" in template
        assert "**思考复杂度**: 高" in template
        assert "多维创新思维框架" in template

        # Check that all SCAMPER categories are included with detailed content
        assert "S - Substitute (替代) - 权重: 12%" in template
        assert "C - Combine (结合) - 权重: 12%" in template
        assert "A - Adapt (适应) - 权重: 12%" in template
        assert "M - Modify/Magnify/Minify (修改/放大/缩小) - 权重: 12%" in template
        assert "P - Put to Other Uses (其他用途) - 权重: 12%" in template
        assert "E - Eliminate (消除) - 权重: 12%" in template
        assert "R - Reverse/Rearrange (逆转/重组) - 权重: 12%" in template

        # Check that TRIZ principles are included
        assert "TRIZ创新原理应用 - 权重: 16%" in template
        assert "分割原理 (Segmentation)" in template
        assert "提取原理 (Extraction)" in template

        # Check that cross-domain inspiration is included
        assert "跨领域启发 - 权重: 12%" in template
        assert "自然界启发" in template
        assert "艺术与设计启发" in template
        assert "科技前沿启发" in template
        assert "社会科学启发" in template

        # Check that detailed evaluation criteria are included
        assert "创新评估与筛选" in template
        assert "新颖性 (Novelty) - 权重: 25%" in template
        assert "可行性 (Feasibility) - 权重: 25%" in template
        assert "价值潜力 (Value Potential) - 权重: 25%" in template
        assert "适应性 (Adaptability) - 权重: 15%" in template
        assert "可持续性 (Sustainability) - 权重: 10%" in template

        # Check that implementation path and risk analysis are included
        assert "实施路径与风险分析" in template
        assert "短期行动 (0-6个月):" in template
        assert "中期发展 (6-18个月):" in template
        assert "长期愿景 (18+个月):" in template
        assert "风险分析" in template

        # Check that meta-analysis is included
        assert "创新思维元分析" in template

    def test_innovation_template_complexity_adaptation_medium(self, template_manager):
        """Test that the template adapts to medium complexity"""
        template = template_manager.get_template(
            "innovation",
            {
                "concept": "在线教育平台",
                "direction": "提高学生参与度和学习效果",
                "constraints": "适用于低带宽环境，支持移动设备",
                "method": "scamper",
                "complexity": "medium",
            },
        )

        # Check that medium complexity elements are included
        assert "深度思考：创新思维激发" in template
        assert "**思考复杂度**: 中等" in template
        assert "SCAMPER创新技法" in template

        # Check that all SCAMPER categories are included with moderate detail
        assert "S - Substitute (替代)" in template
        assert "C - Combine (结合)" in template
        assert "A - Adapt (适应)" in template
        assert "M - Modify (修改)" in template
        assert "P - Put to Other Uses (其他用途)" in template
        assert "E - Eliminate (消除)" in template
        assert "R - Reverse/Rearrange (逆转/重组)" in template

        # Check that each category has core questions and thinking directions
        assert "**核心问题**:" in template
        assert "**思考方向**:" in template
        assert "**创新想法**:" in template

        # Check that cross-domain inspiration is included
        assert "跨领域启发" in template
        assert "自然界" in template
        assert "艺术与设计" in template
        assert "科技前沿" in template
        assert "社会科学" in template

        # Check that evaluation criteria are included
        assert "创新评估" in template
        assert "1. 新颖性 (1-10分)" in template
        assert "2. 可行性 (1-10分)" in template
        assert "3. 价值潜力 (1-10分)" in template
        assert "4. 实施难度 (1-10分，越低越好)" in template

        # Check that best innovation plans are included
        assert "最佳创新方案" in template
        assert "方案一：[创新名称]" in template
        assert "方案二：[创新名称]" in template
        assert "方案三：[创新名称]" in template

    def test_innovation_template_complexity_adaptation_low(self, template_manager):
        """Test that the template adapts to low complexity"""
        template = template_manager.get_template(
            "innovation",
            {
                "concept": "个人时间管理工具",
                "direction": "减少拖延，提高效率",
                "constraints": "简单易用，无需复杂设置",
                "method": "scamper",
                "complexity": "low",
            },
        )

        # Check that low complexity elements are included
        assert "深度思考：基础创新思维" in template
        assert "**思考复杂度**: 低" in template
        assert "简化SCAMPER创新法" in template

        # Check that all SCAMPER categories are included with simplified content
        assert "S - 替代 (Substitute)" in template
        assert "C - 结合 (Combine)" in template
        assert "A - 适应 (Adapt)" in template
        assert "M - 修改 (Modify)" in template
        assert "P - 其他用途 (Put to other uses)" in template
        assert "E - 简化 (Eliminate)" in template
        assert "R - 重组 (Rearrange)" in template

        # Check that each category has simple questions and idea space
        assert "创新想法：" in template

        # Check that simplified cross-domain inspiration is included
        assert "跨领域灵感" in template
        assert "自然界启发" in template
        assert "其他行业启发" in template

        # Check that simplified evaluation is included
        assert "创新评估" in template
        assert "想法一：[创新名称]" in template
        assert "新颖性 (1-10分)：" in template
        assert "可行性 (1-10分)：" in template
        assert "价值潜力 (1-10分)：" in template

        # Check that simplified best innovation plan is included
        assert "最佳创新方案" in template
        assert "推荐方案：[创新名称]" in template
        assert "**描述**：" in template
        assert "**优势**：" in template
        assert "**实施步骤**：" in template

    def test_innovation_template_parameter_handling(self, template_manager):
        """Test that the template handles all required parameters"""
        template = template_manager.get_template(
            "innovation",
            {
                "concept": "测试概念",
                "direction": "测试方向",
                "constraints": "测试约束",
                "method": "scamper",
                "complexity": "medium",
            },
        )

        # Check that parameters are correctly inserted
        assert "**基础概念**: 测试概念" in template
        assert "**创新方向**: 测试方向" in template
        assert "**约束条件**: 测试约束" in template
        assert "**思考复杂度**: 中等" in template

    def test_innovation_template_missing_parameters(self, template_manager):
        """Test that the template handles missing parameters gracefully"""
        template = template_manager.get_template(
            "innovation",
            {
                "concept": "测试概念"
                # Missing direction, constraints, method, and complexity
            },
        )

        # Check that missing parameters are handled gracefully
        assert "**基础概念**: 测试概念" in template
        assert "**创新方向**: [direction]" in template
        assert "**约束条件**: [constraints]" in template
        # Default method should be scamper
        assert "SCAMPER创新技法" in template
        # Default complexity should be medium
        assert "**思考复杂度**: 中等" in template

    def test_innovation_template_json_format(self, template_manager):
        """Test that the template includes proper JSON format specification"""
        template = template_manager.get_template(
            "innovation",
            {
                "concept": "测试概念",
                "direction": "测试方向",
                "constraints": "测试约束",
                "complexity": "medium",
            },
        )

        # Check that JSON format is specified
        assert "## JSON输出格式" in template
        assert "```json" in template
        assert "innovation_subject" in template
        assert "innovation_direction" in template
        assert "constraints" in template
        assert "scamper_ideas" in template
        assert "cross_domain_ideas" in template
        assert "top_innovations" in template


if __name__ == "__main__":
    pytest.main([__file__])
