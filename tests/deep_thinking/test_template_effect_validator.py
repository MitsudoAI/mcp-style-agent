"""
Tests for Template Effect Validator

Tests the automated template effectiveness validation system.
"""

import pytest
from pathlib import Path
import sys

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from mcps.deep_thinking.templates.template_effect_validator import (
    TemplateEffectValidator,
    TemplateEffectMetrics,
    TemplateEffectReport,
    validate_template_effects,
    generate_template_effect_report,
)


class TestTemplateEffectValidator:
    """Test the template effect validator"""

    def setup_method(self):
        self.validator = TemplateEffectValidator()

    def test_validate_high_quality_template(self):
        """Test validation of a high-quality template"""
        high_quality_template = """# 高质量分析模板

你是一位专业的数据分析师，具有丰富的问题分析经验。

请对以下问题进行深入分析：

**分析主题**: {topic}
**复杂程度**: {complexity}
**关注重点**: {focus}

## 分析要求
1. 请具体分析问题的核心要素和关键因素
2. 必须提供至少3个不同角度的深入分析
3. 确保分析的逻辑性和准确性
4. 需要考虑潜在的风险和机会

## 输出格式
请按照以下JSON格式输出分析结果：

```json
{
  "analysis_summary": "问题分析的总体概述",
  "key_findings": [
    "关键发现1",
    "关键发现2", 
    "关键发现3"
  ],
  "confidence_level": 0.85,
  "recommendations": [
    "具体建议1",
    "具体建议2"
  ]
}
```

请开始分析：
"""

        metrics = self.validator.validate_template_effect(
            high_quality_template, "high_quality_test"
        )

        assert isinstance(metrics, TemplateEffectMetrics)
        assert metrics.template_name == "high_quality_test"
        assert metrics.effectiveness_score > 0.7
        assert metrics.output_quality_score > 0.7
        assert metrics.instruction_clarity_score > 0.7
        assert 0 <= metrics.structure_completeness <= 1
        assert 0 <= metrics.content_relevance <= 1
        assert 0 <= metrics.format_compliance <= 1
        assert 0 <= metrics.instruction_following <= 1
        assert 0 <= metrics.language_clarity <= 1
        assert 0 <= metrics.requirement_clarity <= 1
        assert 0 <= metrics.parameter_usage <= 1

    def test_validate_low_quality_template(self):
        """Test validation of a low-quality template"""
        low_quality_template = """# 简单模板

分析问题。
可能需要考虑一些因素。
"""

        metrics = self.validator.validate_template_effect(
            low_quality_template, "low_quality_test"
        )

        assert isinstance(metrics, TemplateEffectMetrics)
        assert metrics.template_name == "low_quality_test"
        assert metrics.effectiveness_score < 0.6
        assert metrics.output_quality_score < 0.6
        assert metrics.instruction_clarity_score < 0.6

    def test_structure_completeness_scoring(self):
        """Test structure completeness scoring"""
        # Template with good structure
        structured_template = """# 结构化模板

你是专业分析师，请分析以下问题：

**问题**: {topic}

## 分析要求
请按照以下步骤进行分析。

## 输出格式
```json
{"result": "分析结果"}
```
"""

        # Template with poor structure
        unstructured_template = """分析问题"""

        structured_score = self.validator._test_structure_completeness(
            structured_template, "structured_test"
        )
        unstructured_score = self.validator._test_structure_completeness(
            unstructured_template, "unstructured_test"
        )

        assert structured_score > unstructured_score
        assert structured_score > 0.7
        assert unstructured_score < 0.5

    def test_content_relevance_scoring(self):
        """Test content relevance scoring"""
        # Template with specific content
        specific_template = """# 具体模板

请具体分析问题，必须提供至少3个角度，确保每个角度不少于100字。

## 步骤
1. 详细分析
2. 具体评估

例如：可以从技术、经济、社会角度分析。
"""

        # Template with vague content
        vague_template = """# 模糊模板

可能需要分析一些问题，也许要考虑相关因素，大概要提供一些观点。
"""

        specific_score = self.validator._test_content_relevance(
            specific_template, "specific_test"
        )
        vague_score = self.validator._test_content_relevance(
            vague_template, "vague_test"
        )

        assert specific_score > vague_score
        assert specific_score > 0.6
        assert vague_score < 0.4

    def test_format_compliance_scoring(self):
        """Test format compliance scoring"""
        # Template with good format
        well_formatted_template = """# 格式良好模板

## 分析要求
1. 第一步
2. 第二步

### 子要求
- 要点1
- 要点2

```json
{
  "result": "有效JSON"
}
```
"""

        # Template with poor format
        poorly_formatted_template = """# 格式差模板

分析要求
第一步
第二步

```json
{
  "result": invalid_json,
}
```
"""

        good_score = self.validator._test_format_compliance(well_formatted_template)
        poor_score = self.validator._test_format_compliance(poorly_formatted_template)

        assert good_score > poor_score
        assert good_score > 0.8
        assert poor_score < 1.0  # Poor format should still be less than perfect

    def test_language_clarity_scoring(self):
        """Test language clarity scoring"""
        # Clear language template
        clear_template = """# 清晰模板

请明确分析问题，确保详细说明每个步骤。
必须具体描述分析过程，准确提供结论。
"""

        # Vague language template
        vague_template = """# 模糊模板

可能需要分析问题，也许要考虑因素。
大概要提供观点，似乎应该包含结论。
"""

        clear_score = self.validator._test_language_clarity(clear_template)
        vague_score = self.validator._test_language_clarity(vague_template)

        assert clear_score > vague_score
        assert clear_score > 0.7
        assert vague_score < 0.8  # Vague should be less than clear

    def test_parameter_usage_scoring(self):
        """Test parameter usage scoring"""
        # Template with good parameters
        good_params_template = """# 参数模板

分析主题: {topic}
复杂度: {complexity}
关注点: {focus}
背景: {domain_context}
"""

        # Template with no parameters
        no_params_template = """# 无参数模板

分析问题并提供结果。
"""

        good_score = self.validator._test_parameter_usage(good_params_template)
        no_params_score = self.validator._test_parameter_usage(no_params_template)

        assert good_score > no_params_score
        assert good_score > 0.8
        assert no_params_score == 0.7  # No parameters is okay, gets default score

    def test_validate_all_templates(self):
        """Test validation of all templates in directory"""
        templates_dir = Path("templates")

        if not templates_dir.exists():
            pytest.skip("Templates directory not found")

        report = self.validator.validate_all_templates("templates")

        assert isinstance(report, TemplateEffectReport)
        assert report.total_templates >= 0
        assert report.tested_templates >= 0
        assert 0 <= report.average_effectiveness <= 1
        assert report.high_quality_count >= 0
        assert report.medium_quality_count >= 0
        assert report.low_quality_count >= 0
        assert isinstance(report.template_metrics, dict)
        assert isinstance(report.recommendations, list)

        # Check that tested templates have metrics
        for template_name, metrics in report.template_metrics.items():
            assert isinstance(metrics, TemplateEffectMetrics)
            assert metrics.template_name == template_name
            assert 0 <= metrics.effectiveness_score <= 1

    def test_generate_detailed_report(self):
        """Test detailed report generation"""
        templates_dir = Path("templates")

        if not templates_dir.exists():
            pytest.skip("Templates directory not found")

        report = self.validator.validate_all_templates("templates")
        detailed_report = self.validator.generate_detailed_report(report)

        assert isinstance(detailed_report, str)
        assert "Template Effectiveness Validation Report" in detailed_report
        assert "Summary" in detailed_report
        assert "Total Templates" in detailed_report
        assert "Average Effectiveness" in detailed_report

        if report.template_metrics:
            assert "Individual Template Results" in detailed_report

            # Should contain template names
            for template_name in report.template_metrics.keys():
                assert template_name in detailed_report

        if report.recommendations:
            assert "Recommendations" in detailed_report


