"""
Test suite for Task 1: Core Interfaces and Data Models

Tests the fundamental components of the zero-cost MCP Server architecture.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from mcps.deep_thinking.models.mcp_models import (
    StartThinkingInput, NextStepInput, AnalyzeStepInput, CompleteThinkingInput,
    MCPToolOutput, MCPToolName, SessionState
)
from mcps.deep_thinking.sessions.session_manager import SessionManager
from mcps.deep_thinking.templates.template_manager import TemplateManager
from mcps.deep_thinking.flows.flow_manager import FlowManager
from mcps.deep_thinking.tools.mcp_tools import MCPTools
from mcps.deep_thinking.config.exceptions import DeepThinkingError


class TestMCPModels:
    """Test MCP data models"""
    
    def test_start_thinking_input(self):
        """Test StartThinkingInput model"""
        input_data = StartThinkingInput(
            topic="如何提高学习效率？",
            complexity="moderate",
            focus="学生群体"
        )
        
        assert input_data.topic == "如何提高学习效率？"
        assert input_data.complexity == "moderate"
        assert input_data.focus == "学生群体"
        assert input_data.flow_type == "comprehensive_analysis"  # default
    
    def test_mcp_tool_output(self):
        """Test MCPToolOutput model"""
        output = MCPToolOutput(
            tool_name=MCPToolName.START_THINKING,
            prompt_template="Test template: {topic}",
            instructions="Test instructions"
        )
        
        assert output.tool_name == MCPToolName.START_THINKING
        assert "Test template" in output.prompt_template
        assert output.instructions == "Test instructions"
        assert output.session_id is None  # optional field
    
    def test_session_state(self):
        """Test SessionState model"""
        session = SessionState(
            session_id="test-session",
            topic="Test topic",
            current_step="test_step",
            flow_type="test_flow"
        )
        
        assert session.session_id == "test-session"
        assert session.topic == "Test topic"
        assert session.current_step == "test_step"
        assert session.flow_type == "test_flow"
        assert session.status == "active"  # default


class TestSessionManager:
    """Test session management system"""
    
    def setup_method(self):
        """Setup test session manager"""
        self.session_manager = SessionManager(':memory:')
    
    def test_create_and_get_session(self):
        """Test session creation and retrieval"""
        session_state = SessionState(
            session_id="test-001",
            topic="Test topic",
            current_step="initial_step",
            flow_type="test_flow"
        )
        
        # Create session
        session_id = self.session_manager.create_session(session_state)
        assert session_id == "test-001"
        
        # Retrieve session
        retrieved = self.session_manager.get_session(session_id)
        assert retrieved is not None
        assert retrieved.topic == "Test topic"
        assert retrieved.current_step == "initial_step"
    
    def test_update_session_step(self):
        """Test session step updates"""
        session_state = SessionState(
            session_id="test-002",
            topic="Test topic",
            current_step="step1",
            flow_type="test_flow"
        )
        
        self.session_manager.create_session(session_state)
        
        # Update step
        self.session_manager.update_session_step("test-002", "step2")
        
        # Verify update
        updated = self.session_manager.get_session("test-002")
        assert updated.current_step == "step2"
        assert updated.step_number == 1  # incremented
    
    def test_add_step_result(self):
        """Test adding step results"""
        session_state = SessionState(
            session_id="test-003",
            topic="Test topic",
            current_step="step1",
            flow_type="test_flow"
        )
        
        self.session_manager.create_session(session_state)
        
        # Add step result
        self.session_manager.add_step_result(
            "test-003", 
            "step1", 
            "Step completed successfully",
            quality_score=0.85
        )
        
        # Verify result was added
        session = self.session_manager.get_session("test-003")
        assert "step1" in session.step_results
        assert session.step_results["step1"]["result"] == "Step completed successfully"
        assert session.step_results["step1"]["quality_score"] == 0.85


class TestTemplateManager:
    """Test template management system"""
    
    def setup_method(self):
        """Setup test template manager"""
        self.template_manager = TemplateManager()
    
    def test_get_decomposition_template(self):
        """Test decomposition template rendering"""
        template = self.template_manager.get_template('decomposition', {
            'topic': '如何提高学习效率？',
            'complexity': 'moderate',
            'focus': '学生群体',
            'domain_context': '教育'
        })
        
        assert '如何提高学习效率？' in template
        assert 'moderate' in template
        assert '学生群体' in template
        assert 'JSON格式' in template
    
    def test_get_evidence_template(self):
        """Test evidence collection template"""
        template = self.template_manager.get_template('evidence_collection', {
            'sub_question': '什么是有效的学习方法？',
            'keywords': ['学习方法', '效率', '记忆'],
            'context': '学生学习'
        })
        
        assert '什么是有效的学习方法？' in template
        assert 'Web搜索' in template
        assert '证据收集' in template
    
    def test_list_templates(self):
        """Test template listing"""
        templates = self.template_manager.list_templates()
        
        assert len(templates) > 0
        assert 'decomposition' in templates
        assert 'evidence_collection' in templates
        assert 'critical_evaluation' in templates


class TestFlowManager:
    """Test flow management system"""
    
    def setup_method(self):
        """Setup test flow manager"""
        self.flow_manager = FlowManager()
    
    def test_list_flows(self):
        """Test flow listing"""
        flows = self.flow_manager.list_flows()
        
        assert len(flows) > 0
        assert 'comprehensive_analysis' in flows
        assert 'quick_analysis' in flows
    
    def test_get_flow_info(self):
        """Test flow information retrieval"""
        flow_info = self.flow_manager.get_flow_info('comprehensive_analysis')
        
        assert flow_info is not None
        assert flow_info['name'] == 'comprehensive_analysis'
        assert flow_info['total_steps'] > 0
        assert 'steps' in flow_info
    
    def test_get_next_step(self):
        """Test next step logic"""
        next_step = self.flow_manager.get_next_step(
            'comprehensive_analysis',
            'decompose_problem',
            '{"sub_questions": [{"id": "sq1"}]}'
        )
        
        assert next_step is not None
        assert next_step['step_name'] == 'collect_evidence'
        assert 'template_name' in next_step
        assert 'instructions' in next_step


class TestMCPTools:
    """Test MCP tools integration"""
    
    def setup_method(self):
        """Setup test MCP tools"""
        self.session_manager = SessionManager(':memory:')
        self.template_manager = TemplateManager()
        self.flow_manager = FlowManager()
        self.mcp_tools = MCPTools(
            self.session_manager,
            self.template_manager,
            self.flow_manager
        )
    
    def test_start_thinking(self):
        """Test start_thinking MCP tool"""
        input_data = StartThinkingInput(
            topic="如何提高团队协作效率？",
            complexity="complex",
            focus="远程工作"
        )
        
        result = self.mcp_tools.start_thinking(input_data)
        
        assert result.tool_name == MCPToolName.START_THINKING
        assert result.session_id is not None
        assert result.step == "decompose_problem"
        assert len(result.prompt_template) > 0
        assert "如何提高团队协作效率？" in result.prompt_template
        assert result.next_action is not None
    
    def test_next_step(self):
        """Test next_step MCP tool"""
        # First create a session
        start_input = StartThinkingInput(
            topic="测试问题",
            complexity="moderate"
        )
        start_result = self.mcp_tools.start_thinking(start_input)
        
        # Then test next step
        next_input = NextStepInput(
            session_id=start_result.session_id,
            step_result='{"sub_questions": [{"id": "sq1", "question": "子问题1"}]}'
        )
        
        result = self.mcp_tools.next_step(next_input)
        
        assert result.tool_name == MCPToolName.NEXT_STEP
        assert result.session_id == start_result.session_id
        assert result.step is not None
        assert len(result.prompt_template) > 0
    
    def test_analyze_step(self):
        """Test analyze_step MCP tool"""
        # Create a session first
        start_input = StartThinkingInput(topic="测试问题")
        start_result = self.mcp_tools.start_thinking(start_input)
        
        # Test analyze step
        analyze_input = AnalyzeStepInput(
            session_id=start_result.session_id,
            step_name="decompose_problem",
            step_result="问题分解完成"
        )
        
        result = self.mcp_tools.analyze_step(analyze_input)
        
        assert result.tool_name == MCPToolName.ANALYZE_STEP
        assert result.session_id == start_result.session_id
        assert "analyze_" in result.step
        assert len(result.prompt_template) > 0
    
    def test_complete_thinking(self):
        """Test complete_thinking MCP tool"""
        # Create a session first
        start_input = StartThinkingInput(topic="测试问题")
        start_result = self.mcp_tools.start_thinking(start_input)
        
        # Test complete thinking
        complete_input = CompleteThinkingInput(
            session_id=start_result.session_id,
            final_insights="测试洞察"
        )
        
        result = self.mcp_tools.complete_thinking(complete_input)
        
        assert result.tool_name == MCPToolName.COMPLETE_THINKING
        assert result.session_id == start_result.session_id
        assert result.step == "generate_final_report"
        assert len(result.prompt_template) > 0


class TestErrorHandling:
    """Test error handling and exceptions"""
    
    def test_deep_thinking_error(self):
        """Test DeepThinkingError exception"""
        error = DeepThinkingError(
            "Test error message",
            error_code="TEST_001",
            details={"test": True}
        )
        
        assert str(error) == "Test error message"
        assert error.error_code == "TEST_001"
        assert error.details["test"] is True
        
        # Test serialization
        error_dict = error.to_dict()
        assert error_dict["error_type"] == "DeepThinkingError"
        assert error_dict["message"] == "Test error message"
        assert error_dict["error_code"] == "TEST_001"
    
    def test_session_not_found_handling(self):
        """Test handling of non-existent sessions"""
        session_manager = SessionManager(':memory:')
        template_manager = TemplateManager()
        flow_manager = FlowManager()
        mcp_tools = MCPTools(session_manager, template_manager, flow_manager)
        
        # Test next_step with non-existent session
        next_input = NextStepInput(
            session_id="non-existent-session",
            step_result="test result"
        )
        
        result = mcp_tools.next_step(next_input)
        
        # Should return session recovery prompt
        assert result.step == "session_recovery"
        assert "会话恢复" in result.prompt_template


def run_tests():
    """Simple test runner without pytest"""
    test_classes = [
        TestMCPModels,
        TestSessionManager,
        TestTemplateManager,
        TestFlowManager,
        TestMCPTools,
        TestErrorHandling
    ]
    
    total_tests = 0
    passed_tests = 0
    
    print("🧪 Running Task 1 Core Interface Tests")
    print("=" * 50)
    
    for test_class in test_classes:
        print(f"\n📋 {test_class.__name__}")
        instance = test_class()
        
        # Setup if method exists
        if hasattr(instance, 'setup_method'):
            instance.setup_method()
        
        # Run all test methods
        for method_name in dir(instance):
            if method_name.startswith('test_'):
                total_tests += 1
                try:
                    method = getattr(instance, method_name)
                    method()
                    print(f"  ✅ {method_name}")
                    passed_tests += 1
                except Exception as e:
                    print(f"  ❌ {method_name}: {e}")
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)