"""
Template Quality Validation System

Provides comprehensive validation for template format, content quality,
instruction clarity, and effectiveness testing.
"""

import json
import re
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from enum import Enum
from pathlib import Path


class ValidationSeverity(Enum):
    """Severity levels for validation issues"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Represents a validation issue found in a template"""

    severity: ValidationSeverity
    category: str
    message: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    suggestion: Optional[str] = None
    context: Optional[str] = None


@dataclass
class TemplateValidationResult:
    """Result of template validation"""

    template_name: str
    is_valid: bool
    overall_score: float  # 0.0 to 1.0
    issues: List[ValidationIssue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)


class TemplateFormatValidator:
    """Validates template format and structure"""

    def __init__(self):
        self.required_sections = {
            "title": r"^#\s+.+",
            "instructions": r"你是|请|需要|要求",
            "output_format": r"输出格式|JSON|格式规范",
        }

        self.parameter_pattern = r"\{([^{}]+)\}"
        self.json_block_pattern = r"```json\s*\n(.*?)\n```"

    def validate_format(
        self, template_content: str, template_name: str
    ) -> List[ValidationIssue]:
        """Validate template format and structure"""
        issues = []
        lines = template_content.split("\n")

        # Check for required sections
        issues.extend(self._check_required_sections(template_content, template_name))

        # Check parameter usage
        issues.extend(self._check_parameter_usage(template_content))

        # Check JSON format blocks
        issues.extend(self._check_json_format_blocks(template_content))

        # Check line length and readability
        issues.extend(self._check_readability(lines))

        # Check for common formatting issues
        issues.extend(self._check_formatting_issues(lines))

        return issues

    def _check_required_sections(
        self, content: str, template_name: str
    ) -> List[ValidationIssue]:
        """Check for required template sections"""
        issues = []

        # Check for title
        if not re.search(r"^#\s+.+", content, re.MULTILINE):
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="structure",
                    message="Template missing title (should start with # followed by title)",
                    suggestion="Add a clear title at the beginning: # Template Title",
                )
            )

        # Check for instructions
        if not re.search(r"你是|请|需要|要求|执行|分析", content):
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="structure",
                    message="Template may be missing clear instructions",
                    suggestion="Add clear instructions for what the user should do",
                )
            )

        # Check for output format specification
        if template_name not in [
            "bias_detection",
            "innovation",
            "reflection",
        ]:  # Simple templates
            if not re.search(r"输出格式|JSON|格式规范|输出要求", content):
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="structure",
                        message="Template may be missing output format specification",
                        suggestion="Add clear output format requirements",
                    )
                )

        return issues

    def _check_parameter_usage(self, content: str) -> List[ValidationIssue]:
        """Check parameter usage in template"""
        issues = []

        # Find all parameters
        parameters = re.findall(self.parameter_pattern, content)

        if not parameters:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    category="parameters",
                    message="Template contains no parameters - verify if this is intentional",
                    suggestion="Consider adding parameters for dynamic content",
                )
            )

        # Check for common parameter issues
        for param in parameters:
            # Check for malformed parameters
            if "|" in param and not re.match(r"^[^|]+(\|[^|]*)?(\|[^|]*)?$", param):
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category="parameters",
                        message=f"Malformed parameter syntax: {{{param}}}",
                        suggestion="Use format: {param}, {param|formatter}, or {param|formatter|default}",
                    )
                )

            # Check for empty parameter names
            param_name = param.split("|")[0].strip()
            if not param_name:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category="parameters",
                        message="Empty parameter name found",
                        suggestion="Ensure all parameters have valid names",
                    )
                )

        # Check for duplicate parameters
        param_names = [p.split("|")[0].strip() for p in parameters]
        duplicates = set([p for p in param_names if param_names.count(p) > 1])
        for dup in duplicates:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    category="parameters",
                    message=f"Parameter '{dup}' used multiple times",
                    suggestion="Multiple usage is fine, but verify it's intentional",
                )
            )

        return issues

    def _check_json_format_blocks(self, content: str) -> List[ValidationIssue]:
        """Check JSON format blocks in template"""
        issues = []

        json_blocks = re.findall(self.json_block_pattern, content, re.DOTALL)

        for i, json_block in enumerate(json_blocks):
            try:
                # Try to parse as JSON (ignoring comments)
                cleaned_json = re.sub(r"//.*", "", json_block)  # Remove comments
                json.loads(cleaned_json)
            except json.JSONDecodeError as e:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="json_format",
                        message=f"JSON block {i+1} contains invalid JSON: {str(e)}",
                        suggestion="Ensure JSON examples are valid or clearly marked as templates",
                    )
                )

        return issues

    def _check_readability(self, lines: List[str]) -> List[ValidationIssue]:
        """Check template readability"""
        issues = []

        for i, line in enumerate(lines, 1):
            # Check line length
            if len(line) > 120:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        category="readability",
                        message=f"Line {i} is very long ({len(line)} characters)",
                        line_number=i,
                        suggestion="Consider breaking long lines for better readability",
                    )
                )

            # Check for excessive whitespace
            if line.strip() != line and line.endswith(" " * 3):
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        category="formatting",
                        message=f"Line {i} has trailing whitespace",
                        line_number=i,
                        suggestion="Remove trailing whitespace",
                    )
                )

        return issues

    def _check_formatting_issues(self, lines: List[str]) -> List[ValidationIssue]:
        """Check for common formatting issues"""
        issues = []

        # Check for inconsistent heading levels
        heading_levels = []
        for i, line in enumerate(lines, 1):
            if line.strip().startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                heading_levels.append((i, level))

        # Check for heading level jumps
        for i in range(1, len(heading_levels)):
            prev_level = heading_levels[i - 1][1]
            curr_level = heading_levels[i][1]
            curr_line = heading_levels[i][0]

            if curr_level > prev_level + 1:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        category="formatting",
                        message=f"Heading level jump at line {curr_line} (from {prev_level} to {curr_level})",
                        line_number=curr_line,
                        suggestion="Use consecutive heading levels for better structure",
                    )
                )

        return issues


