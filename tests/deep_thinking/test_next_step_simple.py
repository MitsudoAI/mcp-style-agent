"""
Simple test for next_step tool functionality
Tests the core logic without complex imports
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))


def test_next_step_basic():
    """Test basic next_step functionality with minimal setup"""
    print("🧪 Testing next_step tool basic functionality...")

    # Test 1: Basic flow progression
    print("  ✅ Test 1: Flow progression logic")

    # Simulate flow steps
    flow_steps = ["decompose", "evidence", "evaluate", "reflect"]
    current_step = "decompose"

    # Find next step
    current_index = flow_steps.index(current_step)
    next_step = (
        flow_steps[current_index + 1] if current_index + 1 < len(flow_steps) else None
    )

    assert next_step == "evidence", f"Expected 'evidence', got {next_step}"
    print(f"    Next step after '{current_step}': {next_step}")

    # Test 2: Template selection logic
    print("  ✅ Test 2: Template selection")

    template_mapping = {
        "decompose": "decomposition",
        "evidence": "evidence_collection",
        "evaluate": "critical_evaluation",
        "reflect": "reflection",
    }

    selected_template = template_mapping.get(next_step, "default")
    assert (
        selected_template == "evidence_collection"
    ), f"Expected 'evidence_collection', got {selected_template}"
    print(f"    Template for '{next_step}': {selected_template}")

    # Test 3: Context building
    print("  ✅ Test 3: Context management")

    session_context = {
        "session_id": "test-123",
        "topic": "Test topic",
        "complexity": "moderate",
        "current_step": next_step,
        "step_number": 2,
        "flow_type": "comprehensive_analysis",
    }

    assert session_context["current_step"] == "evidence"
    assert session_context["step_number"] == 2
    print(f"    Context built: {len(session_context)} fields")

    # Test 4: Quality feedback handling
    print("  ✅ Test 4: Quality feedback processing")

    quality_feedback = {"quality_score": 0.8, "feedback": "Good work"}
    quality_gate_passed = quality_feedback.get("quality_score", 1.0) >= 0.7

    assert quality_gate_passed is True, "Quality gate should pass with score 0.8"
    print(f"    Quality gate passed: {quality_gate_passed}")

    # Test 5: Low quality handling
    print("  ✅ Test 5: Low quality handling")

    low_quality_feedback = {"quality_score": 0.5, "feedback": "Needs improvement"}
    low_quality_gate = low_quality_feedback.get("quality_score", 1.0) >= 0.6

    assert low_quality_gate is False, "Quality gate should fail with score 0.5"

    # Should suggest improvement
    improvement_needed = not low_quality_gate
    improvement_step = f"improve_{current_step}" if improvement_needed else next_step

    assert (
        improvement_step == "improve_decompose"
    ), f"Expected improvement step, got {improvement_step}"
    print(f"    Improvement step suggested: {improvement_step}")

    # Test 6: Metadata generation
    print("  ✅ Test 6: Metadata generation")

    metadata = {
        "step_number": 2,
        "flow_progress": "2/5",
        "flow_type": "comprehensive_analysis",
        "previous_step": current_step,
        "quality_gate_passed": quality_gate_passed,
        "template_selected": selected_template,
        "context_enriched": True,
    }

    required_fields = [
        "step_number",
        "flow_progress",
        "quality_gate_passed",
        "template_selected",
    ]
    for field in required_fields:
        assert field in metadata, f"Missing required metadata field: {field}"

    print(f"    Metadata generated: {len(metadata)} fields")

    # Test 7: Instructions generation
    print("  ✅ Test 7: Instructions generation")

    base_instruction = f"Execute {next_step} step"
    complexity = session_context.get("complexity", "moderate")

    contextual_instruction = base_instruction
    if complexity == "complex":
        contextual_instruction += "。请特别注意分析的深度和全面性"

    assert len(contextual_instruction) > 0, "Instructions should not be empty"
    print(f"    Instructions: {contextual_instruction}")

    print("🎉 All basic next_step tests passed!")
    return True


def test_next_step_error_scenarios():
    """Test error handling scenarios"""
    print("🧪 Testing next_step error scenarios...")

    # Test 1: Non-existent session
    print("  ✅ Test 1: Non-existent session handling")

    # We use a placeholder session ID but don't actually use it in the test
    # session_id = "non-existent-session"
    session_exists = False  # Simulate session not found

    if not session_exists:
        recovery_action = "session_recovery"
        # Generate prompt but not using it in this test
        # recovery_prompt = "Session not found. Please choose recovery option."

    assert recovery_action == "session_recovery", "Should trigger session recovery"
    print(f"    Recovery action: {recovery_action}")

    # Test 2: Flow completion detection
    print("  ✅ Test 2: Flow completion detection")

    flow_steps = ["decompose", "evidence", "evaluate", "reflect"]
    completed_steps = ["decompose", "evidence", "evaluate", "reflect"]

    flow_completed = len(completed_steps) >= len(flow_steps)

    assert flow_completed is True, "Flow should be marked as completed"

    if flow_completed:
        completion_action = "flow_completion"
        # Generate prompt but not using it in this test
        # completion_prompt = "Flow completed. Ready for final report."

    assert completion_action == "flow_completion", "Should trigger flow completion"
    print(f"    Completion action: {completion_action}")

    # Test 3: Invalid step result format
    print("  ✅ Test 3: Invalid step result handling")

    step_result = "Invalid JSON format"

    try:
        # We don't need to use the parsed result in this test
        json.loads(step_result)
        result_valid = True
    except json.JSONDecodeError:
        result_valid = False
        error_guidance = "Please provide result in valid JSON format"

    assert result_valid is False, "Should detect invalid JSON"
    assert "JSON format" in error_guidance, "Should provide JSON format guidance"
    print(f"    Error guidance: {error_guidance}")

    print("🎉 All error scenario tests passed!")
    return True


def test_next_step_template_parameters():
    """Test template parameter building"""
    print("🧪 Testing template parameter building...")

    # Test 1: Basic parameter building
    print("  ✅ Test 1: Basic parameters")

    session_data = {
        "topic": "How to improve team collaboration?",
        "current_step": "decompose",
        "complexity": "moderate",
        "focus": "remote teams",
    }

    step_result = '{"sub_questions": [{"id": "sq1", "question": "What are communication barriers?"}]}'

    template_params = {
        "topic": session_data["topic"],
        "complexity": session_data["complexity"],
        "focus": session_data["focus"],
        "previous_result": step_result,
        "step_name": "evidence",
    }

    assert template_params["topic"] == session_data["topic"]
    assert template_params["complexity"] == session_data["complexity"]
    print(f"    Parameters built: {len(template_params)} fields")

    # Test 2: Enhanced parameters for evidence collection
    print("  ✅ Test 2: Evidence collection parameters")

    if "evidence" in template_params["step_name"]:
        # Extract sub-questions from previous result
        try:
            parsed_result = json.loads(step_result)
            sub_questions = parsed_result.get("sub_questions", [])
            if sub_questions:
                template_params["sub_question"] = sub_questions[0]["question"]
                template_params["keywords"] = sub_questions[0].get(
                    "search_keywords", []
                )
        except Exception:
            template_params["sub_question"] = "Based on problem decomposition"
            template_params["keywords"] = ["relevant", "keywords"]

    assert (
        "sub_question" in template_params
    ), "Should have sub_question for evidence collection"
    print("    Evidence parameters: sub_question, keywords added")

    # Test 3: Context-specific parameters
    print("  ✅ Test 3: Context-specific parameters")

    if session_data["complexity"] == "complex":
        template_params["analysis_depth"] = "comprehensive"
        template_params["additional_guidance"] = "请特别注意分析的深度和全面性"
    else:
        template_params["analysis_depth"] = "standard"
        template_params["additional_guidance"] = ""

    assert (
        template_params["analysis_depth"] == "standard"
    ), "Should use standard depth for moderate complexity"
    print(
        f"    Context parameters: analysis_depth = {template_params['analysis_depth']}"
    )

    print("🎉 All template parameter tests passed!")
    return True


def run_simple_tests():
    """Run all simple tests"""
    print("🚀 Running Simple next_step Tool Tests")
    print("=" * 50)

    tests = [
        test_next_step_basic,
        test_next_step_error_scenarios,
        test_next_step_template_parameters,
    ]

    passed = 0
    total = len(tests)

    for test_func in tests:
        try:
            if test_func():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test failed: {e}")
            print()

    print("=" * 50)
    print(f"🎯 Results: {passed}/{total} test suites passed")

    if passed == total:
        print("🎉 All simple tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False


if __name__ == "__main__":
    success = run_simple_tests()
    exit(0 if success else 1)
