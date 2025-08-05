"""
Tests for Template Quality Validation System

Tests template format validation, content quality checks, instruction clarity,
and automated effectiveness testing.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch

from src.mcps.deep_thinking.templates.template_validator import (
    TemplateValidator,
    TemplateFormatValidator,
    TemplateContentValidator,
    TemplateEffectivenessValidator,
    ValidationSeverity,
    ValidationIssue,
    TemplateValidationResult,
    validate_template_quick
)


class TestTemplateFormatValidator:
    """Test template format validation"""
    
    def setup_method(self):
        self.validator = TemplateFormatValidator()
    
    def test_valid_template_format(self):
        """Test validation of a well-formatted template"""
        template = """# 测试模板

你是一位专业的分析师，请分析以下问题：

**问题**: {topic}
**复杂度**: {complexity}

## 分析要求
请按照以下步骤进行分析：
1. 理解问题背景
2. 收集相关信息
3. 提供分析结果

## 输出格式
```json
{
  "analysis": "分析结果",
  "confidence": 0.8
}
```
"""
        issues = self.validator.validate_format(template, "test_template")
        
        # Should have minimal issues for a well-formatted template
        critical_errors = [i for i in issues if i.severity == ValidationSeverity.ERROR]
        assert len(critical_errors) == 0
    
    def test_missing_title(self):
        """Test detection of missing title"""
        template = """你是一位分析师，请分析问题。"""
        
        issues = self.validator.validate_format(template, "test_template")
        
        title_issues = [i for i in issues if "title" in i.message.lower()]
        assert len(title_issues) > 0
        assert any(i.severity == ValidationSeverity.ERROR for i in title_issues)
    
    def test_parameter_validation(self):
        """Test parameter usage validation"""
        template = """# 测试模板
        
参数测试: {valid_param} {|invalid_param} {}
"""
        issues = self.validator.validate_format(template, "test_template")
        
        param_issues = [i for i in issues if i.category == "parameters"]
        assert len(param_issues) > 0
    
    def test_json_format_validation(self):
        """Test JSON format block validation"""
        template = """# 测试模板

```json
{
  "valid": "json",
  "number": 123
}
```

```json
{
  "invalid": json,
  "missing": quote
}
```
"""
        issues = self.validator.validate_format(template, "test_template")
        
        json_issues = [i for i in issues if i.category == "json_format"]
        assert len(json_issues) > 0
    
    def test_readability_checks(self):
        """Test readability validation"""
        long_line = "这是一个非常长的行，" * 20  # Create a very long line
        template = f"""# 测试模板

{long_line}

正常长度的行。   
"""  # Line with trailing spaces
        
        issues = self.validator.validate_format(template, "test_template")
        
        readability_issues = [i for i in issues if i.category in ["readability", "formatting"]]
        assert len(readability_issues) > 0


class TestTemplateContentValidator:
    """Test template content quality validation"""
    
    def setup_method(self):
        self.validator = TemplateContentValidator()
    
    def test_instruction_clarity(self):
        """Test instruction clarity validation"""
        clear_template = """# 清晰模板

请具体分析以下问题，确保详细说明每个步骤。
要求至少提供3个具体的分析角度。
必须包含明确的结论。
"""
        
        vague_template = """# 模糊模板

可能需要分析一些问题，也许要考虑相关因素。
大概要提供一些观点。
"""
        
        clear_issues = self.validator.validate_content(clear_template, "clear_template")
        vague_issues = self.validator.validate_content(vague_template, "vague_template")
        
        clear_clarity_issues = [i for i in clear_issues if i.category == "clarity"]
        vague_clarity_issues = [i for i in vague_issues if i.category == "clarity"]
        
        # Clear template should have fewer clarity issues
        assert len(clear_clarity_issues) <= len(vague_clarity_issues)
    
    def test_specificity_validation(self):
        """Test specificity validation"""
        specific_template = """# 具体模板

请提供至少5个分析点，每个分析点不少于100字。
必须包含具体的数据支持。
确保分析深度达到专业水平。
"""
        
        vague_template = """# 模糊模板

请提供一些分析，要合理考虑相关因素。
适当包含一些数据。
"""
        
        specific_issues = self.validator.validate_content(specific_template, "specific_template")
        vague_issues = self.validator.validate_content(vague_template, "vague_template")
        
        specific_spec_issues = [i for i in specific_issues if i.category == "specificity"]
        vague_spec_issues = [i for i in vague_issues if i.category == "specificity"]
        
        # Vague template should have more specificity issues
        assert len(vague_spec_issues) >= len(specific_spec_issues)
    
    def test_completeness_validation(self):
        """Test template completeness validation"""
        # Test decomposition template
        incomplete_decomp = """# 分解模板
        
