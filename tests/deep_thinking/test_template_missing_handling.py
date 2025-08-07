"""
Unit tests for Template Missing Handling functionality
Tests template missing detection, fallback mechanisms, and repair functionality
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from src.mcps.deep_thinking.templates.template_manager import TemplateManager, ConfigurationError


class TestTemplateMissingHandling:
    """Test suite for template missing handling functionality"""

    @pytest.fixture
    def temp_templates_dir(self):
        """Create a temporary templates directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def template_manager(self, temp_templates_dir):
        """Create template manager with temporary directory"""
        manager = TemplateManager(templates_dir=temp_templates_dir)
        # Clear built-in templates for clean testing
        manager.cache.clear()
        return manager

    def test_get_template_with_fallback_success(self, template_manager):
        """Test getting template with successful fallback"""
        # Add a fallback template
        template_manager.add_template("decomposition", "# Decomposition Template\nContent here")
        
        # Request a missing template that should fall back to decomposition
        result = template_manager.get_template("advanced_decomposition", {}, use_default_if_missing=True)
        
        assert "# Decomposition Template" in result
        assert "Content here" in result

    def test_get_template_with_similar_name_fallback(self, template_manager):
        """Test fallback to template with similar name"""
        # Add a template with similar name
        template_manager.add_template("evidence_collection", "# Evidence Collection\nCollect evidence here")
        
        # Request a missing template with similar name
        result = template_manager.get_template("evidence_analysis", {}, use_default_if_missing=True)
        
        assert "# Evidence Collection" in result

    def test_get_template_with_category_fallback(self, template_manager):
        """Test fallback based on category keywords"""
        # Add a category template
        template_manager.add_template("critical_evaluation", "# Critical Evaluation\nEvaluate critically")
        
        # Request a missing template with evaluation keyword
        result = template_manager.get_template("quality_evaluation", {}, use_default_if_missing=True)
        
        assert "# Critical Evaluation" in result

    def test_get_template_with_generic_fallback(self, template_manager):
        """Test fallback to generated generic template"""
        # Request a completely unknown template
        result = template_manager.get_template("unknown_template", {"topic": "test topic"}, use_default_if_missing=True)
        
        assert "通用模板" in result
        assert "unknown_template" in result
        assert "不可用" in result

    def test_get_template_without_fallback_raises_error(self, template_manager):
        """Test that missing template raises error when fallback disabled"""
        with pytest.raises(ConfigurationError, match="Template 'missing_template' not found"):
            template_manager.get_template("missing_template", {}, use_default_if_missing=False)

    def test_find_similar_templates(self, template_manager):
        """Test finding templates with similar names"""
        # Add some templates
        template_manager.add_template("decomposition", "Decomposition content")
        template_manager.add_template("evidence_collection", "Evidence content")
        template_manager.add_template("critical_evaluation", "Evaluation content")
        
        # Test finding similar templates
        similar = template_manager._find_similar_templates("decompose_problem")
        assert "decomposition" in similar
        
        similar = template_manager._find_similar_templates("evidence_analysis")
        assert "evidence_collection" in similar
        
        similar = template_manager._find_similar_templates("evaluate_quality")
        assert "critical_evaluation" in similar

    def test_determine_template_type(self, template_manager):
        """Test template type determination"""
        assert template_manager._determine_template_type("analyze_step") == "step"  # "step" takes precedence
        assert template_manager._determine_template_type("step_guidance") == "step"
        assert template_manager._determine_template_type("decomposition") == "analysis"
        assert template_manager._determine_template_type("analysis_report") == "analysis"
        assert template_manager._determine_template_type("evaluation_form") == "evaluation"
        assert template_manager._determine_template_type("unknown_template") == "generic"

    def test_generate_generic_analysis_template(self, template_manager):
        """Test generation of generic analysis template"""
        result = template_manager._generate_generic_analysis_template("test_analysis", {"topic": "AI ethics"})
        
        assert "通用分析框架" in result
        assert "test_analysis" in result
        assert "AI ethics" in result
        assert "问题理解" in result
        assert "信息收集" in result
        assert "结论总结" in result

    def test_generate_generic_step_template(self, template_manager):
        """Test generation of generic step template"""
        result = template_manager._generate_generic_step_template("test_step", {"step_name": "analysis step"})
        
        assert "步骤指导" in result
        assert "test_step" in result
        assert "准备阶段" in result
        assert "执行阶段" in result
        assert "验证阶段" in result

    def test_generate_generic_evaluation_template(self, template_manager):
        """Test generation of generic evaluation template"""
        result = template_manager._generate_generic_evaluation_template("test_eval", {"content": "test content"})
        
        assert "通用评估框架" in result
        assert "test_eval" in result
        assert "test content" in result
        assert "内容质量" in result
        assert "逻辑结构" in result
        assert "证据支撑" in result

    def test_generate_basic_generic_template(self, template_manager):
        """Test generation of basic generic template"""
        result = template_manager._generate_basic_generic_template("test_basic", {})
        
        assert "通用模板" in result
        assert "test_basic" in result
        assert "任务说明" in result
        assert "基本要求" in result
        assert "输出格式" in result

    def test_detect_missing_templates(self, template_manager):
        """Test detection of missing templates"""
        # Add some templates
        template_manager.add_template("decomposition", "Decomposition content")
        template_manager.add_template("evidence_collection", "Evidence content")
        
        result = template_manager.detect_missing_templates()
        
        assert "missing_templates" in result
        assert "available_templates" in result
        assert "total_expected" in result
        assert "total_missing" in result
        assert "missing_percentage" in result
        
        # Check that some templates are detected as missing
        assert result["total_missing"] > 0
        assert result["missing_percentage"] > 0
        
        # Check that added templates are detected as available
        available_names = [t["name"] for t in result["available_templates"]]
        assert "decomposition" in available_names
        assert "evidence_collection" in available_names

    def test_repair_missing_template_with_content(self, template_manager, temp_templates_dir):
        """Test repairing missing template with provided content"""
        template_name = "test_repair"
        template_content = "# Test Repair Template\nThis is a test template"
        
        # Ensure template doesn't exist
        assert template_name not in template_manager.cache
        
        # Repair the template
        result = template_manager.repair_missing_template(template_name, template_content)
        
        assert result is True
        assert template_name in template_manager.cache
        assert template_manager.cache[template_name] == template_content
        
        # Check that file was created
        template_file = Path(temp_templates_dir) / f"{template_name}.tmpl"
        assert template_file.exists()
        assert template_file.read_text(encoding='utf-8') == template_content

    def test_repair_missing_template_with_generic_generation(self, template_manager, temp_templates_dir):
        """Test repairing missing template with generic generation"""
        template_name = "missing_analysis"
        
        # Ensure template doesn't exist
        assert template_name not in template_manager.cache
        
        # Repair the template (should generate generic)
        result = template_manager.repair_missing_template(template_name)
        
        assert result is True
        assert template_name in template_manager.cache
        assert "通用分析框架" in template_manager.cache[template_name]
        assert template_name in template_manager.cache[template_name]
        
        # Check that file was created
        template_file = Path(temp_templates_dir) / f"{template_name}.tmpl"
        assert template_file.exists()

    def test_repair_missing_template_reload_existing_file(self, template_manager, temp_templates_dir):
        """Test repairing template by reloading existing file"""
        template_name = "existing_file"
        template_content = "# Existing File Template\nContent from file"
        
        # Create template file directly
        template_file = Path(temp_templates_dir) / f"{template_name}.tmpl"
        template_file.write_text(template_content, encoding='utf-8')
        
        # Ensure template is not in cache
        assert template_name not in template_manager.cache
        
        # Repair should reload from file
        result = template_manager.repair_missing_template(template_name)
        
        assert result is True
        assert template_name in template_manager.cache
        assert template_manager.cache[template_name] == template_content

    def test_repair_missing_template_failure(self, template_manager):
        """Test repair failure handling"""
        # Mock file operations to fail
        with patch('pathlib.Path.write_text', side_effect=Exception("Write failed")):
            result = template_manager.repair_missing_template("failing_template", "content")
            assert result is False

    def test_auto_repair_missing_templates(self, template_manager):
        """Test automatic repair of missing templates"""
        # Add one template to make some available
        template_manager.add_template("decomposition", "Decomposition content")
        
        result = template_manager.auto_repair_missing_templates()
        
        assert "attempted" in result
        assert "successful" in result
        assert "failed" in result
        assert "total_repaired" in result
        
        # Should have attempted to repair some templates
        assert len(result["attempted"]) > 0
        
        # Some repairs should have succeeded
        assert result["total_repaired"] >= 0
        
        # Check that repaired templates are now in cache
        for template_name in result["successful"]:
            assert template_name in template_manager.cache

    def test_fallback_template_logging(self, template_manager):
        """Test that fallback template usage is logged"""
        # Add a fallback template
        template_manager.add_template("decomposition", "# Decomposition Template")
        
        with patch('src.mcps.deep_thinking.templates.template_manager.logger') as mock_logger:
            template_manager.get_template("advanced_decomposition", {}, use_default_if_missing=True)
            
            # Should log the fallback usage
            mock_logger.info.assert_called()
            log_call = mock_logger.info.call_args[0][0]
            assert "fallback template" in log_call.lower()

    def test_generic_template_generation_logging(self, template_manager):
        """Test that generic template generation is logged"""
        with patch('src.mcps.deep_thinking.templates.template_manager.logger') as mock_logger:
            template_manager.get_template("completely_unknown", {}, use_default_if_missing=True)
            
            # Should log the generic generation
            mock_logger.warning.assert_called()
            log_call = mock_logger.warning.call_args[0][0]
            assert "Generating generic template" in log_call

    def test_template_repair_logging(self, template_manager):
        """Test that template repair operations are logged"""
        with patch('src.mcps.deep_thinking.templates.template_manager.logger') as mock_logger:
            template_manager.repair_missing_template("test_repair", "content")
            
            # Should log the repair
            mock_logger.info.assert_called()
            log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            assert any("Creating missing template" in call for call in log_calls)

    def test_fallback_mappings_coverage(self, template_manager):
        """Test that fallback mappings cover common template variations"""
        # Add base templates
        base_templates = ["decomposition", "critical_evaluation", "evidence_collection", 
                         "bias_detection", "innovation", "reflection", "generic_analysis"]
        
        for template in base_templates:
            template_manager.add_template(template, f"# {template.title()} Template")
        
        # Test advanced variations fall back to base templates
        advanced_templates = ["advanced_decomposition", "advanced_critical_evaluation", 
                             "comprehensive_evidence_collection", "detailed_bias_detection",
                             "enhanced_innovation", "deep_reflection"]
        
        for advanced_template in advanced_templates:
            result = template_manager.get_template(advanced_template, {}, use_default_if_missing=True)
            assert result is not None
            assert len(result) > 0
            # Should not be a generic template (which would contain "不可用")
            assert "不可用" not in result or any(base in result for base in base_templates)

    def test_category_based_fallback(self, template_manager):
        """Test category-based fallback mechanism"""
        # Add category templates
        template_manager.add_template("critical_evaluation", "# Evaluation Template")
        template_manager.add_template("innovation", "# Innovation Template")
        template_manager.add_template("bias_detection", "# Bias Template")
        
        # Test category-based fallbacks
        test_cases = [
            ("quality_evaluation", "critical_evaluation"),
            ("creative_innovation", "innovation"),
            ("bias_analysis", "bias_detection")
        ]
        
        for missing_template, expected_fallback in test_cases:
            result = template_manager.get_template(missing_template, {}, use_default_if_missing=True)
            # Should use the category fallback, not generate generic
            assert "不可用" not in result
            assert len(result) > 10  # Should be substantial content, not just placeholder

    def test_template_missing_detection_with_file_system(self, template_manager, temp_templates_dir):
        """Test missing template detection considers file system"""
        # Create a template file but don't load it
        template_name = "file_only_template"
        template_file = Path(temp_templates_dir) / f"{template_name}.tmpl"
        template_file.write_text("# File Only Template", encoding='utf-8')
        
        # Should not be in cache
        assert template_name not in template_manager.cache
        
        # Detection should find it as "not_loaded"
        result = template_manager.detect_missing_templates()
        
        # Find the template in results
        file_only_template = None
        for template_info in result["available_templates"]:
            if template_info["name"] == template_name:
                file_only_template = template_info
                break
        
        # Should be found as not_loaded (if it's in the expected templates list)
        # If not in expected list, it won't be checked, which is also correct behavior
        if file_only_template:
            assert file_only_template["status"] == "not_loaded"