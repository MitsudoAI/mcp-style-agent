#!/usr/bin/env python3
"""
Template Effect Testing CLI

Command-line interface for testing template effectiveness and generating reports.
"""

import sys
import argparse
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from mcps.deep_thinking.templates.template_effect_validator import (
    TemplateEffectValidator,
    validate_template_effects,
    generate_template_effect_report
)


def main():
    parser = argparse.ArgumentParser(description="Test template effectiveness and generate reports")
    parser.add_argument(
        "--templates-dir", 
        default="templates",
        help="Directory containing template files (default: templates)"
    )
    parser.add_argument(
        "--output-file",
        help="Output file for the report (optional)"
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Check if templates directory exists
    templates_path = Path(args.templates_dir)
    if not templates_path.exists():
        print(f"❌ Templates directory not found: {args.templates_dir}")
        return 1
    
    print(f"🔍 Testing template effectiveness in: {args.templates_dir}")
    print("=" * 60)
    
    try:
        # Run template effect validation
        validator = TemplateEffectValidator()
        report = validator.validate_all_templates(args.templates_dir)
        
        # Print summary
        print(f"📊 TEMPLATE EFFECTIVENESS SUMMARY")
        print(f"Total Templates: {report.total_templates}")
        print(f"Tested Templates: {report.tested_templates}")
        print(f"Average Effectiveness: {report.average_effectiveness:.3f}")
        print()
        
        print(f"🟢 High Quality (≥0.8): {report.high_quality_count} ({report.high_quality_count/max(report.tested_templates,1)*100:.1f}%)")
        print(f"🟡 Medium Quality (0.6-0.8): {report.medium_quality_count} ({report.medium_quality_count/max(report.tested_templates,1)*100:.1f}%)")
        print(f"🔴 Low Quality (<0.6): {report.low_quality_count} ({report.low_quality_count/max(report.tested_templates,1)*100:.1f}%)")
        print()
        
        # Show individual template results if verbose
        if args.verbose and report.template_metrics:
            print("📋 INDIVIDUAL TEMPLATE RESULTS")
            print("-" * 60)
            
            # Sort by effectiveness score
            sorted_metrics = sorted(report.template_metrics.items(), 
                                  key=lambda x: x[1].effectiveness_score, reverse=True)
            
            for template_name, metrics in sorted_metrics:
                status = "🟢" if metrics.effectiveness_score >= 0.8 else "🟡" if metrics.effectiveness_score >= 0.6 else "🔴"
                
                print(f"{status} {template_name}")
                print(f"   Effectiveness: {metrics.effectiveness_score:.3f}")
                print(f"   Output Quality: {metrics.output_quality_score:.3f}")
                print(f"   Instruction Clarity: {metrics.instruction_clarity_score:.3f}")
                print(f"   Structure: {metrics.structure_completeness:.3f}")
                print(f"   Content: {metrics.content_relevance:.3f}")
                print(f"   Format: {metrics.format_compliance:.3f}")
                print()
        
        # Show recommendations
        if report.recommendations:
            print("💡 RECOMMENDATIONS")
            print("-" * 60)
            for i, rec in enumerate(report.recommendations, 1):
                print(f"{i}. {rec}")
            print()
        
        # Generate detailed report if requested
        if args.output_file:
            if args.format == "text":
                detailed_report = validator.generate_detailed_report(report)
                Path(args.output_file).write_text(detailed_report, encoding='utf-8')
                print(f"📄 Detailed report saved to: {args.output_file}")
            elif args.format == "json":
                import json
                # Convert report to JSON-serializable format
                report_dict = {
                    "total_templates": report.total_templates,
                    "tested_templates": report.tested_templates,
                    "average_effectiveness": report.average_effectiveness,
                    "high_quality_count": report.high_quality_count,
                    "medium_quality_count": report.medium_quality_count,
                    "low_quality_count": report.low_quality_count,
                    "template_metrics": {
                        name: {
                            "template_name": metrics.template_name,
                            "effectiveness_score": metrics.effectiveness_score,
                            "output_quality_score": metrics.output_quality_score,
                            "instruction_clarity_score": metrics.instruction_clarity_score,
                            "structure_completeness": metrics.structure_completeness,
                            "content_relevance": metrics.content_relevance,
                            "format_compliance": metrics.format_compliance,
                            "instruction_following": metrics.instruction_following,
                            "language_clarity": metrics.language_clarity,
                            "requirement_clarity": metrics.requirement_clarity,
                            "parameter_usage": metrics.parameter_usage,
                            "test_timestamp": metrics.test_timestamp.isoformat()
                        }
                        for name, metrics in report.template_metrics.items()
                    },
                    "recommendations": report.recommendations,
                    "test_timestamp": report.test_timestamp.isoformat()
                }
                
                Path(args.output_file).write_text(json.dumps(report_dict, indent=2, ensure_ascii=False), encoding='utf-8')
                print(f"📄 JSON report saved to: {args.output_file}")
        
        # Determine exit code based on quality
        if report.tested_templates == 0:
            print("⚠️  No templates were tested")
            return 1
        elif report.average_effectiveness < 0.6:
            print("⚠️  Average template effectiveness is below acceptable threshold")
            return 1
        else:
            print("✅ Template effectiveness testing completed successfully")
            return 0
            
    except Exception as e:
        print(f"❌ Error during template testing: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())