请分解问题。
"""
        
        complete_decomp = """# 分解模板
        
请对问题进行系统性分解，生成子问题。
需要建立子问题之间的关系。
输出JSON格式结果。
"""
        
        incomplete_issues = self.validator.validate_content(incomplete_decomp, "decomposition_test")
        complete_issues = self.validator.validate_content(complete_decomp, "decomposition_test")
        
        incomplete_comp_issues = [i for i in incomplete_issues if i.category == "completeness"]
        complete_comp_issues = [i for i in complete_issues if i.category == "completeness"]
        
        assert len(incomplete_comp_issues) > len(complete_comp_issues)
    
    def test_language_quality(self):
        """Test language quality validation"""
        mixed_style_template = """# 混合风格模板

您好，请您分析问题。
你需要提供详细的分析。
请你确保质量。
"""
        
        consistent_template = """# 一致风格模板

请分析问题。
你需要提供详细的分析。
请确保质量。
"""
        
        mixed_issues = self.validator.validate_content(mixed_style_template, "mixed_template")
        consistent_issues = self.validator.validate_content(consistent_template, "consistent_template")
        
        mixed_lang_issues = [i for i in mixed_issues if i.category == "language"]
        consistent_lang_issues = [i for i in consistent_issues if i.category == "language"]
        
        assert len(mixed_lang_issues) >= len(consistent_lang_issues)


class TestTemplateEffectivenessValidator:
    """Test template effectiveness validation"""
    
    def setup_method(self):
        self.validator = TemplateEffectivenessValidator()
    
    def test_parameter_replacement_testing(self):
        """Test parameter replacement effectiveness"""
        template_with_params = """# 参数模板

分析主题: {topic}
复杂度: {complexity}
关注点: {focus}
未知参数: {unknown_param}
"""
        
        issues = self.validator.validate_effectiveness(template_with_params, "param_template")
        
        param_issues = [i for i in issues if "parameter" in i.message.lower()]
        # Should detect unknown parameter
        assert len(param_issues) > 0
    
    def test_output_structure_validation(self):
        """Test output structure validation"""
        template_with_json = """# JSON模板

请输出JSON格式结果。

```json
{
  "result": "分析结果",
  "score": 0.8
}
```
"""
        
        template_without_json = """# 无JSON模板

请输出JSON格式结果。
"""
        
        with_json_issues = self.validator.validate_effectiveness(template_with_json, "with_json")
        without_json_issues = self.validator.validate_effectiveness(template_without_json, "without_json")
        
        # Template without JSON example should have more issues
        without_json_structure_issues = [i for i in without_json_issues if "JSON" in i.message]
        assert len(without_json_structure_issues) > 0
    
    def test_instruction_completeness(self):
        """Test instruction completeness validation"""
        complete_template = """# 完整模板

你是专业分析师。
请分析给定的问题。
按照以下步骤进行：
1. 理解输入
2. 执行分析
3. 输出结果
返回JSON格式。
"""
        
        incomplete_template = """# 不完整模板

分析问题。
"""
        
        complete_issues = self.validator.validate_effectiveness(complete_template, "complete")
        incomplete_issues = self.validator.validate_effectiveness(incomplete_template, "incomplete")
        
        incomplete_instruction_issues = [i for i in incomplete_issues 
                                       if "instruction" in i.message.lower()]
        assert len(incomplete_instruction_issues) > 0


class TestTemplateValidator:
    """Test main template validator"""
    
    def setup_method(self):
        self.validator = TemplateValidator()
    
    def test_comprehensive_validation(self):
        """Test comprehensive template validation"""
        good_template = """# 高质量模板

你是一位专业的系统分析师，擅长复杂问题分析。

请对以下问题进行深入分析：

**问题**: {topic}
**复杂度**: {complexity}
**关注重点**: {focus}

## 分析要求
1. 请具体分析问题的核心要素
2. 必须提供至少3个不同角度的分析
3. 确保分析深度和准确性

## 输出格式
```json
{
  "analysis": "详细分析结果",
  "key_points": ["要点1", "要点2", "要点3"],
  "confidence": 0.85,
  "recommendations": ["建议1", "建议2"]
}
```

请开始分析：
"""
        
        result = self.validator.validate_template(good_template, "good_template")
        
        assert isinstance(result, TemplateValidationResult)
        assert result.template_name == "good_template"
        assert result.overall_score > 0.7  # Should be a good score
        assert 'metrics' in result.__dict__
        assert len(result.suggestions) > 0
    
    def test_poor_template_validation(self):
        """Test validation of poor quality template"""
        poor_template = """分析问题。