class TestTemplateEffectConvenienceFunctions:
    """Test convenience functions"""

    def test_validate_template_effects_function(self):
        """Test validate_template_effects convenience function"""
        templates_dir = Path("templates")

        if not templates_dir.exists():
            pytest.skip("Templates directory not found")

        report = validate_template_effects("templates")

        assert isinstance(report, TemplateEffectReport)
        assert report.total_templates >= 0

    def test_generate_template_effect_report_function(self):
        """Test generate_template_effect_report convenience function"""
        templates_dir = Path("templates")

        if not templates_dir.exists():
            pytest.skip("Templates directory not found")

        report_text = generate_template_effect_report("templates")

        assert isinstance(report_text, str)
        assert "Template Effectiveness Validation Report" in report_text

    def test_generate_report_with_output_file(self):
        """Test generating report with output file"""
        templates_dir = Path("templates")

        if not templates_dir.exists():
            pytest.skip("Templates directory not found")

        output_file = "test_template_report.md"

        try:
            report_text = generate_template_effect_report("templates", output_file)

            # Check that file was created
            assert Path(output_file).exists()

            # Check file content
            file_content = Path(output_file).read_text()
            assert file_content == report_text
            assert "Template Effectiveness Validation Report" in file_content

        finally:
            # Clean up
            if Path(output_file).exists():
                Path(output_file).unlink()


