"""
Template Effect Validator - 模板效果验证器

Provides automated validation of template effectiveness, output quality assessment,
and instruction clarity testing for the deep thinking engine templates.

This module implements comprehensive testing for template effectiveness
and provides automated quality assurance for prompt templates.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from .template_validator import TemplateValidator, ValidationSeverity


@dataclass
class TemplateEffectMetrics:
    """Metrics for template effectiveness"""
    template_name: str
    effectiveness_score: float  # 0.0 to 1.0
    output_quality_score: float  # 0.0 to 1.0
    instruction_clarity_score: float  # 0.0 to 1.0
    structure_completeness: float  # 0.0 to 1.0
    content_relevance: float  # 0.0 to 1.0
    format_compliance: float  # 0.0 to 1.0
    instruction_following: float  # 0.0 to 1.0
    language_clarity: float  # 0.0 to 1.0
    requirement_clarity: float  # 0.0 to 1.0
    parameter_usage: float  # 0.0 to 1.0
    test_timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TemplateEffectReport:
    """Comprehensive template effect testing report"""
    total_templates: int
    tested_templates: int
    average_effectiveness: float
    high_quality_count: int  # >= 0.8
    medium_quality_count: int  # 0.6-0.8
    low_quality_count: int  # < 0.6
    template_metrics: Dict[str, TemplateEffectMetrics] = field(default_factory=dict)
    issues_summary: Dict[str, int] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    test_timestamp: datetime = field(default_factory=datetime.now)


class TemplateEffectValidator:
    """Main validator for template effectiveness and quality"""
    
    def __init__(self):
        self.template_validator = TemplateValidator()
        
        # Scoring weights for different aspects
        self.effectiveness_weights = {
            'output_quality': 0.4,
            'instruction_clarity': 0.3,
            'validation_score': 0.3
        }
        
        self.quality_weights = {
            'structure_completeness': 0.25,
            'content_relevance': 0.25,
            'format_compliance': 0.25,
            'instruction_following': 0.25
        }
        
        self.clarity_weights = {
            'language_clarity': 0.4,
            'requirement_clarity': 0.4,
            'parameter_usage': 0.2
        }
    
    def validate_template_effect(self, template_content: str, template_name: str) -> TemplateEffectMetrics:
        """Validate the effectiveness of a single template"""
        
        # Run standard validation
        validation_result = self.template_validator.validate_template(template_content, template_name)
        
        # Test output quality components
        structure_score = self._test_structure_completeness(template_content, template_name)
        content_score = self._test_content_relevance(template_content, template_name)
        format_score = self._test_format_compliance(template_content)
        instruction_score = self._test_instruction_following(template_content)
        
        # Calculate output quality score
        output_quality_score = (
            structure_score * self.quality_weights['structure_completeness'] +
            content_score * self.quality_weights['content_relevance'] +
            format_score * self.quality_weights['format_compliance'] +
            instruction_score * self.quality_weights['instruction_following']
        )
        
        # Test instruction clarity components
        language_clarity = self._test_language_clarity(template_content)
        requirement_clarity = self._test_requirement_clarity(template_content)
        parameter_usage = self._test_parameter_usage(template_content)
        
        # Calculate instruction clarity score
        instruction_clarity_score = (
            language_clarity * self.clarity_weights['language_clarity'] +
            requirement_clarity * self.clarity_weights['requirement_clarity'] +
            parameter_usage * self.clarity_weights['parameter_usage']
        )
        
        # Calculate overall effectiveness score
        effectiveness_score = (
            output_quality_score * self.effectiveness_weights['output_quality'] +
            instruction_clarity_score * self.effectiveness_weights['instruction_clarity'] +
            validation_result.overall_score * self.effectiveness_weights['validation_score']
        )
        
        return TemplateEffectMetrics(
            template_name=template_name,
            effectiveness_score=effectiveness_score,
            output_quality_score=output_quality_score,
            instruction_clarity_score=instruction_clarity_score,
            structure_completeness=structure_score,
            content_relevance=content_score,
            format_compliance=format_score,
            instruction_following=instruction_score,
            language_clarity=language_clarity,
            requirement_clarity=requirement_clarity,
            parameter_usage=parameter_usage
        )
    
    def _test_structure_completeness(self, content: str, template_name: str) -> float:
        """Test template structure completeness"""
        score = 0.0
        
        # Basic structural elements
        has_title = bool(re.search(r'^#\s+.+', content, re.MULTILINE))
        has_context = bool(re.search(r'你是|作为|扮演', content))
        has_task = bool(re.search(r'请|需要|要求|任务', content))
        has_output_format = bool(re.search(r'输出格式|JSON|格式规范', content))
        
        basic_score = sum([has_title, has_context, has_task, has_output_format]) / 4
        score += basic_score * 0.6
        
        # Template-specific structure
        if 'decomposition' in template_name:
            has_strategy = bool(re.search(r'分解策略|分解方法', content))
            has_json_example = bool(re.search(r'```json', content))
            specific_score = sum([has_strategy, has_json_example]) / 2
            score += specific_score * 0.4
        elif 'evidence' in template_name:
            has_search_strategy = bool(re.search(r'搜索策略|证据收集', content))
            has_quality_criteria = bool(re.search(r'可信度|质量要求', content))
            specific_score = sum([has_search_strategy, has_quality_criteria]) / 2
            score += specific_score * 0.4
        else:
            # For other templates, just use basic score
            score = basic_score
        
        return max(0.0, min(1.0, score))
    
    def _test_content_relevance(self, content: str, template_name: str) -> float:
        """Test content relevance and focus"""
        score = 0.0
        
        # Check specificity vs vagueness
        specific_terms = len(re.findall(r'必须|应该|确保|至少|不少于|\d+个', content))
        vague_terms = len(re.findall(r'可能|也许|大概|适当|合理|相关', content))
        
        specificity_ratio = specific_terms / max(vague_terms, 1)
        if specificity_ratio > 2.0:
            score += 0.4
        elif specificity_ratio > 1.0:
            score += 0.3
        else:
            score += 0.1
        
        # Check for examples and guidance
        has_examples = bool(re.search(r'例如|比如|示例|样例', content))
        has_steps = bool(re.search(r'步骤|流程|过程', content))
        
        guidance_score = sum([has_examples, has_steps]) / 2
        score += guidance_score * 0.3
        
        # Check content density (not too sparse, not too verbose)
        word_count = len(content.split())
        if 100 <= word_count <= 800:
            score += 0.3
        elif 50 <= word_count < 100 or 800 < word_count <= 1200:
            score += 0.2
        else:
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _test_format_compliance(self, content: str) -> float:
        """Test format compliance and consistency"""
        score = 1.0
        
        # Check JSON format blocks
        json_blocks = re.findall(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
        
        for json_block in json_blocks:
            try:
                # Clean and validate JSON structure
                cleaned_json = re.sub(r'//.*', '', json_block)
                cleaned_json = re.sub(r'"[^"]*\{[^}]+\}[^"]*"', '"placeholder"', cleaned_json)
                json.loads(cleaned_json)
            except json.JSONDecodeError:
                if not ('{' in json_block and '}' in json_block):
                    score -= 0.2
        
        # Check heading structure
        headings = re.findall(r'^(#+)\s+(.+)', content, re.MULTILINE)
        if headings:
            levels = [len(h[0]) for h in headings]
            if max(levels) - min(levels) > 2:
                score -= 0.1
        else:
            score -= 0.2
        
        # Check for proper list formatting
        has_lists = bool(re.search(r'^\d+\.\s+|^[-*]\s+', content, re.MULTILINE))
        if not has_lists:
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _test_instruction_following(self, content: str) -> float:
        """Test instruction clarity and followability"""
        score = 0.0
        
        # Check for action verbs
        action_verbs = len(re.findall(r'请|需要|要求|执行|分析|评估|生成|创建|识别|检测', content))
        if action_verbs >= 5:
            score += 0.3
        elif action_verbs >= 3:
            score += 0.2
        else:
            score += 0.1
        
        # Check for specific requirements
        specific_reqs = len(re.findall(r'必须|应该|确保|至少|不少于|不超过|\d+个|\d+分', content))
        if specific_reqs >= 3:
            score += 0.3
        elif specific_reqs >= 2:
            score += 0.2
        else:
            score += 0.1
        
        # Check for validation instructions
        has_validation = bool(re.search(r'检查|验证|确认|核实', content))
        if has_validation:
            score += 0.2
        
        # Check for error handling
        has_error_handling = bool(re.search(r'如果|当|错误|问题|异常', content))
        if has_error_handling:
            score += 0.2
        
        return max(0.0, min(1.0, score))
    
    def _test_language_clarity(self, content: str) -> float:
        """Test language clarity and readability"""
        score = 0.0
        
        # Check clarity indicators
        clear_terms = ['具体', '明确', '清晰', '详细', '准确', '完整']
        vague_terms = ['可能', '也许', '大概', '或许', '似乎', '好像']
        
        clear_count = sum(content.count(word) for word in clear_terms)
        vague_count = sum(content.count(word) for word in vague_terms)
        
        clarity_ratio = clear_count / max(vague_count, 1)
        if clarity_ratio > 3.0:
            score += 0.5
        elif clarity_ratio > 1.5:
            score += 0.4
        else:
            score += 0.2
        
        # Check sentence complexity
        sentences = re.split(r'[。！？]', content)
        avg_length = sum(len(s.split()) for s in sentences if s.strip()) / max(len([s for s in sentences if s.strip()]), 1)
        
        if avg_length < 20:
            score += 0.3
        elif avg_length < 30:
            score += 0.2
        else:
            score += 0.1
        
        # Check terminology consistency
        key_terms = re.findall(r'(模板|分析|评估|生成|输出|格式)', content)
        if key_terms and len(set(key_terms)) / len(key_terms) > 0.3:
            score += 0.2
        
        return max(0.0, min(1.0, score))
    
    def _test_requirement_clarity(self, content: str) -> float:
        """Test requirement clarity and specificity"""
        score = 0.0
        
        # Check for explicit requirements
        explicit_reqs = len(re.findall(r'必须|应该|需要|要求|确保', content))
        if explicit_reqs >= 5:
            score += 0.4
        elif explicit_reqs >= 3:
            score += 0.3
        else:
            score += 0.1
        
        # Check for measurable criteria
        measurable = len(re.findall(r'\d+个|\d+分|至少|不少于|不超过', content))
        if measurable >= 3:
            score += 0.3
        elif measurable >= 2:
            score += 0.2
        else:
            score += 0.1
        
        # Check for output format specification
        has_format = bool(re.search(r'输出格式|JSON|格式规范', content))
        if has_format:
            score += 0.3
        
        return max(0.0, min(1.0, score))
    
    def _test_parameter_usage(self, content: str) -> float:
        """Test parameter usage effectiveness"""
        score = 0.0
        
        # Find parameters
        parameters = re.findall(r'\{([^{}]+)\}', content)
        
        if not parameters:
            # No parameters is okay for some templates
            score = 0.7
        else:
            # Check parameter quality
            param_names = [p.split('|')[0].strip() for p in parameters]
            
            # Check for meaningful parameter names
            meaningful_params = [p for p in param_names if len(p) > 2 and p not in ['a', 'b', 'c']]
            if len(meaningful_params) == len(param_names):
                score += 0.4
            else:
                score += 0.2
            
            # Check for parameter diversity
            unique_params = len(set(param_names))
            if unique_params >= 3:
                score += 0.3
            elif unique_params >= 2:
                score += 0.2
            else:
                score += 0.1
            
            # Check parameter integration
            param_context = sum(1 for p in param_names if p in content.replace('{', '').replace('}', ''))
            if param_context > 0:
                score += 0.3
        
        return max(0.0, min(1.0, score))
    
    def validate_all_templates(self, templates_dir: str) -> TemplateEffectReport:
        """Validate effectiveness of all templates in directory"""
        templates_path = Path(templates_dir)
        
        if not templates_path.exists():
            return TemplateEffectReport(
                total_templates=0,
                tested_templates=0,
                average_effectiveness=0.0,
                high_quality_count=0,
                medium_quality_count=0,
                low_quality_count=0
            )
        
        template_metrics = {}
        issues_summary = {}
        
        # Process all template files
        for template_file in templates_path.glob("*.tmpl"):
            try:
                content = template_file.read_text(encoding='utf-8')
                
                # Skip very short templates (likely stubs)
                if len(content.split()) < 10:
                    continue
                
                metrics = self.validate_template_effect(content, template_file.stem)
                template_metrics[template_file.stem] = metrics
                
            except Exception as e:
                # Track issues
                issue_type = type(e).__name__
                issues_summary[issue_type] = issues_summary.get(issue_type, 0) + 1
        
        # Calculate summary statistics
        if template_metrics:
            effectiveness_scores = [m.effectiveness_score for m in template_metrics.values()]
            average_effectiveness = sum(effectiveness_scores) / len(effectiveness_scores)
            
            high_quality_count = sum(1 for score in effectiveness_scores if score >= 0.8)
            medium_quality_count = sum(1 for score in effectiveness_scores if 0.6 <= score < 0.8)
            low_quality_count = sum(1 for score in effectiveness_scores if score < 0.6)
        else:
            average_effectiveness = 0.0
            high_quality_count = medium_quality_count = low_quality_count = 0
        
        # Generate recommendations
        recommendations = self._generate_global_recommendations(template_metrics)
        
        return TemplateEffectReport(
            total_templates=len(list(templates_path.glob("*.tmpl"))),
            tested_templates=len(template_metrics),
            average_effectiveness=average_effectiveness,
            high_quality_count=high_quality_count,
            medium_quality_count=medium_quality_count,
            low_quality_count=low_quality_count,
            template_metrics=template_metrics,
            issues_summary=issues_summary,
            recommendations=recommendations
        )
    
    def _generate_global_recommendations(self, template_metrics: Dict[str, TemplateEffectMetrics]) -> List[str]:
        """Generate global recommendations based on all template metrics"""
        recommendations = []
        
        if not template_metrics:
            return ["No templates found for analysis"]
        
        # Analyze common issues
        low_structure_count = sum(1 for m in template_metrics.values() if m.structure_completeness < 0.7)
        low_clarity_count = sum(1 for m in template_metrics.values() if m.language_clarity < 0.7)
        low_format_count = sum(1 for m in template_metrics.values() if m.format_compliance < 0.7)
        
        total_templates = len(template_metrics)
        
        if low_structure_count / total_templates > 0.3:
            recommendations.append("Many templates lack proper structure - focus on improving section organization")
        
        if low_clarity_count / total_templates > 0.3:
            recommendations.append("Language clarity needs improvement across templates - use more specific terms")
        
        if low_format_count / total_templates > 0.3:
            recommendations.append("Format compliance issues detected - review JSON examples and heading structure")
        
        # Quality distribution recommendations
        high_quality_ratio = sum(1 for m in template_metrics.values() if m.effectiveness_score >= 0.8) / total_templates
        
        if high_quality_ratio < 0.5:
            recommendations.append("Less than 50% of templates meet high quality standards - consider template review")
        elif high_quality_ratio > 0.8:
            recommendations.append("Excellent template quality overall - maintain current standards")
        
        return recommendations
    
    def generate_detailed_report(self, report: TemplateEffectReport) -> str:
        """Generate detailed text report"""
        lines = [
            "# Template Effectiveness Validation Report",
            f"Generated: {report.test_timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            f"- Total Templates: {report.total_templates}",
            f"- Tested Templates: {report.tested_templates}",
            f"- Average Effectiveness: {report.average_effectiveness:.3f}",
            "",
            f"- High Quality (≥0.8): {report.high_quality_count} ({report.high_quality_count/max(report.tested_templates,1)*100:.1f}%)",
            f"- Medium Quality (0.6-0.8): {report.medium_quality_count} ({report.medium_quality_count/max(report.tested_templates,1)*100:.1f}%)",
            f"- Low Quality (<0.6): {report.low_quality_count} ({report.low_quality_count/max(report.tested_templates,1)*100:.1f}%)",
            ""
        ]
        
        if report.recommendations:
            lines.extend([
                "## Recommendations",
                ""
            ])
            for rec in report.recommendations:
                lines.append(f"- {rec}")
            lines.append("")
        
        if report.template_metrics:
            lines.extend([
                "## Individual Template Results",
                ""
            ])
            
            # Sort by effectiveness score
            sorted_metrics = sorted(report.template_metrics.items(), 
                                  key=lambda x: x[1].effectiveness_score, reverse=True)
            
            for template_name, metrics in sorted_metrics:
                status = "🟢" if metrics.effectiveness_score >= 0.8 else "🟡" if metrics.effectiveness_score >= 0.6 else "🔴"
                
                lines.extend([
                    f"### {status} {template_name}",
                    f"- Effectiveness: {metrics.effectiveness_score:.3f}",
                    f"- Output Quality: {metrics.output_quality_score:.3f}",
                    f"- Instruction Clarity: {metrics.instruction_clarity_score:.3f}",
                    f"- Structure: {metrics.structure_completeness:.3f}",
                    f"- Content: {metrics.content_relevance:.3f}",
                    f"- Format: {metrics.format_compliance:.3f}",
                    f"- Language: {metrics.language_clarity:.3f}",
                    ""
                ])
        
        if report.issues_summary:
            lines.extend([
                "## Issues Summary",
                ""
            ])
            for issue_type, count in report.issues_summary.items():
                lines.append(f"- {issue_type}: {count}")
            lines.append("")
        
        return "\n".join(lines)


def validate_template_effects(templates_dir: str = "templates") -> TemplateEffectReport:
    """Convenience function to validate all template effects"""
    validator = TemplateEffectValidator()
    return validator.validate_all_templates(templates_dir)


def generate_template_effect_report(templates_dir: str = "templates", output_file: Optional[str] = None) -> str:
    """Generate and optionally save template effect report"""
    validator = TemplateEffectValidator()
    report = validator.validate_all_templates(templates_dir)
    report_text = validator.generate_detailed_report(report)
    
    if output_file:
        Path(output_file).write_text(report_text, encoding='utf-8')
    
    return report_text


if __name__ == "__main__":
    # Run template effect validation
    report = validate_template_effects()
    print(generate_template_effect_report())