可能需要考虑一些因素。
也许要提供结果。
"""
        
        result = self.validator.validate_template(poor_template, "poor_template")
        
        assert result.overall_score < 0.5  # Should be a low score
        assert not result.is_valid or len(result.issues) > 5
        
        # Should have multiple types of issues
        categories = set(issue.category for issue in result.issues)
        assert len(categories) > 2
    
    def test_scoring_system(self):
        """Test the scoring system"""
        # Create templates with different quality levels
        excellent_template = """# 优秀模板

你是专业分析师，请按照以下要求分析问题：

**输入**: {topic}
**要求**: 
- 必须提供至少5个分析角度
- 确保每个角度不少于100字
- 包含具体的数据支持

## 输出格式
```json
{
  "analysis": "详细分析",
  "confidence": 0.9
}
```
"""
        
        poor_template = """分析{topic}"""
        
        excellent_result = self.validator.validate_template(excellent_template, "excellent")
        poor_result = self.validator.validate_template(poor_template, "poor")
        
        assert excellent_result.overall_score > poor_result.overall_score
        assert excellent_result.overall_score > 0.8
        assert poor_result.overall_score < 0.4
    
    def test_validation_metrics(self):
        """Test validation metrics calculation"""
        template = """# 测试模板

你是分析师，请分析{topic}。

要求：
- 具体分析
- 详细说明

输出JSON格式。
"""
        
        result = self.validator.validate_template(template, "test_template")
        
        assert 'format_score' in result.metrics
        assert 'content_score' in result.metrics
        assert 'effectiveness_score' in result.metrics
        assert 'total_issues' in result.metrics
        assert 'parameter_count' in result.metrics
        assert 'word_count' in result.metrics
        assert 'line_count' in result.metrics
        
        # Verify metrics are reasonable
        assert 0 <= result.metrics['format_score'] <= 1
        assert 0 <= result.metrics['content_score'] <= 1
        assert 0 <= result.metrics['effectiveness_score'] <= 1
        assert result.metrics['parameter_count'] >= 0
        assert result.metrics['word_count'] > 0
        assert result.metrics['line_count'] > 0

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_file_validation(self, mock_read_text, mock_exists):
        """Test template file validation"""
        mock_exists.return_value = True
        mock_read_text.return_value = """# 文件模板

你是分析师，请分析{topic}。
"""
        
        result = self.validator.validate_template_file("test_template.tmpl")
        
        assert result.template_name == "test_template"
        assert isinstance(result, TemplateValidationResult)
    
    @patch('pathlib.Path.exists')
    def test_missing_file_validation(self, mock_exists):
        """Test validation of missing template file"""
        mock_exists.return_value = False
        
        result = self.validator.validate_template_file("missing_template.tmpl")
        
        assert not result.is_valid
        assert result.overall_score == 0.0
        assert any(issue.severity == ValidationSeverity.CRITICAL for issue in result.issues)
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    def test_validate_all_templates(self, mock_glob, mock_exists):
        """Test validation of all templates in directory"""
        mock_exists.return_value = True
        
        # Mock template files
        mock_files = [Mock(), Mock()]
        mock_files[0].stem = "template1"
        mock_files[1].stem = "template2"
        mock_files[0].read_text.return_value = "# Template 1\n分析{topic}"
        mock_files[1].read_text.return_value = "# Template 2\n分析{topic}"
        mock_glob.return_value = mock_files
        
        results = self.validator.validate_all_templates("templates/")
        
        assert len(results) == 2
        assert "template1" in results
        assert "template2" in results
    
    def test_validation_report_generation(self):
        """Test validation report generation"""
        # Create sample results
        results = {
            "good_template": TemplateValidationResult(
                template_name="good_template",
                is_valid=True,
                overall_score=0.85,
                issues=[],
                metrics={'total_issues': 0, 'parameter_count': 2, 'word_count': 50, 'line_count': 10},
                suggestions=["Template quality is excellent"]
            ),
            "poor_template": TemplateValidationResult(
                template_name="poor_template",
                is_valid=False,
                overall_score=0.45,
                issues=[
                    ValidationIssue(ValidationSeverity.ERROR, "structure", "Missing title"),
                    ValidationIssue(ValidationSeverity.WARNING, "clarity", "Vague instructions")
                ],
                metrics={'total_issues': 2, 'parameter_count': 1, 'word_count': 20, 'line_count': 5},
                suggestions=["Template needs major revision"]
            )
        }
        
        report = self.validator.generate_validation_report(results)
        
        assert "Template Quality Validation Report" in report
        assert "good_template" in report
        assert "poor_template" in report
        assert "Summary" in report
        assert "Individual Template Results" in report


class TestValidationIssue:
    """Test ValidationIssue class"""
    
    def test_validation_issue_creation(self):
        """Test creating validation issues"""
        issue = ValidationIssue(
            severity=ValidationSeverity.ERROR,
            category="test",
            message="Test message",
            line_number=10,
            suggestion="Test suggestion"
        )
        
        assert issue.severity == ValidationSeverity.ERROR
        assert issue.category == "test"
        assert issue.message == "Test message"
        assert issue.line_number == 10
        assert issue.suggestion == "Test suggestion"


class TestQuickValidation:
    """Test quick validation function"""
    
    def test_quick_validation(self):
        """Test quick template validation"""
        template = """# 快速测试模板

