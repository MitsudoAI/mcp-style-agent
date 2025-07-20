"""
Unit tests for the next_step MCP tool

Tests the enhanced next_step implementation including:
- Flow step control and template selection
- Context management and state tracking
- Quality feedback handling
- Error scenarios and recovery
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

try:
    from mcps.deep_thinking.flows.flow_manager import FlowManager
    from mcps.deep_thinking.models.mcp_models import (  # MCPToolOutput not used in this file
        MCPToolName,
        NextStepInput,
        SessionState,
        StartThinkingInput,
    )
    from mcps.deep_thinking.sessions.session_manager import SessionManager
    from mcps.deep_thinking.templates.template_manager import TemplateManager
    from mcps.deep_thinking.tools.mcp_tools import MCPTools
except ImportError as e:
    print(f"Import error: {e}")
    print("Creating minimal test environment...")

    # Create minimal mock classes for testing
    class MockTemplateManager:
        def get_template(self, name, params=None):
            return f"Mock template for {name}"

        def list_templates(self):
            return ["decomposition", "evidence_collection"]

    class MockFlowManager:
        def get_next_step(self, flow_type, current_step, result):
            return {
                "step_name": "evidence",
                "template_name": "evidence_collection",
                "instructions": "Test",
            }

        def get_total_steps(self, flow_type):
            return 5

    class MockSessionManager:
        def __init__(self, db_path):
            self.sessions = {}

        def create_session(self, session_state):
            self.sessions[session_state.session_id] = session_state
            return session_state.session_id

        def get_session(self, session_id):
            return self.sessions.get(session_id)

        def add_step_result(self, *args, **kwargs):
            return True

        def update_session_step(self, *args, **kwargs):
            return True

    # Use mock classes
    TemplateManager = MockTemplateManager
    FlowManager = MockFlowManager
    SessionManager = MockSessionManager


class TestNextStepTool:
    """Test the next_step MCP tool functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.session_manager = SessionManager(":memory:")
        self.template_manager = TemplateManager()
        self.flow_manager = FlowManager()
        self.mcp_tools = MCPTools(
            self.session_manager, self.template_manager, self.flow_manager
        )

        # Create a test session
        self.test_session_id = self._create_test_session()

    def _create_test_session(self) -> str:
        """Create a test session for testing"""
        start_input = StartThinkingInput(
            topic="如何提高团队协作效率？", complexity="moderate", focus="远程工作团队"
        )
        result = self.mcp_tools.start_thinking(start_input)
        return result.session_id

    def test_next_step_basic_functionality(self):
        """Test basic next_step functionality"""
        # Prepare input with decomposition result
        decomposition_result = json.dumps(
            {
                "main_question": "如何提高团队协作效率？",
                "sub_questions": [
                    {
                        "id": "sq1",
                        "question": "远程工作中的沟通障碍有哪些？",
                        "priority": "high",
                        "search_keywords": ["远程沟通", "协作工具", "沟通障碍"],
                        "expected_perspectives": ["技术角度", "管理角度", "员工角度"],
                    },
                    {
                        "id": "sq2",
                        "question": "有效的协作工具和方法有哪些？",
                        "priority": "high",
                        "search_keywords": ["协作工具", "项目管理", "团队效率"],
                        "expected_perspectives": ["工具评估", "实施策略", "成本效益"],
                    },
                ],
                "relationships": ["sq1影响sq2的工具选择"],
            }
        )

        next_input = NextStepInput(
            session_id=self.test_session_id, step_result=decomposition_result
        )

        # Execute next_step
        result = self.mcp_tools.next_step(next_input)

        # Verify basic properties
        assert result.tool_name == MCPToolName.NEXT_STEP
        assert result.session_id == self.test_session_id
        assert result.step is not None
        assert len(result.prompt_template) > 0
        assert result.instructions is not None
        assert result.context is not None
        assert result.metadata is not None

        # Verify step progression
        assert "evidence" in result.step.lower() or "collect" in result.step.lower()

        # Verify template contains relevant content
        assert "证据收集" in result.prompt_template or "搜索" in result.prompt_template

        print(f"✅ Basic functionality test passed - Next step: {result.step}")

    def test_next_step_with_quality_feedback(self):
        """Test next_step with quality feedback"""
        # First, complete the decomposition step
        decomposition_result = '{"sub_questions": [{"id": "sq1", "question": "test"}]}'

        next_input = NextStepInput(
            session_id=self.test_session_id,
            step_result=decomposition_result,
            quality_feedback={
                "quality_score": 0.9,
                "feedback": "Excellent decomposition",
                "suggestions": [],
            },
        )

        result = self.mcp_tools.next_step(next_input)

        # Verify quality feedback is processed
        assert result.metadata["quality_gate_passed"] is True
        assert "quality_score" not in result.step  # Should proceed normally

        print(
            f"✅ Quality feedback test passed - Quality gate: {result.metadata['quality_gate_passed']}"
        )

    def test_next_step_low_quality_handling(self):
        """Test handling of low quality results"""
        low_quality_result = "简单的分解结果"

        next_input = NextStepInput(
            session_id=self.test_session_id,
            step_result=low_quality_result,
            quality_feedback={
                "quality_score": 0.5,  # Below threshold
                "feedback": "需要更详细的分解",
                "suggestions": ["增加子问题数量", "明确搜索关键词"],
            },
        )

        result = self.mcp_tools.next_step(next_input)

        # Should suggest improvement
        assert "improve" in result.step.lower() or "改进" in result.instructions
        assert result.metadata["quality_gate_passed"] is False

        print(
            f"✅ Low quality handling test passed - Improvement suggested: {result.step}"
        )

    def test_next_step_context_management(self):
        """Test context management and enrichment"""
        step_result = '{"analysis": "detailed analysis result"}'

        next_input = NextStepInput(
            session_id=self.test_session_id, step_result=step_result
        )

        result = self.mcp_tools.next_step(next_input)

        # Verify context enrichment
        assert "session_id" in result.context
        assert "topic" in result.context
        assert "flow_type" in result.context
        assert "step_context" in result.context

        # Verify metadata enrichment
        assert "flow_progress" in result.metadata
        assert "template_selected" in result.metadata
        assert "context_enriched" in result.metadata
        assert result.metadata["context_enriched"] is True

        print(
            f"✅ Context management test passed - Context keys: {len(result.context)}"
        )

    def test_next_step_template_selection(self):
        """Test intelligent template selection"""
        # Test with complex session
        complex_session = SessionState(
            session_id="complex-test",
            topic="复杂的战略决策问题",
            current_step="decompose_problem",
            flow_type="comprehensive_analysis",
            context={"complexity": "complex", "focus": "战略分析"},
        )

        self.session_manager.create_session(complex_session)

        next_input = NextStepInput(
            session_id="complex-test",
            step_result='{"complex_analysis": "detailed result"}',
        )

        result = self.mcp_tools.next_step(next_input)

        # Verify template selection considers complexity
        assert result.metadata["template_selected"] is not None
        assert len(result.prompt_template) > 100  # Should be substantial

        print(
            f"✅ Template selection test passed - Template: {result.metadata['template_selected']}"
        )

    def test_next_step_flow_completion(self):
        """Test flow completion detection"""
        # Create a session and simulate completing all steps
        # We don't need to use the session object in this test
        self.session_manager.get_session(self.test_session_id)

        # Simulate multiple completed steps
        for i, step_name in enumerate(["decompose", "evidence", "evaluate"]):
            self.session_manager.add_step_result(
                self.test_session_id,
                step_name,
                f"Step {i+1} completed",
                quality_score=0.8,
            )
            self.session_manager.update_session_step(self.test_session_id, step_name)

        # Try to get next step when flow should be complete
        next_input = NextStepInput(
            session_id=self.test_session_id, step_result="Final step completed"
        )

        result = self.mcp_tools.next_step(next_input)

        # Should indicate flow completion
        assert "complete" in result.step.lower() or "完成" in result.prompt_template

        print(f"✅ Flow completion test passed - Completion detected: {result.step}")

    def test_next_step_error_handling(self):
        """Test error handling scenarios"""
        # Test with non-existent session
        invalid_input = NextStepInput(
            session_id="non-existent-session", step_result="test result"
        )

        result = self.mcp_tools.next_step(invalid_input)

        # Should return session recovery prompt
        assert result.step == "session_recovery"
        assert (
            "会话恢复" in result.prompt_template
            or "session" in result.prompt_template.lower()
        )

        print("✅ Error handling test passed - Session recovery triggered")

    def test_next_step_step_result_saving(self):
        """Test that step results are properly saved"""
        step_result = '{"detailed_result": "comprehensive analysis", "quality": "high"}'

        next_input = NextStepInput(
            session_id=self.test_session_id,
            step_result=step_result,
            quality_feedback={"quality_score": 0.85},
        )

        # Get session state before
        session_before = self.session_manager.get_session(self.test_session_id)
        current_step_before = session_before.current_step

        # Execute next_step (we don't need to use the result in this test)
        self.mcp_tools.next_step(next_input)

        # Get session state after
        session_after = self.session_manager.get_session(self.test_session_id)

        # Verify step result was saved
        assert current_step_before in session_after.step_results

        # Verify quality score was saved
        if current_step_before in session_after.quality_scores:
            assert session_after.quality_scores[current_step_before] == 0.85

        print(
            f"✅ Step result saving test passed - Results saved for: {current_step_before}"
        )

    def test_next_step_instructions_generation(self):
        """Test contextual instructions generation"""
        # Test with different complexity levels
        test_cases = [
            ("simple", "简单问题"),
            ("moderate", "中等复杂度问题"),
            ("complex", "复杂战略问题"),
        ]

        for complexity, topic in test_cases:
            # Create session with specific complexity
            session_state = SessionState(
                session_id=f"test-{complexity}",
                topic=topic,
                current_step="decompose_problem",
                flow_type="comprehensive_analysis",
                context={"complexity": complexity},
            )

            self.session_manager.create_session(session_state)

            next_input = NextStepInput(
                session_id=f"test-{complexity}",
                step_result=f"Analysis for {complexity} problem",
            )

            result = self.mcp_tools.next_step(next_input)

            # Verify instructions are contextual
            assert len(result.instructions) > 0

            if complexity == "complex":
                assert "深度" in result.instructions or "全面" in result.instructions

        print(
            "✅ Instructions generation test passed - Contextual instructions generated"
        )

    def test_next_step_metadata_completeness(self):
        """Test metadata completeness and accuracy"""
        next_input = NextStepInput(
            session_id=self.test_session_id, step_result='{"test": "result"}'
        )

        result = self.mcp_tools.next_step(next_input)

        # Verify all expected metadata fields
        expected_fields = [
            "step_number",
            "flow_progress",
            "flow_type",
            "previous_step",
            "quality_gate_passed",
            "template_selected",
            "context_enriched",
        ]

        for field in expected_fields:
            assert field in result.metadata, f"Missing metadata field: {field}"

        # Verify metadata values are reasonable
        assert isinstance(result.metadata["step_number"], int)
        assert "/" in result.metadata["flow_progress"]
        assert isinstance(result.metadata["quality_gate_passed"], bool)
        assert isinstance(result.metadata["context_enriched"], bool)

        print(
            f"✅ Metadata completeness test passed - All {len(expected_fields)} fields present"
        )


def run_next_step_tests():
    """Run all next_step tool tests"""
    test_class = TestNextStepTool()

    test_methods = [
        "test_next_step_basic_functionality",
        "test_next_step_with_quality_feedback",
        "test_next_step_low_quality_handling",
        "test_next_step_context_management",
        "test_next_step_template_selection",
        "test_next_step_flow_completion",
        "test_next_step_error_handling",
        "test_next_step_step_result_saving",
        "test_next_step_instructions_generation",
        "test_next_step_metadata_completeness",
    ]

    total_tests = len(test_methods)
    passed_tests = 0

    print("🧪 Running next_step Tool Tests")
    print("=" * 50)

    for method_name in test_methods:
        try:
            # Setup for each test
            test_class.setup_method()

            # Run test
            method = getattr(test_class, method_name)
            method()
            passed_tests += 1

        except Exception as e:
            print(f"  ❌ {method_name}: {e}")

    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("🎉 All next_step tool tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False


if __name__ == "__main__":
    success = run_next_step_tests()
    exit(0 if success else 1)
