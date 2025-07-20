"""
Tests for the Multi-Perspective Debate Template
"""

import json
import pytest

from src.mcps.deep_thinking.templates.template_manager import TemplateManager


class TestMultiPerspectiveDebateTemplate:
    """Test the multi-perspective debate template functionality"""

    @pytest.fixture
    def template_manager(self):
        """Create a template manager for testing"""
        return TemplateManager()

    def test_debate_template_exists(self, template_manager):
        """Test that the multi-perspective debate template exists"""
        templates = template_manager.list_templates()
        assert "multi_perspective_debate" in templates

    def test_debate_template_basic_structure(self, template_manager):
        """Test that the template has the correct basic structure"""
        template = template_manager.get_template(
            "multi_perspective_debate",
            {
                "topic": "教育改革的必要性",
                "evidence_summary": "收集了关于教育现状的多方面证据",
                "complexity": "medium",
                "focus": "政策影响"
            }
        )
        
        # Check main sections exist
        assert "🎭 辩论角色设定" in template
        assert "🔄 辩论流程设计" in template
        assert "📊 输出格式要求" in template
        assert "✅ 质量检查清单" in template
        
        # Check role definitions
        assert "🟢 支持方 (Proponent)" in template
        assert "🔴 反对方 (Opponent)" in template
        assert "🟡 中立分析方 (Neutral Analyst)" in template

    def test_debate_template_role_requirements(self, template_manager):
        """Test that each role has clear requirements"""
        template = template_manager.get_template(
            "multi_perspective_debate",
            {
                "topic": "人工智能发展的伦理问题",
                "evidence_summary": "AI伦理相关研究和案例",
                "complexity": "high",
                "focus": "伦理标准"
            }
        )
        
        # Check role requirements
        assert "每轮发言控制在150-200字" in template
        assert "必须引用具体证据支撑观点" in template
        assert "逻辑清晰，避免情绪化表达" in template
        assert "保持客观中立，避免偏向任何一方" in template

    def test_debate_template_flow_structure(self, template_manager):
        """Test that the debate flow is properly structured"""
        template = template_manager.get_template(
            "multi_perspective_debate",
            {
                "topic": "远程工作的利弊分析",
                "evidence_summary": "远程工作效率和影响研究",
                "complexity": "medium",
                "focus": "工作效率"
            }
        )
        
        # Check debate rounds
        assert "第一轮：立场阐述 (Position Statements)" in template
        assert "第二轮：交锋质疑 (Cross-Examination)" in template
        assert "第三轮：深度交锋 (Deep Engagement)" in template
        
        # Check round requirements
        assert "🟢 支持方开场" in template
        assert "🔴 反对方开场" in template
        assert "🟡 中立方开场" in template

    def test_debate_template_json_format(self, template_manager):
        """Test that the template includes proper JSON format specification"""
        template = template_manager.get_template(
            "multi_perspective_debate",
            {
                "topic": "环保政策的经济影响",
                "evidence_summary": "环保与经济关系研究",
                "complexity": "high",
                "focus": "政策平衡"
            }
        )
        
        # Check JSON format specification
        assert "```json" in template
        assert "debate_topic" in template
        assert "participants" in template
        assert "debate_analysis" in template
        assert "next_steps_recommendation" in template
        
        # Check participant structure
        assert '"role": "proponent"' in template
        assert '"role": "opponent"' in template
        assert '"role": "neutral_analyst"' in template

    def test_debate_template_quality_checklist(self, template_manager):
        """Test that the template includes comprehensive quality checklist"""
        template = template_manager.get_template(
            "multi_perspective_debate",
            {
                "topic": "数字货币的未来发展",
                "evidence_summary": "数字货币技术和政策研究",
                "complexity": "high",
                "focus": "技术与监管"
            }
        )
        
        # Check quality checklist sections
        assert "内容质量检查" in template
        assert "角色一致性检查" in template
        assert "格式规范检查" in template
        assert "辩论质量检查" in template
        
        # Check specific checklist items
        assert "每个角色的立场是否清晰明确？" in template
        assert "论据是否基于提供的证据？" in template
        assert "JSON格式是否完全正确？" in template
        assert "是否识别了核心分歧点？" in template

    def test_debate_template_parameter_substitution(self, template_manager):
        """Test that template parameters are properly substituted"""
        topic = "气候变化应对策略"
        evidence = "IPCC报告和各国政策分析"
        complexity = "high"
        focus = "国际合作"
        
        template = template_manager.get_template(
            "multi_perspective_debate",
            {
                "topic": topic,
                "evidence_summary": evidence,
                "complexity": complexity,
                "focus": focus
            }
        )
        
        # Check parameter substitution
        assert topic in template
        assert evidence in template
        assert complexity in template
        assert focus in template

    def test_debate_template_analysis_requirements(self, template_manager):
        """Test that the template includes proper analysis requirements"""
        template = template_manager.get_template(
            "multi_perspective_debate",
            {
                "topic": "社交媒体对青少年的影响",
                "evidence_summary": "心理学和社会学研究",
                "complexity": "medium",
                "focus": "心理健康"
            }
        )
        
        # Check analysis components
        assert "key_disagreements" in template
        assert "consensus_points" in template
        assert "strongest_arguments" in template
        assert "weakest_arguments" in template
        assert "unresolved_issues" in template
        assert "debate_quality_assessment" in template

    def test_debate_template_scoring_system(self, template_manager):
        """Test that the template includes proper scoring system"""
        template = template_manager.get_template(
            "multi_perspective_debate",
            {
                "topic": "新能源汽车发展前景",
                "evidence_summary": "技术发展和市场分析",
                "complexity": "medium",
                "focus": "市场前景"
            }
        )
        
        # Check scoring dimensions
        assert "logical_rigor" in template
        assert "evidence_usage" in template
        assert "argument_depth" in template
        assert "interaction_quality" in template
        assert "overall_score" in template

    def test_debate_template_missing_parameters(self, template_manager):
        """Test that the template handles missing parameters gracefully"""
        template = template_manager.get_template(
            "multi_perspective_debate",
            {
                "topic": "测试主题"
                # Missing other parameters
            }
        )
        
        # Should not raise exception and should include placeholder values
        assert "测试主题" in template
        assert "[evidence_summary]" in template
        assert "[complexity]" in template
        assert "[focus]" in template

    def test_debate_template_word_count_requirements(self, template_manager):
        """Test that the template specifies proper word count requirements"""
        template = template_manager.get_template(
            "multi_perspective_debate",
            {
                "topic": "在线教育的效果评估",
                "evidence_summary": "教育技术研究",
                "complexity": "medium",
                "focus": "学习效果"
            }
        )
        
        # Check word count specifications
        assert "150-200字" in template
        assert "100-150字" in template
        assert '"word_count"' in template

    def test_debate_template_evidence_integration(self, template_manager):
        """Test that the template emphasizes evidence integration"""
        template = template_manager.get_template(
            "multi_perspective_debate",
            {
                "topic": "基因编辑技术的应用前景",
                "evidence_summary": "生物技术和伦理研究",
                "complexity": "high",
                "focus": "技术伦理"
            }
        )
        
        # Check evidence requirements
        assert "必须引用具体证据支撑观点" in template
        assert "基于事实进行批判性分析" in template
        assert "evidence_cited" in template
        assert "基于证据构建逻辑链条" in template

    def test_debate_template_interaction_requirements(self, template_manager):
        """Test that the template requires proper interaction between roles"""
        template = template_manager.get_template(
            "multi_perspective_debate",
            {
                "topic": "城市化进程中的环境保护",
                "evidence_summary": "城市发展和环保研究",
                "complexity": "high",
                "focus": "可持续发展"
            }
        )
        
        # Check interaction requirements
        assert "积极回应反对方的质疑" in template
        assert "质疑支持方论据的可靠性" in template
        assert "公正评估双方论据的优劣" in template
        assert "针对前一轮的观点进行质疑和回应" in template

    def test_debate_template_output_validation(self, template_manager):
        """Test that the template includes comprehensive output validation"""
        template = template_manager.get_template(
            "multi_perspective_debate",
            {
                "topic": "人口老龄化的社会影响",
                "evidence_summary": "人口学和社会政策研究",
                "complexity": "high",
                "focus": "社会保障"
            }
        )
        
        # Check validation requirements
        assert "是否体现了真实的交锋和互动？" in template
        assert "论证逻辑是否严密？" in template
        assert "所有必需字段是否完整？" in template
        assert "质量评分是否客观？" in template


if __name__ == "__main__":
    pytest.main([__file__])