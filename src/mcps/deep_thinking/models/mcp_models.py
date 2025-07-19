"""
MCP (Model Context Protocol) specific data models and interfaces
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class MCPToolName(str, Enum):
    """Available MCP tools for deep thinking"""
    START_THINKING = "start_thinking"
    NEXT_STEP = "next_step"
    ANALYZE_STEP = "analyze_step"
    COMPLETE_THINKING = "complete_thinking"


class MCPToolInput(BaseModel):
    """Standard input for MCP tools"""
    model_config = ConfigDict(extra='allow')
    
    tool_name: MCPToolName = Field(..., description="Name of the MCP tool being called")
    parameters: Dict[str, Any] = Field(..., description="Tool-specific parameters")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class MCPToolOutput(BaseModel):
    """Standard output from MCP tools - returns Prompt templates, not processed results"""
    model_config = ConfigDict(extra='allow')
    
    tool_name: MCPToolName = Field(..., description="Name of the MCP tool")
    session_id: Optional[str] = Field(default=None, description="Session identifier if applicable")
    step: Optional[str] = Field(default=None, description="Current step name")
    prompt_template: str = Field(..., description="Prompt template for the LLM to execute")
    instructions: str = Field(..., description="Instructions for how to use the prompt")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Context information")
    next_action: Optional[str] = Field(default=None, description="Suggested next action")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class StartThinkingInput(BaseModel):
    """Input for start_thinking MCP tool"""
    
    topic: str = Field(..., description="Main topic or question to analyze")
    complexity: str = Field(default="moderate", description="Complexity level: simple, moderate, complex")
    focus: str = Field(default="", description="Specific focus or angle")
    flow_type: str = Field(default="comprehensive_analysis", description="Type of thinking flow to use")


class NextStepInput(BaseModel):
    """Input for next_step MCP tool"""
    
    session_id: str = Field(..., description="Session identifier")
    step_result: str = Field(..., description="Result from the previous step")
    quality_feedback: Optional[Dict[str, Any]] = Field(default=None, description="Quality feedback if any")


class AnalyzeStepInput(BaseModel):
    """Input for analyze_step MCP tool"""
    
    session_id: str = Field(..., description="Session identifier")
    step_name: str = Field(..., description="Name of the step to analyze")
    step_result: str = Field(..., description="Result from the step")
    analysis_type: str = Field(default="quality", description="Type of analysis to perform")


class CompleteThinkingInput(BaseModel):
    """Input for complete_thinking MCP tool"""
    
    session_id: str = Field(..., description="Session identifier")
    final_insights: Optional[str] = Field(default=None, description="Any final insights to include")


class PromptTemplate(BaseModel):
    """Prompt template definition"""
    
    template_id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Human-readable template name")
    description: str = Field(..., description="Template description")
    template_content: str = Field(..., description="The actual prompt template")
    parameters: List[str] = Field(default_factory=list, description="Required parameters")
    category: str = Field(..., description="Template category (decomposition, evidence, etc.)")
    version: str = Field(default="1.0", description="Template version")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")


class SessionState(BaseModel):
    """Current state of a thinking session"""
    
    session_id: str = Field(..., description="Unique session identifier")
    topic: str = Field(..., description="Main topic being analyzed")
    current_step: str = Field(..., description="Current step in the flow")
    step_number: int = Field(default=0, description="Current step number")
    flow_type: str = Field(..., description="Type of thinking flow")
    status: str = Field(default="active", description="Session status")
    step_results: Dict[str, Any] = Field(default_factory=dict, description="Results from completed steps")
    context: Dict[str, Any] = Field(default_factory=dict, description="Session context")
    quality_scores: Dict[str, float] = Field(default_factory=dict, description="Quality scores for steps")
    created_at: datetime = Field(default_factory=datetime.now, description="Session creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")


class FlowDefinition(BaseModel):
    """Definition of a thinking flow"""
    
    flow_name: str = Field(..., description="Name of the flow")
    description: str = Field(..., description="Flow description")
    steps: List[Dict[str, Any]] = Field(..., description="Ordered list of flow steps")
    entry_conditions: Optional[Dict[str, Any]] = Field(default=None, description="Conditions for using this flow")
    quality_gates: Optional[Dict[str, float]] = Field(default=None, description="Quality thresholds for steps")
    estimated_duration: Optional[int] = Field(default=None, description="Estimated duration in minutes")


class ErrorRecoveryPrompt(BaseModel):
    """Prompt template for error recovery scenarios"""
    
    error_type: str = Field(..., description="Type of error that occurred")
    error_message: str = Field(..., description="Error message")
    recovery_prompt: str = Field(..., description="Prompt to help recover from the error")
    recovery_options: List[str] = Field(default_factory=list, description="Available recovery options")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Error context")