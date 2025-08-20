#!/usr/bin/env python3
"""
Template Quality Validation CLI Tool

Command-line interface for validating template quality, generating reports,
and performing batch validation of template directories.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

from template_validator import (
    TemplateValidator,
    TemplateValidationResult,
    ValidationSeverity,
    validate_template_quick,
)


def print_colored(text: str, color: str = "white"):
    """Print colored text to terminal"""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m",
    }

    print(f"{colors.get(color, colors['white'])}{text}{colors['reset']}")


def print_validation_summary(result: TemplateValidationResult):
    """Print a summary of validation results"""
    # Status indicator
    status_color = "green" if result.is_valid else "red"
    status_text = "✅ VALID" if result.is_valid else "❌ INVALID"

    print_colored(f"\n{'='*60}", "cyan")
    print_colored(f"Template: {result.template_name}", "blue")
    print_colored(f"Status: {status_text}", status_color)
    print_colored(f"Overall Score: {result.overall_score:.2f}/1.00", "white")

    # Score bar
    score_bar = "█" * int(result.overall_score * 20) + "░" * (
        20 - int(result.overall_score * 20)
    )
    print_colored(f"Quality: [{score_bar}]", "cyan")

    # Metrics
    if result.metrics:
        print_colored("\nMetrics:", "yellow")
        print(f"  • Total Issues: {result.metrics.get('total_issues', 0)}")
        print(
            f"  • Critical: {result.metrics.get('critical_issues', 0)}, "
            f"Errors: {result.metrics.get('error_issues', 0)}, "
            f"Warnings: {result.metrics.get('warning_issues', 0)}"
        )
        print(f"  • Parameters: {result.metrics.get('parameter_count', 0)}")
        print(
            f"  • Size: {result.metrics.get('word_count', 0)} words, "
            f"{result.metrics.get('line_count', 0)} lines"
        )
        print(
            f"  • Scores: Format {result.metrics.get('format_score', 0):.2f}, "
            f"Content {result.metrics.get('content_score', 0):.2f}, "
            f"Effectiveness {result.metrics.get('effectiveness_score', 0):.2f}"
        )


def print_issues(result: TemplateValidationResult, show_all: bool = False):
    """Print validation issues"""
    if not result.issues:
        print_colored("  No issues found! 🎉", "green")
        return

    # Group issues by severity
    issues_by_severity = {
        ValidationSeverity.CRITICAL: [],
        ValidationSeverity.ERROR: [],
        ValidationSeverity.WARNING: [],
        ValidationSeverity.INFO: [],
    }

    for issue in result.issues:
        issues_by_severity[issue.severity].append(issue)

    # Print issues by severity
    severity_colors = {
        ValidationSeverity.CRITICAL: "red",
        ValidationSeverity.ERROR: "red",
        ValidationSeverity.WARNING: "yellow",
        ValidationSeverity.INFO: "blue",
    }

    severity_icons = {
        ValidationSeverity.CRITICAL: "🚨",
        ValidationSeverity.ERROR: "❌",
        ValidationSeverity.WARNING: "⚠️",
        ValidationSeverity.INFO: "ℹ️",
    }

    for severity in [
        ValidationSeverity.CRITICAL,
        ValidationSeverity.ERROR,
        ValidationSeverity.WARNING,
        ValidationSeverity.INFO,
    ]:
        issues = issues_by_severity[severity]
        if not issues:
            continue

        if not show_all and severity == ValidationSeverity.INFO and len(issues) > 3:
            # Limit info issues if not showing all
            issues = issues[:3]
            truncated = True
        else:
            truncated = False

        print_colored(
            f"\n{severity_icons[severity]} {severity.value.upper()} Issues:",
            severity_colors[severity],
        )

        for issue in issues:
            location = f" (Line {issue.line_number})" if issue.line_number else ""
            print(f"  • [{issue.category}] {issue.message}{location}")
            if issue.suggestion:
                print_colored(f"    💡 {issue.suggestion}", "cyan")

        if truncated:
            print_colored(
                f"    ... and {len(issues_by_severity[severity]) - 3} more info issues",
                "blue",
            )


def print_suggestions(result: TemplateValidationResult):
    """Print improvement suggestions"""
    if not result.suggestions:
        return

    print_colored("\n💡 Suggestions:", "magenta")
    for suggestion in result.suggestions:
        print(f"  • {suggestion}")


def validate_single_template(template_path: str, verbose: bool = False) -> bool:
    """Validate a single template file"""
    validator = TemplateValidator()

    try:
        result = validator.validate_template_file(template_path)

        print_validation_summary(result)
        print_issues(result, show_all=verbose)
        print_suggestions(result)

        return result.is_valid

    except Exception as e:
        print_colored(f"Error validating template: {e}", "red")
        return False


def validate_directory(
    templates_dir: str, verbose: bool = False, output_format: str = "console"
) -> bool:
    """Validate all templates in a directory"""
    validator = TemplateValidator()

    try:
        results = validator.validate_all_templates(templates_dir)

        if not results:
            print_colored("No template files found in directory.", "yellow")
            return True

        if output_format == "json":
            # Output JSON format
            json_results = {}
            for name, result in results.items():
                json_results[name] = {
                    "is_valid": result.is_valid,
                    "overall_score": result.overall_score,
                    "metrics": result.metrics,
                    "issues": [
                        {
                            "severity": issue.severity.value,
                            "category": issue.category,
                            "message": issue.message,
                            "line_number": issue.line_number,
                            "suggestion": issue.suggestion,
                        }
                        for issue in result.issues
                    ],
                    "suggestions": result.suggestions,
                }

            print(json.dumps(json_results, indent=2, ensure_ascii=False))

        elif output_format == "report":
            # Generate detailed report
            report = validator.generate_validation_report(results)
            print(report)

        else:
            # Console format
            print_colored(f"\n{'='*80}", "cyan")
            print_colored("TEMPLATE VALIDATION RESULTS", "cyan")
            print_colored(f"{'='*80}", "cyan")

            # Summary statistics
            total_templates = len(results)
            valid_templates = sum(1 for r in results.values() if r.is_valid)
            avg_score = sum(r.overall_score for r in results.values()) / total_templates

            print_colored(f"\nSummary:", "yellow")
            print(f"  • Total Templates: {total_templates}")
            print(
                f"  • Valid Templates: {valid_templates} ({valid_templates/total_templates*100:.1f}%)"
            )
            print(f"  • Average Score: {avg_score:.2f}/1.00")

            # Individual results
            for name, result in sorted(results.items()):
                print_validation_summary(result)
                if verbose:
                    print_issues(result, show_all=True)
                    print_suggestions(result)
                else:
                    # Show only critical and error issues
                    critical_and_errors = [
                        i
                        for i in result.issues
                        if i.severity
                        in [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR]
                    ]
                    if critical_and_errors:
                        print_colored("\n🚨 Critical Issues:", "red")
                        for issue in critical_and_errors[:3]:  # Show top 3
                            print(f"  • [{issue.category}] {issue.message}")

        # Return True if all templates are valid
        return all(result.is_valid for result in results.values())

    except Exception as e:
        print_colored(f"Error validating directory: {e}", "red")
        return False


def quick_validate(template_content: str, template_name: str = "stdin"):
    """Quick validation for piped content"""
    result = validate_template_quick(template_content, template_name)

    status = "✅ VALID" if result["is_valid"] else "❌ INVALID"
    print_colored(f"Status: {status}", "green" if result["is_valid"] else "red")
    print(f"Score: {result['score']:.2f}/1.00")
    print(f"Issues: {result['issues_count']}")

    if result["critical_issues"]:
        print_colored("\nCritical Issues:", "red")
        for issue in result["critical_issues"]:
            print(f"  • {issue}")

    if result["suggestions"]:
        print_colored("\nTop Suggestions:", "magenta")
        for suggestion in result["suggestions"]:
            print(f"  • {suggestion}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Template Quality Validation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate a single template
  python validate_templates.py template.tmpl
  
  # Validate all templates in directory
  python validate_templates.py templates/
  
  # Generate detailed report
  python validate_templates.py templates/ --format report
  
  # Verbose output with all issues
  python validate_templates.py templates/ --verbose
  
  # JSON output for automation
  python validate_templates.py templates/ --format json
  
  # Quick validation from stdin
  cat template.tmpl | python validate_templates.py --quick
        """,
    )

    parser.add_argument(
        "path",
        nargs="?",
        help="Path to template file or directory (omit for stdin with --quick)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show all validation issues including info level",
    )

    parser.add_argument(
        "--format",
        "-f",
        choices=["console", "json", "report"],
        default="console",
        help="Output format (default: console)",
    )

    parser.add_argument(
        "--quick",
        "-q",
        action="store_true",
        help="Quick validation mode (reads from stdin)",
    )

    parser.add_argument("--output", "-o", help="Output file (default: stdout)")

    args = parser.parse_args()

    # Handle quick validation from stdin
    if args.quick:
        if not sys.stdin.isatty():
            content = sys.stdin.read()
            quick_validate(content)
            return
        else:
            print_colored("Error: --quick requires input from stdin", "red")
            sys.exit(1)

    # Require path for non-quick mode
    if not args.path:
        parser.print_help()
        sys.exit(1)

    path = Path(args.path)

    # Redirect output if specified
    if args.output:
        sys.stdout = open(args.output, "w", encoding="utf-8")

    try:
        if path.is_file():
            # Validate single template
            success = validate_single_template(str(path), args.verbose)
        elif path.is_dir():
            # Validate directory
            success = validate_directory(str(path), args.verbose, args.format)
        else:
            print_colored(f"Error: Path not found: {path}", "red")
            sys.exit(1)

        # Exit with appropriate code
        sys.exit(0 if success else 1)

    finally:
        if args.output:
            sys.stdout.close()


if __name__ == "__main__":
    main()
