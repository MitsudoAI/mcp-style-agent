"""
Tests for the Evidence Collection Template
"""

import json
import pytest

from src.mcps.deep_thinking.templates.template_manager import TemplateManager


class TestEvidenceCollectionTemplate:
    """Test the evidence collection template functionality"""

    @pytest.fixture
    def template_manager(self):
        """Create a template manager for testing"""
        return TemplateManager()

    def test_evidence_collection_template_exists(self, template_manager):
        """Test that the evidence collection template exists"""
        templates = template_manager.list_templates()
        assert "evidence_collection" in templates

    def test_evidence_collection_template_basic_structure(self, template_manager):
        """Test that the template has the correct basic structure"""
        template = template_manager.get_template(
            "evidence_collection",
            {
                "sub_question": "人工智能对就业市场的影响是什么？",
                "keywords": "人工智能, 就业市场, 自动化, 工作岗位",
                "complexity": "medium",
            },
        )

        # Check that the template contains the main sections
        assert "# 深度思考：证据收集" in template
        assert "**子问题**:" in template
        assert "**搜索关键词**:" in template
        assert "**证据要求**:" in template
        assert "**复杂度**:" in template

        # Check that the specific sub-question and keywords are included
        assert "人工智能对就业市场的影响是什么？" in template
        assert "人工智能, 就业市场, 自动化, 工作岗位" in template

    def test_evidence_collection_search_strategy(self, template_manager):
        """Test that the template includes comprehensive search strategies"""
        template = template_manager.get_template(
            "evidence_collection",
            {
                "sub_question": "测试问题",
                "keywords": "测试关键词",
                "complexity": "high",
            },
        )

        # Check that all search strategy sections are included
        assert "## 搜索策略指导：" in template
        assert "### 1. 多源证据搜索策略" in template
        assert "**学术来源**:" in template
        assert "**权威机构**:" in template
        assert "**新闻媒体**:" in template
        assert "**专家观点**:" in template
        assert "**行业资料**:" in template
        assert "**社区讨论**:" in template

        # Check that quality requirements are included
        assert "### 2. 证据质量要求" in template
        assert "**可靠性**:" in template
        assert "**时效性**:" in template
        assert "**权威性**:" in template
        assert "**多样性**:" in template
        assert "**透明度**:" in template
        assert "**相关性**:" in template

    def test_evidence_collection_execution_steps(self, template_manager):
        """Test that the template includes detailed execution steps"""
        template = template_manager.get_template(
            "evidence_collection",
            {
                "sub_question": "测试问题",
                "keywords": "测试关键词",
                "complexity": "medium",
            },
        )

        # Check that all execution steps are included
        assert "## 执行步骤：" in template
        assert "1. **关键词优化**:" in template
        assert "2. **系统性搜索**:" in template
        assert "3. **证据评估与筛选**:" in template
        assert "4. **冲突检测与处理**:" in template
        assert "5. **证据整合与结构化**:" in template

    def test_evidence_collection_json_format(self, template_manager):
        """Test that the template includes proper JSON format specification"""
        template = template_manager.get_template(
            "evidence_collection",
            {"sub_question": "测试问题", "keywords": "测试关键词", "complexity": "low"},
        )

        # Check that JSON format specification is included
        assert "## JSON输出格式规范：" in template
        assert "```json" in template
        assert "sub_question" in template
        assert "search_process" in template
        assert "evidence_collection" in template
        assert "conflict_analysis" in template
        assert "evidence_synthesis" in template

        # Check that the template includes validation checklist
        assert "## 输出验证检查清单：" in template
        assert "1. JSON格式是否完全符合规范？" in template
        assert "2. 证据多样性是否充分？" in template
        assert "3. 证据质量评估是否充分？" in template
        assert "4. 冲突检测是否到位？" in template
        assert "5. 证据整合是否有效？" in template

    def test_evidence_collection_conflict_detection(self, template_manager):
        """Test that the template includes conflict detection instructions"""
        template = template_manager.get_template(
            "evidence_collection",
            {
                "sub_question": "测试问题",
                "keywords": "测试关键词",
                "complexity": "high",
            },
        )

        # Check that conflict detection is emphasized
        assert "冲突检测与处理" in template
        assert "主动识别相互矛盾的信息" in template
        assert "分析冲突的可能原因" in template
        assert "标记争议点和不确定性" in template
        assert "提供多方观点的平衡呈现" in template

        # Check that conflict analysis is part of the JSON structure
        assert "conflict_analysis" in template
        assert "conflict_id" in template
        assert "topic" in template
        assert "conflicting_evidence" in template
        assert "nature_of_conflict" in template
        assert "possible_explanations" in template
        assert "resolution_approach" in template

    def test_evidence_collection_parameter_handling(self, template_manager):
        """Test that the template handles all required parameters"""
        template = template_manager.get_template(
            "evidence_collection",
            {
                "sub_question": "测试问题",
                "keywords": "测试关键词",
                "complexity": "medium",
            },
        )

        # Check that parameters are correctly inserted
        assert "**子问题**: 测试问题" in template
        assert "**搜索关键词**: 测试关键词" in template
        assert "**复杂度**: medium" in template

    def test_evidence_collection_missing_parameters(self, template_manager):
        """Test that the template handles missing parameters gracefully"""
        template = template_manager.get_template(
            "evidence_collection",
            {
                "sub_question": "测试问题"
                # Missing keywords and complexity
            },
        )

        # Check that missing parameters are handled gracefully
        assert "**子问题**: 测试问题" in template
        assert "**搜索关键词**: [keywords]" in template
        assert "**复杂度**: [complexity]" in template


if __name__ == "__main__":
    pytest.main([__file__])
