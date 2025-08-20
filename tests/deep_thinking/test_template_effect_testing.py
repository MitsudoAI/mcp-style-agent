"""
Template Effect Testing - 模板效果测试

Implements comprehensive testing for template effectiveness, output quality assessment,
instruction clarity testing, and automated template quality validation.

This module focuses on testing the actual effectiveness of prompt templates
in generating high-quality outputs and clear instructions.
"""

import pytest
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from unittest.mock import Mock, patch

import sys

sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from mcps.deep_thinking.templates.template_validator import (
    TemplateValidator,
    ValidationSeverity,
    ValidationIssue,
    TemplateValidationResult,
)
from mcps.deep_thinking.templates.template_manager import TemplateManager


@dataclass
class TemplateEffectTestResult:
    """Result of template effect testing"""

    template_name: str
    effectiveness_score: float  # 0.0 to 1.0
    output_quality_score: float  # 0.0 to 1.0
    instruction_clarity_score: float  # 0.0 to 1.0
    test_results: Dict[str, Any] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class TemplateOutputQualityTester:
    """Tests template output quality and structure"""

    def __init__(self):
        self.quality_metrics = {
            "structure_completeness": 0.25,
            "content_relevance": 0.25,
            "format_compliance": 0.25,
            "instruction_following": 0.25,
        }

    def test_output_quality(
        self, template_content: str, template_name: str
    ) -> Dict[str, Any]:
        """Test the quality of expected template outputs"""
        results = {
            "structure_score": 0.0,
            "content_score": 0.0,
            "format_score": 0.0,
            "instruction_score": 0.0,
            "overall_score": 0.0,
            "issues": [],
            "strengths": [],
        }

        # Test structure completeness
        structure_result = self._test_structure_completeness(
            template_content, template_name
        )
        results["structure_score"] = structure_result["score"]
        results["issues"].extend(structure_result["issues"])
        results["strengths"].extend(structure_result["strengths"])

        # Test content relevance
        content_result = self._test_content_relevance(template_content, template_name)
        results["content_score"] = content_result["score"]
        results["issues"].extend(content_result["issues"])
        results["strengths"].extend(content_result["strengths"])

        # Test format compliance
        format_result = self._test_format_compliance(template_content)
        results["format_score"] = format_result["score"]
        results["issues"].extend(format_result["issues"])
        results["strengths"].extend(format_result["strengths"])

        # Test instruction following
        instruction_result = self._test_instruction_following(template_content)
        results["instruction_score"] = instruction_result["score"]
        results["issues"].extend(instruction_result["issues"])
        results["strengths"].extend(instruction_result["strengths"])

        # Calculate overall score
        results["overall_score"] = (
            results["structure_score"] * self.quality_metrics["structure_completeness"]
            + results["content_score"] * self.quality_metrics["content_relevance"]
            + results["format_score"] * self.quality_metrics["format_compliance"]
            + results["instruction_score"]
            * self.quality_metrics["instruction_following"]
        )

        return results

    def _test_structure_completeness(
        self, content: str, template_name: str
    ) -> Dict[str, Any]:
        """Test if template has complete structure for its purpose"""
        result = {"score": 0.0, "issues": [], "strengths": []}

        # Check for essential structural elements
        has_title = bool(re.search(r"^#\s+.+", content, re.MULTILINE))
        has_context = bool(re.search(r"你是|作为|扮演", content))
        has_task_description = bool(re.search(r"请|需要|要求|任务", content))
        has_output_format = bool(re.search(r"输出格式|JSON|格式规范", content))

        structure_elements = [
            has_title,
            has_context,
            has_task_description,
            has_output_format,
        ]
        structure_score = sum(structure_elements) / len(structure_elements)

        if has_title:
            result["strengths"].append("Template has clear title")
        else:
            result["issues"].append("Missing clear title")

        if has_context:
            result["strengths"].append("Template provides role context")
        else:
            result["issues"].append("Missing role/context setting")

        if has_task_description:
            result["strengths"].append("Template has clear task description")
        else:
            result["issues"].append("Missing clear task description")

        if has_output_format:
            result["strengths"].append("Template specifies output format")
        else:
            result["issues"].append("Missing output format specification")

        # Template-specific structure checks
        if "decomposition" in template_name:
            has_decomp_strategy = bool(re.search(r"分解策略|分解方法", content))
            has_json_example = bool(re.search(r"```json", content))

            if has_decomp_strategy:
                result["strengths"].append(
                    "Decomposition template has strategy guidance"
                )
            else:
                result["issues"].append("Missing decomposition strategy guidance")
                structure_score -= 0.1

            if has_json_example:
                result["strengths"].append("Provides JSON output example")
            else:
                result["issues"].append("Missing JSON output example")
                structure_score -= 0.1

        elif "evidence" in template_name:
            has_search_strategy = bool(re.search(r"搜索策略|证据收集", content))
            has_quality_criteria = bool(re.search(r"可信度|质量要求", content))

            if has_search_strategy:
                result["strengths"].append("Evidence template has search strategy")
            else:
                result["issues"].append("Missing search strategy guidance")
                structure_score -= 0.1

            if has_quality_criteria:
                result["strengths"].append("Provides quality assessment criteria")
            else:
                result["issues"].append("Missing quality assessment criteria")
                structure_score -= 0.1

        result["score"] = max(0.0, min(1.0, structure_score))
        return result

    def _test_content_relevance(
        self, content: str, template_name: str
    ) -> Dict[str, Any]:
        """Test if template content is relevant and focused"""
        result = {"score": 0.0, "issues": [], "strengths": []}

        # Check content density and relevance
        word_count = len(content.split())
        line_count = len(content.split("\n"))

        # Check for specific, actionable instructions
        specific_instructions = len(
            re.findall(r"必须|应该|确保|至少|不少于|\d+个", content)
        )
        vague_language = len(re.findall(r"可能|也许|大概|适当|合理|相关", content))

        specificity_ratio = specific_instructions / max(vague_language, 1)

        if specificity_ratio > 2.0:
            result["strengths"].append("Template uses specific, actionable language")
            specificity_score = 1.0
        elif specificity_ratio > 1.0:
            result["strengths"].append("Template has good specificity")
            specificity_score = 0.8
        else:
            result["issues"].append("Template uses too much vague language")
            specificity_score = 0.5

        # Check for relevant examples and guidance
        has_examples = bool(re.search(r"例如|比如|示例|样例", content))
        has_step_by_step = bool(re.search(r"步骤|流程|过程", content))

        guidance_score = 0.0
        if has_examples:
            result["strengths"].append("Template provides examples")
            guidance_score += 0.5

        if has_step_by_step:
            result["strengths"].append("Template provides step-by-step guidance")
            guidance_score += 0.5

        if guidance_score == 0:
            result["issues"].append("Template lacks examples and step-by-step guidance")

        # Overall content relevance score
        content_score = specificity_score * 0.6 + guidance_score * 0.4

        result["score"] = max(0.0, min(1.0, content_score))
        return result

    def _test_format_compliance(self, content: str) -> Dict[str, Any]:
        """Test if template follows proper formatting standards"""
        result = {"score": 0.0, "issues": [], "strengths": []}

        format_score = 1.0

        # Check JSON format blocks
        json_blocks = re.findall(r"```json\s*\n(.*?)\n```", content, re.DOTALL)

        for i, json_block in enumerate(json_blocks):
            try:
                # Remove comments and template placeholders for validation
                cleaned_json = re.sub(r"//.*", "", json_block)
                cleaned_json = re.sub(
                    r'"[^"]*\{[^}]+\}[^"]*"', '"template_placeholder"', cleaned_json
                )

                # Try to parse the cleaned JSON
                json.loads(cleaned_json)
                result["strengths"].append(f"JSON block {i+1} has valid structure")
            except json.JSONDecodeError:
                # For templates, we expect some JSON to be template-like
                if "{" in json_block and "}" in json_block:
                    result["strengths"].append(
                        f"JSON block {i+1} appears to be a valid template"
                    )
                else:
                    result["issues"].append(f"JSON block {i+1} has formatting issues")
                    format_score -= 0.2

        # Check heading structure
        headings = re.findall(r"^(#+)\s+(.+)", content, re.MULTILINE)
        if headings:
            result["strengths"].append("Template has proper heading structure")

            # Check for heading level consistency
            levels = [len(h[0]) for h in headings]
            if max(levels) - min(levels) <= 2:
                result["strengths"].append("Heading levels are consistent")
            else:
                result["issues"].append("Inconsistent heading levels")
                format_score -= 0.1
        else:
            result["issues"].append("Template lacks proper heading structure")
            format_score -= 0.2

        # Check for proper list formatting
        has_numbered_lists = bool(re.search(r"^\d+\.\s+", content, re.MULTILINE))
        has_bullet_lists = bool(re.search(r"^[-*]\s+", content, re.MULTILINE))

        if has_numbered_lists or has_bullet_lists:
            result["strengths"].append("Template uses proper list formatting")
        else:
            result["issues"].append(
                "Template could benefit from better list formatting"
            )
            format_score -= 0.1

        result["score"] = max(0.0, min(1.0, format_score))
        return result

    def _test_instruction_following(self, content: str) -> Dict[str, Any]:
        """Test if template provides clear instructions that can be followed"""
        result = {"score": 0.0, "issues": [], "strengths": []}

        instruction_score = 0.0

        # Check for clear action verbs
        action_verbs = re.findall(
            r"(请|需要|要求|执行|分析|评估|生成|创建|识别|检测)", content
        )
        if len(action_verbs) >= 3:
            result["strengths"].append("Template has clear action verbs")
            instruction_score += 0.3
        else:
            result["issues"].append("Template needs more clear action verbs")

        # Check for specific requirements
        specific_reqs = re.findall(
            r"(必须|应该|确保|至少|不少于|不超过|\d+个|\d+分)", content
        )
        if len(specific_reqs) >= 2:
            result["strengths"].append("Template has specific requirements")
            instruction_score += 0.3
        else:
            result["issues"].append("Template needs more specific requirements")

        # Check for validation/verification instructions
        has_validation = bool(re.search(r"检查|验证|确认|核实", content))
        if has_validation:
            result["strengths"].append("Template includes validation instructions")
            instruction_score += 0.2
        else:
            result["issues"].append("Template could include validation steps")

        # Check for error handling guidance
        has_error_handling = bool(re.search(r"如果|当|错误|问题|异常", content))
        if has_error_handling:
            result["strengths"].append("Template provides error handling guidance")
            instruction_score += 0.2
        else:
            result["issues"].append("Template could include error handling guidance")

        result["score"] = max(0.0, min(1.0, instruction_score))
        return result