class TemplateContentValidator:
    """Validates template content quality and clarity"""

    def __init__(self):
        self.clarity_indicators = {
            "positive": [
                "具体",
                "明确",
                "清晰",
                "详细",
                "准确",
                "完整",
                "请",
                "需要",
                "要求",
                "确保",
                "必须",
                "应该",
                "步骤",
                "方法",
                "策略",
                "要求",
                "标准",
                "规范",
            ],
            "negative": [
                "可能",
                "也许",
                "大概",
                "或许",
                "似乎",
                "好像",
                "模糊",
                "不清楚",
                "不确定",
                "随意",
                "任意",
            ],
        }

        self.instruction_patterns = {
            "action_verbs": r"(请|需要|要求|执行|分析|评估|生成|创建|识别|检测|收集|整理)",
            "specific_requirements": r"(必须|应该|确保|至少|不少于|不超过|\d+个|\d+分)",
            "format_specifications": r"(JSON|格式|输出|结构|模板|示例)",
        }

    def validate_content(
        self, template_content: str, template_name: str
    ) -> List[ValidationIssue]:
        """Validate template content quality"""
        issues = []

        # Check instruction clarity
        issues.extend(self._check_instruction_clarity(template_content))

        # Check specificity
        issues.extend(self._check_specificity(template_content))

        # Check completeness
        issues.extend(self._check_completeness(template_content, template_name))

        # Check language quality
        issues.extend(self._check_language_quality(template_content))

        return issues

    def _check_instruction_clarity(self, content: str) -> List[ValidationIssue]:
        """Check clarity of instructions"""
        issues = []

        # Count clarity indicators
        positive_count = sum(
            content.count(word) for word in self.clarity_indicators["positive"]
        )
        negative_count = sum(
            content.count(word) for word in self.clarity_indicators["negative"]
        )

        clarity_ratio = positive_count / max(negative_count, 1)

        if clarity_ratio < 2.0:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="clarity",
                    message=f"Instructions may lack clarity (clarity ratio: {clarity_ratio:.1f})",
                    suggestion="Use more specific and definitive language in instructions",
                )
            )

        # Check for action verbs
        action_verbs = re.findall(self.instruction_patterns["action_verbs"], content)
        if len(action_verbs) < 3:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    category="clarity",
                    message="Few action verbs found in instructions",
                    suggestion="Use clear action verbs to guide user behavior",
                )
            )

        return issues

    def _check_specificity(self, content: str) -> List[ValidationIssue]:
        """Check specificity of requirements"""
        issues = []

        # Check for specific requirements
        specific_reqs = re.findall(
            self.instruction_patterns["specific_requirements"], content
        )

        if len(specific_reqs) < 2:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    category="specificity",
                    message="Template may lack specific requirements",
                    suggestion="Add specific requirements (e.g., minimum number of items, scoring criteria)",
                )
            )

        # Check for vague language
        vague_patterns = [r"一些", r"几个", r"适当", r"合理", r"相关", r"重要"]
        vague_count = sum(
            len(re.findall(pattern, content)) for pattern in vague_patterns
        )

        if vague_count > 5:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="specificity",
                    message=f"Template contains vague language ({vague_count} instances)",
                    suggestion="Replace vague terms with specific requirements",
                )
            )

        return issues

    def _check_completeness(
        self, content: str, template_name: str
    ) -> List[ValidationIssue]:
        """Check template completeness"""
        issues = []

        # Check for essential components based on template type
        if "decomposition" in template_name:
            required_elements = ["分解", "子问题", "JSON", "关系"]
            missing = [elem for elem in required_elements if elem not in content]
            if missing:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="completeness",
                        message=f"Decomposition template missing elements: {', '.join(missing)}",
                        suggestion="Ensure all essential decomposition elements are included",
                    )
                )

        elif "evidence" in template_name:
            required_elements = ["证据", "搜索", "来源", "可信度"]
            missing = [elem for elem in required_elements if elem not in content]
            if missing:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="completeness",
                        message=f"Evidence template missing elements: {', '.join(missing)}",
                        suggestion="Ensure all essential evidence collection elements are included",
                    )
                )

        elif "bias" in template_name:
            required_elements = ["偏见", "检测", "认知", "分析"]
            missing = [elem for elem in required_elements if elem not in content]
            if missing:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="completeness",
                        message=f"Bias detection template missing elements: {', '.join(missing)}",
                        suggestion="Ensure all essential bias detection elements are included",
                    )
                )

        return issues

    def _check_language_quality(self, content: str) -> List[ValidationIssue]:
        """Check language quality and consistency"""
        issues = []

        # Check for mixed language styles
        formal_indicators = ["您", "请您", "敬请"]
        informal_indicators = ["你", "请你"]

        formal_count = sum(content.count(word) for word in formal_indicators)
        informal_count = sum(content.count(word) for word in informal_indicators)

        if formal_count > 0 and informal_count > 0:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    category="language",
                    message="Mixed formal and informal language detected",
                    suggestion="Use consistent language style throughout the template",
                )
            )

        # Check for repetitive phrases
        sentences = re.split(r"[。！？]", content)
        sentence_starts = [s.strip()[:10] for s in sentences if len(s.strip()) > 10]

        if len(sentence_starts) != len(set(sentence_starts)):
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    category="language",
                    message="Repetitive sentence patterns detected",
                    suggestion="Vary sentence structures for better readability",
                )
            )

        return issues


