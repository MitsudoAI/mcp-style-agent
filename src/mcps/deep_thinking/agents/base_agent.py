"""
Base Agent class and interface definitions
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
import asyncio
import time
import uuid
from datetime import datetime

from ..models.agent_models import (
    AgentInput, AgentOutput, AgentConfig, AgentMetadata, 
    AgentExecutionContext, AgentType, AgentStatus
)
from ..config.exceptions import (
    AgentExecutionError, AgentTimeoutError, AgentValidationError,
    AgentConfigurationError
)


class AgentInterface(ABC):
    """Abstract interface that all agents must implement"""
    
    @abstractmethod
    async def execute(self, input_data: AgentInput, context: AgentExecutionContext) -> AgentOutput:
        """
        Execute the agent's main functionality
        
        Args:
            input_data: Standardized input data
            context: Execution context with session information
            
        Returns:
            AgentOutput: Standardized output data
            
        Raises:
            AgentExecutionError: If execution fails
            AgentTimeoutError: If execution times out
            AgentValidationError: If input validation fails
        """
        pass
    
    @abstractmethod
    def validate_input(self, input_data: AgentInput) -> bool:
        """
        Validate input data before execution
        
        Args:
            input_data: Input data to validate
            
        Returns:
            bool: True if valid, False otherwise
            
        Raises:
            AgentValidationError: If validation fails with details
        """
        pass
    
    @abstractmethod
    def get_metadata(self) -> AgentMetadata:
        """
        Get agent metadata including capabilities and requirements
        
        Returns:
            AgentMetadata: Agent metadata
        """
        pass
    
    @abstractmethod
    def get_default_config(self) -> AgentConfig:
        """
        Get default configuration for this agent
        
        Returns:
            AgentConfig: Default configuration
        """
        pass


class BaseAgent(AgentInterface):
    """
    Base implementation of the Agent interface with common functionality
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize the base agent
        
        Args:
            config: Agent configuration, uses default if None
        """
        self.config = config or self.get_default_config()
        self.agent_type = self.config.agent_type
        self.execution_history: List[AgentOutput] = []
        self._is_initialized = False
        self._initialization_lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """
        Initialize the agent (called once before first execution)
        Override in subclasses for custom initialization
        """
        async with self._initialization_lock:
            if not self._is_initialized:
                await self._initialize_agent()
                self._is_initialized = True
    
    async def _initialize_agent(self) -> None:
        """
        Internal initialization method - override in subclasses
        """
        pass
    
    async def execute(self, input_data: AgentInput, context: AgentExecutionContext) -> AgentOutput:
        """
        Execute the agent with timeout and error handling
        """
        # Ensure agent is initialized
        await self.initialize()
        
        # Validate input
        if not self.validate_input(input_data):
            raise AgentValidationError(f"Invalid input for {self.agent_type}")
        
        # Create interaction ID
        interaction_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Execute with timeout
            output = await asyncio.wait_for(
                self._execute_internal(input_data, context, interaction_id),
                timeout=self.config.timeout_seconds
            )
            
            # Calculate execution time
            execution_time = time.time() - start_time
            output.execution_time = execution_time
            
            # Store in history
            self.execution_history.append(output)
            
            return output
            
        except asyncio.TimeoutError:
            raise AgentTimeoutError(
                f"Agent {self.agent_type} timed out after {self.config.timeout_seconds} seconds"
            )
        except Exception as e:
            # Create error output
            error_output = AgentOutput(
                agent_type=self.agent_type,
                session_id=input_data.session_id,
                interaction_id=interaction_id,
                status=AgentStatus.FAILED,
                data={},
                execution_time=time.time() - start_time,
                error_message=str(e)
            )
            self.execution_history.append(error_output)
            raise AgentExecutionError(f"Agent {self.agent_type} execution failed: {str(e)}")
    
    @abstractmethod
    async def _execute_internal(
        self, 
        input_data: AgentInput, 
        context: AgentExecutionContext,
        interaction_id: str
    ) -> AgentOutput:
        """
        Internal execution method - must be implemented by subclasses
        
        Args:
            input_data: Validated input data
            context: Execution context
            interaction_id: Unique interaction identifier
            
        Returns:
            AgentOutput: Execution results
        """
        pass
    
    def validate_input(self, input_data: AgentInput) -> bool:
        """
        Basic input validation - can be overridden in subclasses
        """
        try:
            # Check required fields
            if not input_data.session_id:
                raise AgentValidationError("session_id is required")
            
            if input_data.agent_type != self.agent_type:
                raise AgentValidationError(f"Agent type mismatch: expected {self.agent_type}, got {input_data.agent_type}")
            
            # Validate agent-specific requirements
            return self._validate_agent_specific_input(input_data)
            
        except Exception as e:
            raise AgentValidationError(f"Input validation failed: {str(e)}")
    
    def _validate_agent_specific_input(self, input_data: AgentInput) -> bool:
        """
        Agent-specific input validation - override in subclasses
        """
        return True
    
    def get_execution_history(self) -> List[AgentOutput]:
        """
        Get the execution history for this agent instance
        """
        return self.execution_history.copy()
    
    def get_last_execution(self) -> Optional[AgentOutput]:
        """
        Get the last execution result
        """
        return self.execution_history[-1] if self.execution_history else None
    
    def clear_history(self) -> None:
        """
        Clear the execution history
        """
        self.execution_history.clear()
    
    def update_config(self, new_config: AgentConfig) -> None:
        """
        Update agent configuration
        """
        if new_config.agent_type != self.agent_type:
            raise AgentConfigurationError(
                f"Cannot change agent type from {self.agent_type} to {new_config.agent_type}"
            )
        self.config = new_config
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for this agent
        """
        if not self.execution_history:
            return {}
        
        successful_executions = [
            output for output in self.execution_history 
            if output.status == AgentStatus.COMPLETED
        ]
        
        failed_executions = [
            output for output in self.execution_history
            if output.status == AgentStatus.FAILED
        ]
        
        execution_times = [
            output.execution_time for output in successful_executions
            if output.execution_time is not None
        ]
        
        quality_scores = [
            output.quality_score for output in successful_executions
            if output.quality_score is not None
        ]
        
        return {
            'total_executions': len(self.execution_history),
            'successful_executions': len(successful_executions),
            'failed_executions': len(failed_executions),
            'success_rate': len(successful_executions) / len(self.execution_history) if self.execution_history else 0,
            'average_execution_time': sum(execution_times) / len(execution_times) if execution_times else 0,
            'average_quality_score': sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            'last_execution_time': self.execution_history[-1].timestamp if self.execution_history else None
        }
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.agent_type})"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(agent_type={self.agent_type}, config={self.config})"


