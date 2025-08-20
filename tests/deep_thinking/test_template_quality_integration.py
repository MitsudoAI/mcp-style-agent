"""
Integration tests for template quality validation with template manager

Tests the integration between template validation and the existing template management system.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from mcps.deep_thinking.templates.template_validator import (
    TemplateValidator,
    ValidationSeverity,
)
from mcps.deep_thinking.templates.template_manager import TemplateManager


class TestTemplateQualityIntegration:
    """Test integration between template validation and template manager"""

    def setup_method(self):
        self.validator = TemplateValidator()
        self.template_manager = TemplateManager("templates")

    def test_validate_template_manager_templates(self):
        """Test validation of templates from template manager"""
        # Get all templates from manager
        template_names = self.template_manager.list_templates()

        assert len(template_names) > 0, "Template manager should have templates"

        validation_results = {}

        for template_name in template_names:
            try:
                # Get template content from manager
                template_content = self.template_manager.get_template(
                    template_name, params={}, use_default_if_missing=True
                )

                # Validate the template
                result = self.validator.validate_template(
                    template_content, template_name
                )
                validation_results[template_name] = result

                # Basic assertions
                assert result.template_name == template_name
                assert isinstance(result.overall_score, float)
                assert 0 <= result.overall_score <= 1
                assert isinstance(result.is_valid, bool)

                print(
                    f"✓ {template_name}: Score {result.overall_score:.2f}, "
                    f"Valid: {result.is_valid}, Issues: {len(result.issues)}"
                )

            except Exception as e:
                print(f"✗ Error validating {template_name}: {e}")
                assert False, f"Template validation failed for {template_name}: {e}"

        # Ensure we validated some templates
        assert len(validation_results) > 0

        # Check that most templates have reasonable quality
        good_templates = sum(
            1 for r in validation_results.values() if r.overall_score >= 0.7
        )
        total_templates = len(validation_results)

        print(
            f"\nQuality Summary: {good_templates}/{total_templates} templates have score >= 0.7"
        )

        # At least 70% of templates should have good quality
        assert (
            good_templates / total_templates >= 0.7
        ), f"Too many low-quality templates: {good_templates}/{total_templates}"

    def test_template_parameter_validation_integration(self):
        """Test that template validation works with parameter replacement"""
        # Test with decomposition template which has many parameters
        template_name = "decomposition"

        # Get template with parameters
        test_params = {
            "topic": "如何提高学习效率",
            "complexity": "moderate",
            "focus": "学生群体",
            "domain_context": "教育心理学",
        }

        try:
            # Get template content with parameters replaced
            template_with_params = self.template_manager.get_template(
                template_name, params=test_params
            )

            # Validate the template content (original, not with params replaced)
            original_template = self.template_manager.cache.get(template_name, "")
            result = self.validator.validate_template(original_template, template_name)

            # Should be valid and have good score
            assert result.is_valid, f"Template {template_name} should be valid"
            assert (
                result.overall_score >= 0.8
            ), f"Template {template_name} should have high quality"

            # Should detect parameters
            assert (
                result.metrics["parameter_count"] > 0
            ), "Should detect parameters in template"

            print(f"✓ Parameter integration test passed for {template_name}")
            print(f"  Original template score: {result.overall_score:.2f}")
            print(f"  Parameters detected: {result.metrics['parameter_count']}")
            print(f"  Template with params length: {len(template_with_params)} chars")

        except Exception as e:
            assert False, f"Parameter integration test failed: {e}"

    def test_template_validation_with_file_system(self):
        """Test validation of templates from file system"""
        templates_dir = Path("templates")

        if not templates_dir.exists():
            print("Templates directory not found, skipping file system test")
            return

        # Validate all templates in directory
        results = self.validator.validate_all_templates(templates_dir)

        assert len(results) > 0, "Should find template files"

        # Compare with template manager templates
        manager_templates = set(self.template_manager.list_templates())
        file_templates = set(results.keys())

        # Should have significant overlap
        common_templates = manager_templates.intersection(file_templates)
        assert (
            len(common_templates) > 0
        ), "Should have common templates between manager and files"

        print(f"✓ File system validation found {len(results)} templates")
        print(f"  Common with manager: {len(common_templates)}")
        print(f"  Manager only: {manager_templates - file_templates}")
        print(f"  Files only: {file_templates - manager_templates}")

    def test_validation_report_generation(self):
        """Test generation of validation reports"""
        templates_dir = Path("templates")

        if not templates_dir.exists():
            print("Templates directory not found, skipping report test")
            return

        # Generate validation results
        results = self.validator.validate_all_templates(templates_dir)

        # Generate report
        report = self.validator.generate_validation_report(results)

        # Basic report checks
        assert "Template Quality Validation Report" in report
        assert "Summary" in report
        assert "Individual Template Results" in report

        # Should contain template names
        for template_name in results.keys():
            assert template_name in report

        # Should contain scores and metrics
        assert "Average Quality Score" in report
        assert "Total Templates" in report

        print(f"✓ Generated validation report ({len(report)} characters)")
        print("Report preview:")
        print(report[:500] + "..." if len(report) > 500 else report)

    def test_template_improvement_suggestions(self):
        """Test that validation provides useful improvement suggestions"""
        # Create a deliberately poor template
        poor_template = """分析问题。