class TemplateEffectivenessValidator:
    """Validates template effectiveness through automated testing"""

    def __init__(self):
        self.test_parameters = {
            "topic": "如何提高学习效率",
            "complexity": "moderate",
            "focus": "学生群体",
            "domain_context": "教育",
            "sub_question": "什么是最有效的学习方法？",
            "keywords": ["学习方法", "效率", "记忆"],
            "content": "学习效率的研究表明...",
            "context": "在教育心理学领域...",
        }

    def validate_effectiveness(
        self, template_content: str, template_name: str
    ) -> List[ValidationIssue]:
        """Validate template effectiveness"""
        issues = []

        # Test parameter replacement
        issues.extend(self._test_parameter_replacement(template_content))

        # Test output structure
        issues.extend(self._test_output_structure(template_content, template_name))

        # Test instruction completeness
        issues.extend(self._test_instruction_completeness(template_content))

        return issues

    def _test_parameter_replacement(self, content: str) -> List[ValidationIssue]:
        """Test parameter replacement functionality"""
        issues = []

        # Find parameters in template
        parameters = re.findall(r"\{([^{}]+)\}", content)

        # Test with sample parameters
        try:
            test_content = content
            for param in parameters:
                param_name = param.split("|")[0].strip()
                if param_name in self.test_parameters:
                    test_value = self.test_parameters[param_name]
                    test_content = test_content.replace(f"{{{param}}}", str(test_value))

            # Check if any parameters remain unreplaced
            remaining_params = re.findall(r"\{([^{}]+)\}", test_content)
            if remaining_params:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="effectiveness",
                        message=f"Parameters not covered by test data: {remaining_params}",
                        suggestion="Ensure all parameters have appropriate test values",
                    )
                )

        except Exception as e:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="effectiveness",
                    message=f"Parameter replacement test failed: {str(e)}",
                    suggestion="Check parameter syntax and formatting",
                )
            )

        return issues

    def _test_output_structure(
        self, content: str, template_name: str
    ) -> List[ValidationIssue]:
        """Test expected output structure"""
        issues = []

        # Check for JSON output requirements
        if "JSON" in content or "json" in content:
            json_blocks = re.findall(r"```json\s*\n(.*?)\n```", content, re.DOTALL)

            if not json_blocks:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="effectiveness",
                        message="Template mentions JSON but provides no JSON example",
                        suggestion="Include a JSON example to guide output format",
                    )
                )
            else:
                # Validate JSON structure
                for i, json_block in enumerate(json_blocks):
                    try:
                        # Remove comments and parse
                        cleaned_json = re.sub(r"//.*", "", json_block)
                        parsed = json.loads(cleaned_json)

                        # Check for reasonable structure
                        if isinstance(parsed, dict) and len(parsed) < 2:
                            issues.append(
                                ValidationIssue(
                                    severity=ValidationSeverity.INFO,
                                    category="effectiveness",
                                    message=f"JSON example {i+1} has minimal structure",
                                    suggestion="Consider providing more comprehensive JSON examples",
                                )
                            )

                    except json.JSONDecodeError:
                        # This is expected for template JSON with placeholders
                        pass

        return issues

    def _test_instruction_completeness(self, content: str) -> List[ValidationIssue]:
        """Test instruction completeness"""
        issues = []

        # Check for essential instruction components
        instruction_components = {
            "context_setting": r"你是|作为|扮演",
            "task_description": r"请|需要|要求|任务",
            "input_specification": r"输入|给定|提供",
            "process_guidance": r"步骤|方法|流程|过程",
            "output_specification": r"输出|结果|格式|返回",
        }

        missing_components = []
        for component, pattern in instruction_components.items():
            if not re.search(pattern, content):
                missing_components.append(component)

        if len(missing_components) > 2:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="effectiveness",
                    message=f"Template may be missing instruction components: {', '.join(missing_components)}",
                    suggestion="Consider adding missing instruction components for clarity",
                )
            )

        return issues


