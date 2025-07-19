"""
Tests for core interfaces and data models
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any

from mcps.deep_thinking.models.agent_models import (
    AgentInput, AgentOutput, AgentConfig, AgentMetadata, 
    AgentType, AgentStatus, AgentExecutionContext
)
from mcps.deep_thinking.models.thinking_models import (
    ThinkingSession, QuestionDecomposition, SubQuestion, 
    ComplexityLevel, Priority
)
from mcps.deep_thinking.agents.base_agent import BaseAgent, AgentFactory
from mcps.deep_thinking.config.exceptions import (
    AgentValidationError, AgentExecutionError
)


class TestAgent(BaseAgent):
    """Test agent implementation for testing"""
    
    def get_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_type=AgentType.DECOMPOSER,
            name="Test Agent",
            description="A test agent for unit testing",
            version="1.0.0",
            required_inputs=["test_input"],
            output_schema={"type": "object"}
        )
    
    def get_default_config(self) -> AgentConfig:
        return AgentConfig(
            agent_type=AgentType.DECOMPOSER,
            enabled=True,
            max_retries=3,
            timeout_seconds=30,
            temperature=0.7
        )
    
    async def _execute_internal(
        self, 
        input_data: AgentInput, 
        context: AgentExecutionContext,
        interaction_id: str
    ) -> AgentOutput:
        # Simple test implementation
        return AgentOutput(
            agent_type=self.agent_type,
            session_id=input_data.session_id,
            interaction_id=interaction_id,
            status=AgentStatus.COMPLETED,
            data={"result": "test_success", "input_received": input_data.data},
            quality_score=0.9
        )


class TestFailingAgent(BaseAgent):
    """Test agent that always fails"""
    
    def get_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_type=AgentType.CRITIC,
            name="Failing Test Agent",
            description="A test agent that always fails",
            version="1.0.0",
            required_inputs=["test_input"],
            output_schema={"type": "object"}
        )
    
    def get_default_config(self) -> AgentConfig:
        return AgentConfig(
            agent_type=AgentType.CRITIC,
            enabled=True,
            max_retries=1,
            timeout_seconds=30
        )
    
    async def _execute_internal(
        self, 
        input_data: AgentInput, 
        context: AgentExecutionContext,
        interaction_id: str
    ) -> AgentOutput:
        raise Exception("Test failure")


class TestDataModels:
    """Test Pydantic data models"""
    
    def test_agent_input_creation(self):
        """Test AgentInput model creation and validation"""
        agent_input = AgentInput(
            session_id="test_session_123",
            agent_type=AgentType.DECOMPOSER,
            data={"question": "What is the meaning of life?"},
            context={"user_id": "test_user"}
        )
        
        assert agent_input.session_id == "test_session_123"
        assert agent_input.agent_type == AgentType.DECOMPOSER
        assert agent_input.data["question"] == "What is the meaning of life?"
        assert agent_input.context["user_id"] == "test_user"
    
    def test_agent_output_creation(self):
        """Test AgentOutput model creation"""
        agent_output = AgentOutput(
            agent_type=AgentType.DECOMPOSER,
            session_id="test_session_123",
            interaction_id="interaction_456",
            status=AgentStatus.COMPLETED,
            data={"result": "success"},
            quality_score=0.85,
            execution_time=2.5
        )
        
        assert agent_output.agent_type == AgentType.DECOMPOSER
        assert agent_output.status == AgentStatus.COMPLETED
        assert agent_output.quality_score == 0.85
        assert agent_output.execution_time == 2.5
        assert isinstance(agent_output.timestamp, datetime)
    
    def test_thinking_session_creation(self):
        """Test ThinkingSession model creation"""
        session = ThinkingSession(
            id="session_123",
            topic="Test thinking session",
            user_id="user_456"
        )
        
        assert session.id == "session_123"
        assert session.topic == "Test thinking session"
        assert session.user_id == "user_456"
        assert isinstance(session.start_time, datetime)
        assert len(session.thinking_traces) == 0
    
    def test_question_decomposition_creation(self):
        """Test QuestionDecomposition model creation"""
        sub_question = SubQuestion(
            id="sub_1",
            question="What are the philosophical implications?",
            priority=Priority.HIGH,
            search_keywords=["philosophy", "implications"],
            expected_perspectives=["existentialist", "pragmatic"],
            estimated_complexity=ComplexityLevel.COMPLEX
        )
        
        decomposition = QuestionDecomposition(
            main_question="What is the meaning of life?",
            complexity_assessment=ComplexityLevel.COMPLEX,
            sub_questions=[sub_question],
            decomposition_strategy="philosophical_analysis"
        )
        
        assert decomposition.main_question == "What is the meaning of life?"
        assert decomposition.complexity_assessment == ComplexityLevel.COMPLEX
        assert len(decomposition.sub_questions) == 1
        assert decomposition.sub_questions[0].priority == Priority.HIGH


class TestBaseAgent:
    """Test BaseAgent functionality"""
    
    @pytest.fixture
    def test_agent(self):
        """Create a test agent instance"""
        return TestAgent()
    
    @pytest.fixture
    def failing_agent(self):
        """Create a failing test agent instance"""
        return TestFailingAgent()
    
    @pytest.fixture
    def agent_input(self):
        """Create test agent input"""
        return AgentInput(
            session_id="test_session_123",
            agent_type=AgentType.DECOMPOSER,
            data={"test_input": "test_value"}
        )
    
    @pytest.fixture
    def execution_context(self):
        """Create test execution context"""
        return AgentExecutionContext(
            session_id="test_session_123",
            flow_step=1,
            execution_mode="test"
        )
    
    def test_agent_metadata(self, test_agent):
        """Test agent metadata retrieval"""
        metadata = test_agent.get_metadata()
        
        assert metadata.agent_type == AgentType.DECOMPOSER
        assert metadata.name == "Test Agent"
        assert "test_input" in metadata.required_inputs
    
    def test_agent_default_config(self, test_agent):
        """Test agent default configuration"""
        config = test_agent.get_default_config()
        
        assert config.agent_type == AgentType.DECOMPOSER
        assert config.enabled is True
        assert config.max_retries == 3
        assert config.timeout_seconds == 30
    
    @pytest.mark.asyncio
    async def test_successful_agent_execution(self, test_agent, agent_input, execution_context):
        """Test successful agent execution"""
        output = await test_agent.execute(agent_input, execution_context)
        
        assert output.status == AgentStatus.COMPLETED
        assert output.data["result"] == "test_success"
        assert output.data["input_received"] == agent_input.data
        assert output.quality_score == 0.9
        assert output.execution_time is not None
        assert output.execution_time > 0
    
    @pytest.mark.asyncio
    async def test_agent_execution_failure(self, failing_agent, execution_context):
        """Test agent execution failure handling"""
        # Create input with correct agent type for the failing agent
        failing_agent_input = AgentInput(
            session_id="test_session_123",
            agent_type=AgentType.CRITIC,  # Correct type for failing agent
            data={"test_input": "test_value"}
        )
        
        with pytest.raises(AgentExecutionError):
            await failing_agent.execute(failing_agent_input, execution_context)
        
        # Check that failure was recorded in history
        history = failing_agent.get_execution_history()
        assert len(history) == 1
        assert history[0].status == AgentStatus.FAILED
        assert history[0].error_message is not None
    
    @pytest.mark.asyncio
    async def test_agent_input_validation(self, test_agent, execution_context):
        """Test agent input validation"""
        # Test with wrong agent type
        invalid_input = AgentInput(
            session_id="test_session_123",
            agent_type=AgentType.CRITIC,  # Wrong type
            data={"test_input": "test_value"}
        )
        
        with pytest.raises(AgentValidationError):
            await test_agent.execute(invalid_input, execution_context)
    
    def test_agent_performance_metrics(self, test_agent):
        """Test agent performance metrics calculation"""
        # Initially no metrics
        metrics = test_agent.get_performance_metrics()
        assert metrics == {}
        
        # Add some mock execution history
        test_agent.execution_history = [
            AgentOutput(
                agent_type=AgentType.DECOMPOSER,
                session_id="test",
                interaction_id="1",
                status=AgentStatus.COMPLETED,
                data={},
                execution_time=1.0,
                quality_score=0.8
            ),
            AgentOutput(
                agent_type=AgentType.DECOMPOSER,
                session_id="test",
                interaction_id="2",
                status=AgentStatus.FAILED,
                data={},
                execution_time=0.5,
                error_message="Test error"
            )
        ]
        
        metrics = test_agent.get_performance_metrics()
        assert metrics['total_executions'] == 2
        assert metrics['successful_executions'] == 1
        assert metrics['failed_executions'] == 1
        assert metrics['success_rate'] == 0.5
        assert metrics['average_execution_time'] == 1.0
        assert metrics['average_quality_score'] == 0.8


class TestAgentFactory:
    """Test AgentFactory functionality"""
    
    def test_agent_registration(self):
        """Test agent registration with factory"""
        AgentFactory.register_agent(AgentType.DECOMPOSER, TestAgent)
        
        assert AgentFactory.is_registered(AgentType.DECOMPOSER)
        assert AgentType.DECOMPOSER in AgentFactory.get_registered_types()
    
    def test_agent_creation(self):
        """Test agent creation through factory"""
        AgentFactory.register_agent(AgentType.DECOMPOSER, TestAgent)
        
        agent = AgentFactory.create_agent(AgentType.DECOMPOSER)
        
        assert isinstance(agent, TestAgent)
        assert agent.agent_type == AgentType.DECOMPOSER
    
    def test_agent_creation_with_config(self):
        """Test agent creation with custom config"""
        AgentFactory.register_agent(AgentType.DECOMPOSER, TestAgent)
        
        custom_config = AgentConfig(
            agent_type=AgentType.DECOMPOSER,
            temperature=0.5,
            max_retries=5
        )
        
        agent = AgentFactory.create_agent(AgentType.DECOMPOSER, custom_config)
        
        assert agent.config.temperature == 0.5
        assert agent.config.max_retries == 5


if __name__ == "__main__":
    pytest.main([__file__])