class TemplateInstructionClarityTester:
    """Tests template instruction clarity and comprehensibility"""

    def __init__(self):
        self.clarity_factors = {
            "language_clarity": 0.3,
            "structure_clarity": 0.3,
            "requirement_clarity": 0.4,
        }

    def test_instruction_clarity(self, template_content: str) -> Dict[str, Any]:
        """Test the clarity of template instructions"""
        results = {
            "language_clarity_score": 0.0,
            "structure_clarity_score": 0.0,
            "requirement_clarity_score": 0.0,
            "overall_clarity_score": 0.0,
            "clarity_issues": [],
            "clarity_strengths": [],
        }

        # Test language clarity
        lang_result = self._test_language_clarity(template_content)
        results["language_clarity_score"] = lang_result["score"]
        results["clarity_issues"].extend(lang_result["issues"])
        results["clarity_strengths"].extend(lang_result["strengths"])

        # Test structure clarity
        struct_result = self._test_structure_clarity(template_content)
        results["structure_clarity_score"] = struct_result["score"]
        results["clarity_issues"].extend(struct_result["issues"])
        results["clarity_strengths"].extend(struct_result["strengths"])

        # Test requirement clarity
        req_result = self._test_requirement_clarity(template_content)
        results["requirement_clarity_score"] = req_result["score"]
        results["clarity_issues"].extend(req_result["issues"])
        results["clarity_strengths"].extend(req_result["strengths"])

        # Calculate overall clarity score
        results["overall_clarity_score"] = (
            results["language_clarity_score"] * self.clarity_factors["language_clarity"]
            + results["structure_clarity_score"]
            * self.clarity_factors["structure_clarity"]
            + results["requirement_clarity_score"]
            * self.clarity_factors["requirement_clarity"]
        )

        return results

    def _test_language_clarity(self, content: str) -> Dict[str, Any]:
        """Test language clarity and readability"""
        result = {"score": 0.0, "issues": [], "strengths": []}

        # Check for clear, direct language
        clear_indicators = ["具体", "明确", "清晰", "详细", "准确", "完整"]
        vague_indicators = ["可能", "也许", "大概", "或许", "似乎", "好像"]

        clear_count = sum(content.count(word) for word in clear_indicators)
        vague_count = sum(content.count(word) for word in vague_indicators)

        clarity_ratio = clear_count / max(vague_count, 1)

        if clarity_ratio > 3.0:
            result["strengths"].append("Language is very clear and specific")
            language_score = 1.0
        elif clarity_ratio > 1.5:
            result["strengths"].append("Language is generally clear")
            language_score = 0.8
        else:
            result["issues"].append("Language contains too much vague terminology")
            language_score = 0.5

        # Check sentence length and complexity
        sentences = re.split(r"[。！？]", content)
        avg_sentence_length = sum(len(s.split()) for s in sentences if s.strip()) / max(
            len([s for s in sentences if s.strip()]), 1
        )

        if avg_sentence_length < 15:
            result["strengths"].append("Sentences are appropriately concise")
        elif avg_sentence_length < 25:
            result["strengths"].append("Sentence length is reasonable")
        else:
            result["issues"].append("Sentences may be too long and complex")
            language_score -= 0.2

        # Check for consistent terminology
        key_terms = re.findall(r"(模板|分析|评估|生成|输出|格式)", content)
        if len(set(key_terms)) / max(len(key_terms), 1) > 0.3:
            result["strengths"].append("Uses consistent terminology")
        else:
            result["issues"].append("Could benefit from more consistent terminology")
            language_score -= 0.1

        result["score"] = max(0.0, min(1.0, language_score))
        return result

    def _test_structure_clarity(self, content: str) -> Dict[str, Any]:
        """Test structural clarity and organization"""
        result = {"score": 0.0, "issues": [], "strengths": []}

        structure_score = 0.0

        # Check for logical flow
        has_intro = bool(re.search(r"^#.*", content, re.MULTILINE))
        has_sections = len(re.findall(r"^##.*", content, re.MULTILINE)) >= 2
        has_conclusion = bool(re.search(r"开始|请开始", content))

        if has_intro:
            result["strengths"].append("Template has clear introduction")
            structure_score += 0.3
        else:
            result["issues"].append("Template lacks clear introduction")

        if has_sections:
            result["strengths"].append("Template is well-organized with sections")
            structure_score += 0.4
        else:
            result["issues"].append(
                "Template could benefit from better section organization"
            )

        if has_conclusion:
            result["strengths"].append("Template has clear call to action")
            structure_score += 0.3
        else:
            result["issues"].append("Template lacks clear call to action")

        # Check for progressive complexity
        sections = re.split(r"^##", content, flags=re.MULTILINE)
        if len(sections) > 2:
            # Simple heuristic: later sections should build on earlier ones
            result["strengths"].append("Template follows logical progression")

        result["score"] = max(0.0, min(1.0, structure_score))
        return result

    def _test_requirement_clarity(self, content: str) -> Dict[str, Any]:
        """Test clarity of requirements and expectations"""
        result = {"score": 0.0, "issues": [], "strengths": []}

        requirement_score = 0.0

        # Check for explicit requirements
        explicit_reqs = re.findall(r"(必须|应该|需要|要求|确保)", content)
        if len(explicit_reqs) >= 3:
            result["strengths"].append("Template has clear explicit requirements")
            requirement_score += 0.4
        else:
            result["issues"].append("Template needs more explicit requirements")

        # Check for measurable criteria
        measurable_criteria = re.findall(r"(\d+个|\d+分|至少|不少于|不超过)", content)
        if len(measurable_criteria) >= 2:
            result["strengths"].append("Template provides measurable criteria")
            requirement_score += 0.3
        else:
            result["issues"].append("Template could include more measurable criteria")

        # Check for output format specification
        has_format_spec = bool(re.search(r"输出格式|JSON|格式规范", content))
        if has_format_spec:
            result["strengths"].append("Template clearly specifies output format")
            requirement_score += 0.3
        else:
            result["issues"].append(
                "Template should specify output format more clearly"
            )

        result["score"] = max(0.0, min(1.0, requirement_score))
        return result