class TemplateValidator:
    """Main template validator that orchestrates all validation types"""

    def __init__(self):
        self.format_validator = TemplateFormatValidator()
        self.content_validator = TemplateContentValidator()
        self.effectiveness_validator = TemplateEffectivenessValidator()

        # Scoring weights for different validation aspects
        self.scoring_weights = {"format": 0.3, "content": 0.4, "effectiveness": 0.3}

    def validate_template(
        self, template_content: str, template_name: str
    ) -> TemplateValidationResult:
        """Perform comprehensive template validation"""
        all_issues = []

        # Run all validators
        format_issues = self.format_validator.validate_format(
            template_content, template_name
        )
        content_issues = self.content_validator.validate_content(
            template_content, template_name
        )
        effectiveness_issues = self.effectiveness_validator.validate_effectiveness(
            template_content, template_name
        )

        all_issues.extend(format_issues)
        all_issues.extend(content_issues)
        all_issues.extend(effectiveness_issues)

        # Calculate scores
        format_score = self._calculate_category_score(format_issues)
        content_score = self._calculate_category_score(content_issues)
        effectiveness_score = self._calculate_category_score(effectiveness_issues)

        overall_score = (
            format_score * self.scoring_weights["format"]
            + content_score * self.scoring_weights["content"]
            + effectiveness_score * self.scoring_weights["effectiveness"]
        )

        # Determine if template is valid (no critical or error issues)
        is_valid = not any(
            issue.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR]
            for issue in all_issues
        )

        # Generate suggestions
        suggestions = self._generate_suggestions(all_issues, overall_score)

        # Compile metrics
        metrics = {
            "format_score": format_score,
            "content_score": content_score,
            "effectiveness_score": effectiveness_score,
            "total_issues": len(all_issues),
            "critical_issues": len(
                [i for i in all_issues if i.severity == ValidationSeverity.CRITICAL]
            ),
            "error_issues": len(
                [i for i in all_issues if i.severity == ValidationSeverity.ERROR]
            ),
            "warning_issues": len(
                [i for i in all_issues if i.severity == ValidationSeverity.WARNING]
            ),
            "info_issues": len(
                [i for i in all_issues if i.severity == ValidationSeverity.INFO]
            ),
            "parameter_count": len(re.findall(r"\{([^{}]+)\}", template_content)),
            "word_count": len(template_content.split()),
            "line_count": len(template_content.split("\n")),
        }

        return TemplateValidationResult(
            template_name=template_name,
            is_valid=is_valid,
            overall_score=overall_score,
            issues=all_issues,
            metrics=metrics,
            suggestions=suggestions,
        )

    def _calculate_category_score(self, issues: List[ValidationIssue]) -> float:
        """Calculate score for a category of issues"""
        if not issues:
            return 1.0

        # Penalty weights for different severity levels
        penalties = {
            ValidationSeverity.INFO: 0.05,
            ValidationSeverity.WARNING: 0.15,
            ValidationSeverity.ERROR: 0.4,
            ValidationSeverity.CRITICAL: 0.8,
        }

        total_penalty = sum(penalties.get(issue.severity, 0) for issue in issues)

        # Cap the penalty to avoid negative scores
        total_penalty = min(total_penalty, 1.0)

        return max(0.0, 1.0 - total_penalty)

    def _generate_suggestions(
        self, issues: List[ValidationIssue], overall_score: float
    ) -> List[str]:
        """Generate improvement suggestions based on validation results"""
        suggestions = []

        # Priority suggestions based on severity
        critical_issues = [
            i for i in issues if i.severity == ValidationSeverity.CRITICAL
        ]
        error_issues = [i for i in issues if i.severity == ValidationSeverity.ERROR]

        if critical_issues:
            suggestions.append(
                "🚨 Address critical issues immediately - template may not function correctly"
            )

        if error_issues:
            suggestions.append(
                "⚠️ Fix error-level issues to improve template reliability"
            )

        # Score-based suggestions
        if overall_score < 0.6:
            suggestions.append(
                "📝 Consider major revision - template needs significant improvement"
            )
        elif overall_score < 0.8:
            suggestions.append(
                "✏️ Template needs moderate improvements for better quality"
            )
        elif overall_score < 0.9:
            suggestions.append("🔧 Minor improvements would enhance template quality")
        else:
            suggestions.append(
                "✅ Template quality is excellent - only minor optimizations needed"
            )

        # Category-specific suggestions
        format_issues = [
            i for i in issues if i.category in ["structure", "formatting", "parameters"]
        ]
        content_issues = [
            i
            for i in issues
            if i.category in ["clarity", "specificity", "completeness"]
        ]
        effectiveness_issues = [i for i in issues if i.category == "effectiveness"]

        if len(format_issues) > 3:
            suggestions.append(
                "📋 Focus on improving template structure and formatting"
            )

        if len(content_issues) > 3:
            suggestions.append("📖 Enhance instruction clarity and content quality")

        if len(effectiveness_issues) > 2:
            suggestions.append("🎯 Improve template effectiveness and usability")

        return suggestions

    def validate_template_file(
        self, template_path: Union[str, Path]
    ) -> TemplateValidationResult:
        """Validate a template file"""
        template_path = Path(template_path)

        if not template_path.exists():
            return TemplateValidationResult(
                template_name=template_path.stem,
                is_valid=False,
                overall_score=0.0,
                issues=[
                    ValidationIssue(
                        severity=ValidationSeverity.CRITICAL,
                        category="file",
                        message=f"Template file not found: {template_path}",
                        suggestion="Ensure the template file exists and is accessible",
                    )
                ],
            )

        try:
            content = template_path.read_text(encoding="utf-8")
            return self.validate_template(content, template_path.stem)
        except Exception as e:
            return TemplateValidationResult(
                template_name=template_path.stem,
                is_valid=False,
                overall_score=0.0,
                issues=[
                    ValidationIssue(
                        severity=ValidationSeverity.CRITICAL,
                        category="file",
                        message=f"Error reading template file: {str(e)}",
                        suggestion="Check file encoding and permissions",
                    )
                ],
            )

    def validate_all_templates(
        self, templates_dir: Union[str, Path]
    ) -> Dict[str, TemplateValidationResult]:
        """Validate all templates in a directory"""
        templates_dir = Path(templates_dir)
        results = {}

        if not templates_dir.exists():
            return results

        for template_file in templates_dir.glob("*.tmpl"):
            result = self.validate_template_file(template_file)
            results[template_file.stem] = result

        return results

    def generate_validation_report(
        self, results: Dict[str, TemplateValidationResult]
    ) -> str:
        """Generate a comprehensive validation report"""
        if not results:
            return "No templates found for validation."

        report_lines = [
            "# Template Quality Validation Report",
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            "",
        ]

        # Overall statistics
        total_templates = len(results)
        valid_templates = sum(1 for r in results.values() if r.is_valid)
        avg_score = statistics.mean(r.overall_score for r in results.values())

        report_lines.extend(
            [
                f"- **Total Templates**: {total_templates}",
                f"- **Valid Templates**: {valid_templates} ({valid_templates/total_templates*100:.1f}%)",
                f"- **Average Quality Score**: {avg_score:.2f}/1.00",
                "",
            ]
        )

        # Top issues
        all_issues = []
        for result in results.values():
            all_issues.extend(result.issues)

        if all_issues:
            issue_categories = {}
            for issue in all_issues:
                category = issue.category
                if category not in issue_categories:
                    issue_categories[category] = 0
                issue_categories[category] += 1

            report_lines.extend(["## Most Common Issues", ""])

            for category, count in sorted(
                issue_categories.items(), key=lambda x: x[1], reverse=True
            )[:5]:
                report_lines.append(f"- **{category.title()}**: {count} issues")

            report_lines.append("")

        # Individual template results
        report_lines.extend(["## Individual Template Results", ""])

        for template_name, result in sorted(results.items()):
            status = "✅ Valid" if result.is_valid else "❌ Invalid"
            score_bar = "█" * int(result.overall_score * 10) + "░" * (
                10 - int(result.overall_score * 10)
            )

            report_lines.extend(
                [
                    f"### {template_name} {status}",
                    f"**Score**: {result.overall_score:.2f}/1.00 `{score_bar}`",
                    "",
                ]
            )

            if result.metrics:
                report_lines.extend(
                    [
                        "**Metrics**:",
                        f"- Issues: {result.metrics.get('total_issues', 0)} total "
                        f"({result.metrics.get('critical_issues', 0)} critical, "
                        f"{result.metrics.get('error_issues', 0)} errors, "
                        f"{result.metrics.get('warning_issues', 0)} warnings)",
                        f"- Parameters: {result.metrics.get('parameter_count', 0)}",
                        f"- Size: {result.metrics.get('word_count', 0)} words, {result.metrics.get('line_count', 0)} lines",
                        "",
                    ]
                )

            if result.suggestions:
                report_lines.extend(
                    [
                        "**Suggestions**:",
                        *[f"- {suggestion}" for suggestion in result.suggestions],
                        "",
                    ]
                )

            # Show top issues
            if result.issues:
                critical_and_errors = [
                    i
                    for i in result.issues
                    if i.severity
                    in [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR]
                ]
                if critical_and_errors:
                    report_lines.extend(
                        [
                            "**Critical Issues**:",
                            *[
                                f"- {issue.severity.value.upper()}: {issue.message}"
                                for issue in critical_and_errors[:3]
                            ],
                            "",
                        ]
                    )

            report_lines.append("---")
            report_lines.append("")

        return "\n".join(report_lines)


# Convenience function for quick validation
def validate_template_quick(
    template_content: str, template_name: str = "unknown"
) -> Dict[str, Any]:
    """Quick template validation with simplified output"""
    validator = TemplateValidator()
    result = validator.validate_template(template_content, template_name)

    return {
        "is_valid": result.is_valid,
        "score": result.overall_score,
        "issues_count": len(result.issues),
        "critical_issues": [
            i.message
            for i in result.issues
            if i.severity == ValidationSeverity.CRITICAL
        ],
        "suggestions": result.suggestions[:3],  # Top 3 suggestions
    }