class TestTemplateEffectMetrics:
    """Test TemplateEffectMetrics dataclass"""

    def test_template_effect_metrics_creation(self):
        """Test creating TemplateEffectMetrics"""
        metrics = TemplateEffectMetrics(
            template_name="test_template",
            effectiveness_score=0.85,
            output_quality_score=0.80,
            instruction_clarity_score=0.90,
            structure_completeness=0.85,
            content_relevance=0.75,
            format_compliance=0.90,
            instruction_following=0.80,
            language_clarity=0.85,
            requirement_clarity=0.95,
            parameter_usage=0.90,
        )

        assert metrics.template_name == "test_template"
        assert metrics.effectiveness_score == 0.85
        assert metrics.output_quality_score == 0.80
        assert metrics.instruction_clarity_score == 0.90
        assert hasattr(metrics, "test_timestamp")


class TestTemplateEffectReport:
    """Test TemplateEffectReport dataclass"""

    def test_template_effect_report_creation(self):
        """Test creating TemplateEffectReport"""
        report = TemplateEffectReport(
            total_templates=10,
            tested_templates=8,
            average_effectiveness=0.75,
            high_quality_count=3,
            medium_quality_count=4,
            low_quality_count=1,
        )

        assert report.total_templates == 10
        assert report.tested_templates == 8
        assert report.average_effectiveness == 0.75
        assert report.high_quality_count == 3
        assert report.medium_quality_count == 4
        assert report.low_quality_count == 1
        assert hasattr(report, "test_timestamp")
        assert isinstance(report.template_metrics, dict)
        assert isinstance(report.recommendations, list)


def run_template_effect_validator_tests():
    """Run all template effect validator tests"""
    test_classes = [
        TestTemplateEffectValidator,
        TestTemplateEffectConvenienceFunctions,
        TestTemplateEffectMetrics,
        TestTemplateEffectReport,
    ]

    passed = 0
    failed = 0

    for test_class in test_classes:
        test_instance = test_class()
        if hasattr(test_instance, "setup_method"):
            test_instance.setup_method()

        # Get all test methods
        test_methods = [
            method for method in dir(test_instance) if method.startswith("test_")
        ]

        for test_method_name in test_methods:
            try:
                print(f"\n{'='*60}")
                print(f"Running: {test_class.__name__}.{test_method_name}")
                print("=" * 60)

                test_method = getattr(test_instance, test_method_name)
                test_method()

                print(f"✅ PASSED: {test_class.__name__}.{test_method_name}")
                passed += 1

            except Exception as e:
                print(f"❌ FAILED: {test_class.__name__}.{test_method_name}")
                print(f"Error: {e}")
                failed += 1

    print(f"\n{'='*60}")
    print(f"TEMPLATE EFFECT VALIDATOR TEST RESULTS")
    print(f"{'='*60}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")

    if failed == 0:
        print("🎉 All template effect validator tests passed!")
    else:
        print(f"⚠️  {failed} test(s) failed")

    return failed == 0


if __name__ == "__main__":
    success = run_template_effect_validator_tests()
    exit(0 if success else 1)