class TemplateEffectTester:
    """Main class for comprehensive template effect testing"""

    def __init__(self):
        self.output_quality_tester = TemplateOutputQualityTester()
        self.instruction_clarity_tester = TemplateInstructionClarityTester()
        self.template_validator = TemplateValidator()

    def test_template_effectiveness(
        self, template_content: str, template_name: str
    ) -> TemplateEffectTestResult:
        """Perform comprehensive template effectiveness testing"""

        # Test output quality
        quality_results = self.output_quality_tester.test_output_quality(
            template_content, template_name
        )

        # Test instruction clarity
        clarity_results = self.instruction_clarity_tester.test_instruction_clarity(
            template_content
        )

        # Run standard validation
        validation_result = self.template_validator.validate_template(
            template_content, template_name
        )

        # Calculate overall effectiveness score
        effectiveness_score = (
            quality_results["overall_score"] * 0.4
            + clarity_results["overall_clarity_score"] * 0.3
            + validation_result.overall_score * 0.3
        )

        # Compile issues and recommendations
        all_issues = []
        all_issues.extend(quality_results["issues"])
        all_issues.extend(clarity_results["clarity_issues"])
        all_issues.extend([issue.message for issue in validation_result.issues])

        recommendations = []
        recommendations.extend(self._generate_quality_recommendations(quality_results))
        recommendations.extend(self._generate_clarity_recommendations(clarity_results))
        recommendations.extend(validation_result.suggestions)

        # Compile test results
        test_results = {
            "output_quality": quality_results,
            "instruction_clarity": clarity_results,
            "validation_result": validation_result.__dict__,
            "effectiveness_breakdown": {
                "quality_contribution": quality_results["overall_score"] * 0.4,
                "clarity_contribution": clarity_results["overall_clarity_score"] * 0.3,
                "validation_contribution": validation_result.overall_score * 0.3,
            },
        }

        return TemplateEffectTestResult(
            template_name=template_name,
            effectiveness_score=effectiveness_score,
            output_quality_score=quality_results["overall_score"],
            instruction_clarity_score=clarity_results["overall_clarity_score"],
            test_results=test_results,
            issues=all_issues,
            recommendations=list(set(recommendations)),  # Remove duplicates
        )

    def _generate_quality_recommendations(
        self, quality_results: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on quality test results"""
        recommendations = []

        if quality_results["structure_score"] < 0.7:
            recommendations.append(
                "Improve template structure with clearer sections and organization"
            )

        if quality_results["content_score"] < 0.7:
            recommendations.append(
                "Enhance content relevance and reduce vague language"
            )

        if quality_results["format_score"] < 0.7:
            recommendations.append(
                "Fix formatting issues, especially JSON examples and heading structure"
            )

        if quality_results["instruction_score"] < 0.7:
            recommendations.append(
                "Strengthen instructions with more action verbs and specific requirements"
            )

        return recommendations

    def _generate_clarity_recommendations(
        self, clarity_results: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on clarity test results"""
        recommendations = []

        if clarity_results["language_clarity_score"] < 0.7:
            recommendations.append(
                "Use more specific and direct language, avoid vague terms"
            )

        if clarity_results["structure_clarity_score"] < 0.7:
            recommendations.append(
                "Improve structural organization with better section flow"
            )

        if clarity_results["requirement_clarity_score"] < 0.7:
            recommendations.append("Make requirements more explicit and measurable")

        return recommendations

    def test_all_templates(
        self, templates_dir: str
    ) -> Dict[str, TemplateEffectTestResult]:
        """Test effectiveness of all templates in a directory"""
        results = {}
        templates_path = Path(templates_dir)

        if not templates_path.exists():
            return results

        for template_file in templates_path.glob("*.tmpl"):
            try:
                content = template_file.read_text(encoding="utf-8")
                result = self.test_template_effectiveness(content, template_file.stem)
                results[template_file.stem] = result
            except Exception as e:
                # Create error result
                results[template_file.stem] = TemplateEffectTestResult(
                    template_name=template_file.stem,
                    effectiveness_score=0.0,
                    output_quality_score=0.0,
                    instruction_clarity_score=0.0,
                    issues=[f"Error testing template: {str(e)}"],
                    recommendations=["Fix template file issues before testing"],
                )

        return results

    def generate_effectiveness_report(
        self, results: Dict[str, TemplateEffectTestResult]
    ) -> str:
        """Generate a comprehensive effectiveness testing report"""
        if not results:
            return "No template test results available."

        report_lines = [
            "# Template Effectiveness Testing Report",
            f"Generated on: {Path(__file__).name}",
            "",
            "## Executive Summary",
            "",
        ]

        # Calculate summary statistics
        total_templates = len(results)
        avg_effectiveness = (
            sum(r.effectiveness_score for r in results.values()) / total_templates
        )
        avg_quality = (
            sum(r.output_quality_score for r in results.values()) / total_templates
        )
        avg_clarity = (
            sum(r.instruction_clarity_score for r in results.values()) / total_templates
        )

        high_quality_templates = sum(
            1 for r in results.values() if r.effectiveness_score >= 0.8
        )
        medium_quality_templates = sum(
            1 for r in results.values() if 0.6 <= r.effectiveness_score < 0.8
        )
        low_quality_templates = sum(
            1 for r in results.values() if r.effectiveness_score < 0.6
        )

        report_lines.extend(
            [
                f"- **Total Templates Tested**: {total_templates}",
                f"- **Average Effectiveness Score**: {avg_effectiveness:.2f}",
                f"- **Average Output Quality Score**: {avg_quality:.2f}",
                f"- **Average Instruction Clarity Score**: {avg_clarity:.2f}",
                "",
                f"- **High Quality Templates** (≥0.8): {high_quality_templates} ({high_quality_templates/total_templates*100:.1f}%)",
                f"- **Medium Quality Templates** (0.6-0.8): {medium_quality_templates} ({medium_quality_templates/total_templates*100:.1f}%)",
                f"- **Low Quality Templates** (<0.6): {low_quality_templates} ({low_quality_templates/total_templates*100:.1f}%)",
                "",
                "## Individual Template Results",
                "",
            ]
        )

        # Sort templates by effectiveness score (descending)
        sorted_results = sorted(
            results.items(), key=lambda x: x[1].effectiveness_score, reverse=True
        )

        for template_name, result in sorted_results:
            status_emoji = (
                "🟢"
                if result.effectiveness_score >= 0.8
                else "🟡" if result.effectiveness_score >= 0.6 else "🔴"
            )

            report_lines.extend(
                [
                    f"### {status_emoji} {template_name}",
                    "",
                    f"- **Effectiveness Score**: {result.effectiveness_score:.2f}",
                    f"- **Output Quality Score**: {result.output_quality_score:.2f}",
                    f"- **Instruction Clarity Score**: {result.instruction_clarity_score:.2f}",
                    "",
                ]
            )

            if result.issues:
                report_lines.extend(["**Issues Found**:", ""])
                for issue in result.issues[:5]:  # Limit to top 5 issues
                    report_lines.append(f"- {issue}")
                report_lines.append("")

            if result.recommendations:
                report_lines.extend(["**Recommendations**:", ""])
                for rec in result.recommendations[:3]:  # Limit to top 3 recommendations
                    report_lines.append(f"- {rec}")
                report_lines.append("")

            report_lines.append("---")
            report_lines.append("")

        return "\n".join(report_lines)


# Test classes for the template effect testing functionality
class TestTemplateOutputQualityTester:
    """Test the output quality testing functionality"""

    def setup_method(self):
        self.tester = TemplateOutputQualityTester()

    def test_high_quality_template(self):
        """Test with a high-quality template"""
        high_quality_template = """# 高质量分析模板

你是一位专业的数据分析师，具有丰富的问题分析经验。

请对以下问题进行深入分析：

**分析主题**: {topic}
**复杂程度**: {complexity}

## 分析要求
1. 请具体分析问题的核心要素
2. 必须提供至少3个不同角度的分析
3. 确保分析的逻辑性和准确性

## 输出格式
```json
{
  "analysis": "详细分析结果",
  "confidence": 0.85
}
```

请开始分析：
"""

        result = self.tester.test_output_quality(
            high_quality_template, "high_quality_test"
        )

        assert result["overall_score"] > 0.7
        assert result["structure_score"] > 0.6
        assert result["content_score"] > 0.5
        assert result["format_score"] > 0.7
        assert result["instruction_score"] > 0.7
        assert len(result["strengths"]) > len(result["issues"])

    def test_low_quality_template(self):
        """Test with a low-quality template"""
        low_quality_template = """分析问题。

可能需要考虑一些因素。
也许要提供结果。
"""

        result = self.tester.test_output_quality(
            low_quality_template, "low_quality_test"
        )

        assert result["overall_score"] < 0.5
        assert len(result["issues"]) > len(result["strengths"])

    def test_decomposition_template_specific_checks(self):
        """Test decomposition template specific quality checks"""
        decomp_template = """# 问题分解模板

你是分解专家，请分解问题：

**问题**: {topic}

## 分解策略
使用系统性分解方法。

## 输出格式
```json
{
  "sub_questions": ["问题1", "问题2"]
}
```
"""

        result = self.tester.test_output_quality(decomp_template, "decomposition_test")

        # Should detect decomposition-specific elements
        assert any("strategy" in strength.lower() for strength in result["strengths"])
        assert any("json" in strength.lower() for strength in result["strengths"])


class TestTemplateInstructionClarityTester:
    """Test the instruction clarity testing functionality"""

    def setup_method(self):
        self.tester = TemplateInstructionClarityTester()

    def test_clear_instructions(self):
        """Test template with clear instructions"""
        clear_template = """# 清晰指令模板

请具体分析以下问题，确保详细说明每个步骤。

## 要求
1. 必须提供至少3个分析角度
2. 确保每个角度不少于100字
3. 需要包含具体的数据支持

## 输出格式
请按照JSON格式输出结果。

请开始分析：
"""

        result = self.tester.test_instruction_clarity(clear_template)

        assert result["overall_clarity_score"] > 0.7
        assert result["language_clarity_score"] > 0.7
        assert result["structure_clarity_score"] > 0.7
        assert result["requirement_clarity_score"] > 0.7
        assert len(result["clarity_strengths"]) > len(result["clarity_issues"])

    def test_vague_instructions(self):
        """Test template with vague instructions"""
        vague_template = """# 模糊指令模板

可能需要分析一些问题，也许要考虑相关因素。
大概要提供一些观点。
适当包含一些数据。
"""

        result = self.tester.test_instruction_clarity(vague_template)

        assert result["overall_clarity_score"] < 0.6
        assert len(result["clarity_issues"]) > len(result["clarity_strengths"])

    def test_language_clarity_scoring(self):
        """Test language clarity scoring mechanism"""
        specific_template = """# 具体模板

请明确分析问题，确保详细说明，必须准确完整。
"""

        vague_template = """# 模糊模板

可能需要分析，也许要考虑，大概要提供，似乎应该包含。
"""

        specific_result = self.tester.test_instruction_clarity(specific_template)
        vague_result = self.tester.test_instruction_clarity(vague_template)

        assert (
            specific_result["language_clarity_score"]
            > vague_result["language_clarity_score"]
        )


class TestTemplateEffectTester:
    """Test the main template effect testing functionality"""

    def setup_method(self):
        self.tester = TemplateEffectTester()

    def test_comprehensive_template_testing(self):
        """Test comprehensive template effectiveness testing"""
        test_template = """# 综合测试模板

你是一位专业的分析师，请对以下问题进行深入分析：

**问题**: {topic}
**复杂度**: {complexity}

## 分析要求
1. 请具体分析问题的核心要素
2. 必须提供至少3个不同角度的分析
3. 确保分析的逻辑性和准确性

## 输出格式
```json
{
  "analysis": "详细分析结果",
  "confidence": 0.85
}
```

请开始分析：
"""

        result = self.tester.test_template_effectiveness(
            test_template, "comprehensive_test"
        )

        assert isinstance(result, TemplateEffectTestResult)
        assert result.template_name == "comprehensive_test"
        assert 0 <= result.effectiveness_score <= 1
        assert 0 <= result.output_quality_score <= 1
        assert 0 <= result.instruction_clarity_score <= 1
        assert "output_quality" in result.test_results
        assert "instruction_clarity" in result.test_results
        assert "validation_result" in result.test_results
        assert isinstance(result.issues, list)
        assert isinstance(result.recommendations, list)

    def test_effectiveness_score_calculation(self):
        """Test effectiveness score calculation"""
        good_template = """# 优秀模板

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

请开始分析：
"""

        poor_template = """分析{topic}"""

        good_result = self.tester.test_template_effectiveness(
            good_template, "good_test"
        )
        poor_result = self.tester.test_template_effectiveness(
            poor_template, "poor_test"
        )

        assert good_result.effectiveness_score > poor_result.effectiveness_score
        assert good_result.effectiveness_score > 0.7
        assert poor_result.effectiveness_score < 0.5

    def test_recommendation_generation(self):
        """Test recommendation generation"""
        template_with_issues = """# 有问题的模板

分析问题，可能需要考虑一些因素。
"""

        result = self.tester.test_template_effectiveness(
            template_with_issues, "issues_test"
        )

        assert len(result.recommendations) > 0
        assert len(result.issues) > 0

        # Should have specific recommendations
        rec_text = " ".join(result.recommendations).lower()
        assert any(
            keyword in rec_text
            for keyword in ["structure", "clarity", "specific", "format"]
        )


class TestTemplateEffectIntegration:
    """Integration tests with existing template files"""

    def setup_method(self):
        self.tester = TemplateEffectTester()
        self.template_manager = TemplateManager("templates")

    def test_existing_templates_effectiveness(self):
        """Test effectiveness of existing template files"""
        templates_dir = Path("templates")

        if not templates_dir.exists():
            pytest.skip("Templates directory not found")

        results = self.tester.test_all_templates("templates")

        assert len(results) > 0, "Should find template files"

        # All templates should have reasonable effectiveness scores
        for name, result in results.items():
            assert isinstance(result, TemplateEffectTestResult)
            assert 0 <= result.effectiveness_score <= 1
            assert result.template_name == name

            print(
                f"Template {name}: Effectiveness {result.effectiveness_score:.2f}, "
                f"Quality {result.output_quality_score:.2f}, "
                f"Clarity {result.instruction_clarity_score:.2f}"
            )

        # Filter out stub templates (templates with very low word count)
        complete_templates = {
            name: result
            for name, result in results.items()
            if result.test_results.get("validation_result", {})
            .get("metrics", {})
            .get("word_count", 0)
            > 20
        }

        if complete_templates:
            # At least 70% of complete templates should have decent effectiveness
            good_templates = sum(
                1 for r in complete_templates.values() if r.effectiveness_score >= 0.6
            )
            total_complete = len(complete_templates)

            assert (
                good_templates / total_complete >= 0.7
            ), f"Too many low-effectiveness complete templates: {good_templates}/{total_complete}"
        else:
            # If no complete templates, just ensure we found some templates
            assert len(results) > 0, "Should find at least some template files"

    def test_effectiveness_report_generation(self):
        """Test effectiveness report generation"""
        templates_dir = Path("templates")

        if not templates_dir.exists():
            pytest.skip("Templates directory not found")

        results = self.tester.test_all_templates("templates")
        report = self.tester.generate_effectiveness_report(results)

        assert "Template Effectiveness Testing Report" in report
        assert "Executive Summary" in report
        assert "Individual Template Results" in report
        assert "Average Effectiveness Score" in report

        # Should contain template names
        for template_name in results.keys():
            assert template_name in report

        print("Generated effectiveness report:")
        print(report[:1000] + "..." if len(report) > 1000 else report)

    def test_template_manager_integration(self):
        """Test integration with template manager"""
        template_names = self.template_manager.list_templates()

        if not template_names:
            pytest.skip("No templates found in template manager")

        # Test a few templates from the manager
        for template_name in template_names[:3]:  # Test first 3 templates
            try:
                template_content = self.template_manager.get_template(
                    template_name, params={}, use_default_if_missing=True
                )

                # Get original template content for testing
                original_content = self.template_manager.cache.get(
                    template_name, template_content
                )

                result = self.tester.test_template_effectiveness(
                    original_content, template_name
                )

                assert isinstance(result, TemplateEffectTestResult)
                assert result.template_name == template_name

                print(f"✓ Template manager integration test passed for {template_name}")
                print(f"  Effectiveness: {result.effectiveness_score:.2f}")

            except Exception as e:
                pytest.fail(
                    f"Template manager integration failed for {template_name}: {e}"
                )


def run_template_effect_tests():
    """Run all template effect tests"""
    test_classes = [
        TestTemplateOutputQualityTester,
        TestTemplateInstructionClarityTester,
        TestTemplateEffectTester,
        TestTemplateEffectIntegration,
    ]

    passed = 0
    failed = 0

    for test_class in test_classes:
        test_instance = test_class()
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
    print(f"TEMPLATE EFFECT TEST RESULTS")
    print(f"{'='*60}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")

    if failed == 0:
        print("🎉 All template effect tests passed!")
    else:
        print(f"⚠️  {failed} test(s) failed")

    return failed == 0


if __name__ == "__main__":
    success = run_template_effect_tests()
    exit(0 if success else 1)
