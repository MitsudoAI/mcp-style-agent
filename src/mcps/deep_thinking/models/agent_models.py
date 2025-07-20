"""
Agent-related Pydantic models and DTOs
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AgentType(str, Enum):
    """Enumeration of available agent types"""

    DECOMPOSER = "decomposer"
    EVIDENCE_SEEKER = "evidence_seeker"
    DEBATE_ORCHESTRATOR = "debate_orchestrator"
    CRITIC = "critic"
    BIAS_BUSTER = "bias_buster"
    INNOVATOR = "innovator"
    REFLECTOR = "reflector"


class AgentStatus(str, Enum):
    """Agent execution status"""

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class AgentInput(BaseModel):
    """Standard input interface for all agents"""

    model_config = ConfigDict(extra="allow")

    session_id: str = Field(..., description="Unique session identifier")
    agent_type: AgentType = Field(..., description="Type of agent being invoked")
    data: Dict[str, Any] = Field(..., description="Agent-specific input data")
    context: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional context information"
    )
    config: Optional[Dict[str, Any]] = Field(
        default=None, description="Agent-specific configuration"
    )
    parent_interaction_id: Optional[str] = Field(
        default=None, description="ID of parent interaction if this is a sub-task"
    )


class AgentOutput(BaseModel):
    """Standard output interface for all agents"""

    model_config = ConfigDict(extra="allow")

    agent_type: AgentType = Field(
        ..., description="Type of agent that produced this output"
    )
    session_id: str = Field(..., description="Session identifier")
    interaction_id: str = Field(..., description="Unique interaction identifier")
    status: AgentStatus = Field(..., description="Execution status")
    data: Dict[str, Any] = Field(..., description="Agent-specific output data")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Execution metadata"
    )
    execution_time: Optional[float] = Field(
        default=None, description="Execution time in seconds"
    )
    quality_score: Optional[float] = Field(
        default=None, description="Quality score of the output"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if execution failed"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Timestamp of completion"
    )


class AgentConfig(BaseModel):
    """Configuration for agent behavior"""

    model_config = ConfigDict(extra="allow")

    agent_type: AgentType = Field(..., description="Type of agent")
    enabled: bool = Field(default=True, description="Whether the agent is enabled")
    max_retries: int = Field(default=3, description="Maximum number of retry attempts")
    timeout_seconds: int = Field(default=300, description="Timeout for agent execution")
    temperature: float = Field(default=0.7, description="LLM temperature parameter")
    model_name: Optional[str] = Field(
        default=None, description="Specific LLM model to use"
    )
    custom_prompts: Optional[Dict[str, str]] = Field(
        default=None, description="Custom prompt templates"
    )
    quality_threshold: float = Field(
        default=0.8, description="Minimum quality threshold"
    )
    specific_config: Optional[Dict[str, Any]] = Field(
        default=None, description="Agent-specific configuration"
    )


class AgentMetadata(BaseModel):
    """Metadata about agent capabilities and requirements"""

    agent_type: AgentType = Field(..., description="Type of agent")
    name: str = Field(..., description="Human-readable agent name")
    description: str = Field(..., description="Description of agent capabilities")
    version: str = Field(..., description="Agent version")
    required_inputs: List[str] = Field(..., description="Required input fields")
    optional_inputs: List[str] = Field(
        default_factory=list, description="Optional input fields"
    )
    output_schema: Dict[str, Any] = Field(
        ..., description="JSON schema of expected output"
    )
    dependencies: List[AgentType] = Field(
        default_factory=list, description="Agent dependencies"
    )
    capabilities: List[str] = Field(
        default_factory=list, description="List of agent capabilities"
    )
    limitations: List[str] = Field(
        default_factory=list, description="Known limitations"
    )


class AgentExecutionContext(BaseModel):
    """Context information for agent execution"""

    session_id: str = Field(..., description="Current session ID")
    user_id: Optional[str] = Field(default=None, description="User identifier")
    flow_step: int = Field(..., description="Current step in the thinking flow")
    previous_outputs: List[AgentOutput] = Field(
        default_factory=list, description="Previous agent outputs in this session"
    )
    shared_context: Dict[str, Any] = Field(
        default_factory=dict, description="Shared context across agents"
    )
    execution_mode: str = Field(
        default="normal", description="Execution mode (normal, debug, test)"
    )
    resource_limits: Optional[Dict[str, Any]] = Field(
        default=None, description="Resource usage limits"
    )


class AgentRegistration(BaseModel):
    """Agent registration information"""

    agent_type: AgentType = Field(..., description="Type of agent")
    class_name: str = Field(..., description="Python class name")
    module_path: str = Field(..., description="Python module path")
    metadata: AgentMetadata = Field(..., description="Agent metadata")
    config: AgentConfig = Field(..., description="Default configuration")
    is_active: bool = Field(default=True, description="Whether the agent is active")
    registration_time: datetime = Field(
        default_factory=datetime.now, description="Registration timestamp"
    )