你是分析师，请分析{topic}。

要求具体分析。
"""
        
        result = validate_template_quick(template, "quick_test")
        
        assert 'is_valid' in result
        assert 'score' in result
        assert 'issues_count' in result
        assert 'critical_issues' in result
        assert 'suggestions' in result
        
        assert isinstance(result['is_valid'], bool)
        assert 0 <= result['score'] <= 1
        assert result['issues_count'] >= 0
        assert isinstance(result['critical_issues'], list)
        assert isinstance(result['suggestions'], list)
        assert len(result['suggestions']) <= 3  # Should limit to top 3


class TestIntegrationWithExistingTemplates:
    """Test validation with existing template files"""
    
    def setup_method(self):
        self.validator = TemplateValidator()
    
    def test_validate_decomposition_template(self):
        """Test validation of actual decomposition template"""
        # This would test against the real decomposition template
        template_path = Path("templates/decomposition.tmpl")
        
        if template_path.exists():
            result = self.validator.validate_template_file(template_path)
            
            # Decomposition template should be reasonably good
            assert result.overall_score > 0.6
            assert result.template_name == "decomposition"
            
            # Should have parameters
            assert result.metrics['parameter_count'] > 0
    
    def test_validate_evidence_collection_template(self):
        """Test validation of evidence collection template"""
        template_path = Path("templates/evidence_collection.tmpl")
        
        if template_path.exists():
            result = self.validator.validate_template_file(template_path)
            
            # Evidence template should be comprehensive
            assert result.overall_score > 0.6
            assert result.template_name == "evidence_collection"
    
    def test_validate_all_existing_templates(self):
        """Test validation of all existing templates"""
        templates_dir = Path("templates")
        
        if templates_dir.exists():
            results = self.validator.validate_all_templates(templates_dir)
            
            # Should find some templates
            assert len(results) > 0
            
            # All templates should have reasonable scores
            for name, result in results.items():
                assert result.overall_score >= 0.3  # Minimum acceptable score
                assert isinstance(result.metrics, dict)
                assert len(result.suggestions) > 0


# Performance and edge case tests
class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def setup_method(self):
        self.validator = TemplateValidator()
    
    def test_empty_template(self):
        """Test validation of empty template"""
        result = self.validator.validate_template("", "empty_template")
        
        assert not result.is_valid
        assert result.overall_score < 0.3
        assert len(result.issues) > 0
    
    def test_very_long_template(self):
        """Test validation of very long template"""
        long_template = "# 长模板\n\n" + "这是一个很长的模板内容。" * 1000
        
        result = self.validator.validate_template(long_template, "long_template")
        
        # Should still work but may have readability issues
        assert isinstance(result, TemplateValidationResult)
        assert result.metrics['word_count'] > 1000
    
    def test_template_with_special_characters(self):
        """Test template with special characters"""
        special_template = """# 特殊字符模板

包含特殊字符：@#$%^&*()
Unicode字符：中文、日本語、한국어
表情符号：😀🎉🔥

参数：{topic}
"""
        
        result = self.validator.validate_template(special_template, "special_template")
        
        # Should handle special characters gracefully
        assert isinstance(result, TemplateValidationResult)
        assert result.metrics['parameter_count'] == 1
    
    def test_malformed_json_in_template(self):
        """Test template with malformed JSON"""
        malformed_template = """# JSON模板

```json
{
  "valid": "json",
  "invalid": missing_quotes,
  "incomplete":
}
```
"""
        
        result = self.validator.validate_template(malformed_template, "malformed_template")
        
        json_issues = [i for i in result.issues if i.category == "json_format"]
        assert len(json_issues) > 0


if __name__ == "__main__":
    pytest.main([__file__])