class AgentFactory:
    """
    Factory class for creating agent instances
    """
    
    _agent_classes: Dict[AgentType, Type[BaseAgent]] = {}
    
    @classmethod
    def register_agent(cls, agent_type: AgentType, agent_class: Type[BaseAgent]) -> None:
        """
        Register an agent class for a specific agent type
        
        Args:
            agent_type: The agent type enum
            agent_class: The agent class to register
        """
        if not issubclass(agent_class, BaseAgent):
            raise AgentConfigurationError(f"Agent class must inherit from BaseAgent")
        
        cls._agent_classes[agent_type] = agent_class
    
    @classmethod
    def create_agent(cls, agent_type: AgentType, config: Optional[AgentConfig] = None) -> BaseAgent:
        """
        Create an agent instance of the specified type
        
        Args:
            agent_type: Type of agent to create
            config: Optional configuration for the agent
            
        Returns:
            BaseAgent: Created agent instance
            
        Raises:
            AgentConfigurationError: If agent type is not registered
        """
        if agent_type not in cls._agent_classes:
            raise AgentConfigurationError(f"Agent type {agent_type} is not registered")
        
        agent_class = cls._agent_classes[agent_type]
        return agent_class(config)
    
    @classmethod
    def get_registered_types(cls) -> List[AgentType]:
        """
        Get list of registered agent types
        """
        return list(cls._agent_classes.keys())
    
    @classmethod
    def is_registered(cls, agent_type: AgentType) -> bool:
        """
        Check if an agent type is registered
        """
        return agent_type in cls._agent_classes