可能需要考虑一些因素。
也许要提供结果。
"""

        result = self.validator.validate_template(poor_template, "poor_test")

        # Should have low score and many issues
        assert result.overall_score < 0.5, "Poor template should have low score"
        assert len(result.issues) > 3, "Poor template should have many issues"
        assert len(result.suggestions) > 0, "Should provide improvement suggestions"

        # Should have critical or error issues
        serious_issues = [
            i
            for i in result.issues
            if i.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR]
        ]
        assert len(serious_issues) > 0, "Poor template should have serious issues"

        print(f"✓ Poor template validation:")
        print(f"  Score: {result.overall_score:.2f}")
        print(f"  Issues: {len(result.issues)}")
        print(f"  Suggestions: {result.suggestions[:2]}")  # Show first 2 suggestions

    def test_template_quality_metrics(self):
        """Test that quality metrics are meaningful"""
        # Test with a good template
        good_template = """# 高质量分析模板

你是一位专业的数据分析师，具有丰富的问题分析经验。

请对以下问题进行深入分析：

**分析主题**: {topic}
**复杂程度**: {complexity}
**关注重点**: {focus}
**领域背景**: {domain_context}

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
  "detailed_analysis": {
    "core_elements": "核心要素分析",
    "risk_assessment": "风险评估",
    "opportunities": "机会识别"
  },
  "confidence_level": 0.85,
  "recommendations": [
    "具体建议1",
    "具体建议2"
  ]
}
```

请开始分析：
"""

        result = self.validator.validate_template(good_template, "good_test")

        # Should have high score and few issues
        assert result.overall_score > 0.8, "Good template should have high score"
        assert result.is_valid, "Good template should be valid"

        # Check metrics
        metrics = result.metrics
        assert metrics["parameter_count"] > 0, "Should detect parameters"
        assert metrics["word_count"] > 50, "Should count words"
        assert metrics["line_count"] > 10, "Should count lines"
        assert metrics["format_score"] > 0.8, "Should have good format score"
        assert metrics["content_score"] > 0.8, "Should have good content score"
        assert (
            metrics["effectiveness_score"] > 0.7
        ), "Should have good effectiveness score"

        print(f"✓ Good template metrics:")
        print(f"  Overall score: {result.overall_score:.2f}")
        print(f"  Format: {metrics['format_score']:.2f}")
        print(f"  Content: {metrics['content_score']:.2f}")
        print(f"  Effectiveness: {metrics['effectiveness_score']:.2f}")
        print(f"  Parameters: {metrics['parameter_count']}")
        print(f"  Size: {metrics['word_count']} words, {metrics['line_count']} lines")


def run_integration_tests():
    """Run all integration tests"""
    test_instance = TestTemplateQualityIntegration()
    test_instance.setup_method()

    tests = [
        test_instance.test_validate_template_manager_templates,
        test_instance.test_template_parameter_validation_integration,
        test_instance.test_template_validation_with_file_system,
        test_instance.test_validation_report_generation,
        test_instance.test_template_improvement_suggestions,
        test_instance.test_template_quality_metrics,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            print(f"\n{'='*60}")
            print(f"Running: {test.__name__}")
            print("=" * 60)
            test()
            print(f"✅ PASSED: {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {test.__name__}")
            print(f"Error: {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"INTEGRATION TEST RESULTS")
    print(f"{'='*60}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")

    if failed == 0:
        print("🎉 All integration tests passed!")
    else:
        print(f"⚠️  {failed} test(s) failed")

    return failed == 0


if __name__ == "__main__":
    success = run_integration_tests()
    exit(0 if success else 1)
