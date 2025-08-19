"""
Thinking process related Pydantic models
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FlowStepStatus(str, Enum):
    """Status of a flow step"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ComplexityLevel(str, Enum):
    """Question complexity levels"""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class QuestionRelationship(str, Enum):
    """Types of relationships between questions"""

    PREREQUISITE = "prerequisite"
    PARALLEL = "parallel"
    DEPENDENT = "dependent"
    SUPPORTING = "supporting"


class Priority(str, Enum):
    """Priority levels"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SessionStatus(str, Enum):
    """Thinking session status"""

    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class SubQuestion(BaseModel):
    """Individual sub-question from decomposition"""

    id: str = Field(..., description="Unique identifier for the sub-question")
    question: str = Field(..., description="The sub-question text")
    priority: Priority = Field(..., description="Priority level of this sub-question")
    search_keywords: List[str] = Field(..., description="Keywords for evidence search")
    expected_perspectives: List[str] = Field(
        default_factory=list, description="Expected viewpoints to explore"
    )
    potential_controversies: List[str] = Field(
        default_factory=list, description="Potential controversial aspects"
    )
    domain_context: Optional[str] = Field(
        default=None, description="Domain or context for this question"
    )
    estimated_complexity: ComplexityLevel = Field(
        default=ComplexityLevel.MODERATE, description="Estimated complexity"
    )


class QuestionRelationshipLink(BaseModel):
    """Relationship between questions"""

    from_question_id: str = Field(..., description="Source question ID")
    to_question_id: str = Field(..., description="Target question ID")
    relationship: QuestionRelationship = Field(..., description="Type of relationship")
    strength: float = Field(default=1.0, description="Strength of relationship (0-1)")
    description: Optional[str] = Field(
        default=None, description="Description of the relationship"
    )


class QuestionDecomposition(BaseModel):
    """Result of question decomposition process"""

    main_question: str = Field(..., description="Original main question")
    complexity_assessment: ComplexityLevel = Field(
        ..., description="Assessed complexity level"
    )
    sub_questions: List[SubQuestion] = Field(..., description="List of sub-questions")
    question_relationships: List[QuestionRelationshipLink] = Field(
        default_factory=list, description="Relationships between questions"
    )
    decomposition_strategy: str = Field(
        ..., description="Strategy used for decomposition"
    )
    total_estimated_time: Optional[int] = Field(
        default=None, description="Estimated total processing time in minutes"
    )
    recommended_approach: Optional[str] = Field(
        default=None, description="Recommended approach for tackling the questions"
    )


class ThinkingTrace(BaseModel):
    """Individual step in the thinking process"""

    id: str = Field(..., description="Unique trace identifier")
    session_id: str = Field(..., description="Session this trace belongs to")
    step_number: int = Field(..., description="Sequential step number")
    agent_type: str = Field(..., description="Type of agent that generated this trace")
    role: str = Field(..., description="Role or perspective taken")
    thought_content: str = Field(..., description="The actual thought or reasoning")
    evidence_references: List[str] = Field(
        default_factory=list, description="References to evidence sources"
    )
    evaluation_scores: Optional[Dict[str, float]] = Field(
        default=None, description="Quality evaluation scores"
    )
    bias_flags: Optional[List[str]] = Field(
        default=None, description="Detected cognitive biases"
    )
    confidence_level: Optional[float] = Field(
        default=None, description="Confidence in this reasoning step"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="When this trace was created"
    )
    parent_trace_id: Optional[str] = Field(
        default=None, description="Parent trace if this is a sub-thought"
    )


class ThinkingSession(BaseModel):
    """Complete thinking session"""

    id: str = Field(..., description="Unique session identifier")
    user_id: Optional[str] = Field(
        default=None, description="User who initiated the session"
    )
    topic: str = Field(..., description="Main topic or question being explored")
    session_type: str = Field(
        default="comprehensive_analysis", description="Type of thinking session"
    )
    status: SessionStatus = Field(
        default=SessionStatus.ACTIVE, description="Current session status"
    )
    start_time: datetime = Field(
        default_factory=datetime.now, description="Session start time"
    )
    end_time: Optional[datetime] = Field(default=None, description="Session end time")
    configuration: Dict[str, Any] = Field(
        default_factory=dict, description="Session configuration"
    )
    decomposition: Optional[QuestionDecomposition] = Field(
        default=None, description="Question decomposition results"
    )
    thinking_traces: List[ThinkingTrace] = Field(
        default_factory=list, description="All thinking traces in this session"
    )
    final_results: Optional[Dict[str, Any]] = Field(
        default=None, description="Final analysis results"
    )
    quality_metrics: Optional[Dict[str, float]] = Field(
        default=None, description="Overall quality metrics"
    )
    total_execution_time: Optional[float] = Field(
        default=None, description="Total execution time in seconds"
    )
    agent_interactions_count: int = Field(
        default=0, description="Total number of agent interactions"
    )


class FlowStep(BaseModel):
    """Individual step in a thinking flow"""

    step_id: str = Field(..., description="Unique step identifier")
    agent_type: str = Field(..., description="Agent type to execute")
    step_name: str = Field(..., description="Human-readable step name")
    description: Optional[str] = Field(default=None, description="Step description")
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Step-specific configuration"
    )
    conditions: Optional[Dict[str, Any]] = Field(
        default=None, description="Conditions for step execution"
    )
    parallel: bool = Field(
        default=False, description="Whether this step can run in parallel"
    )
    for_each: Optional[str] = Field(default=None, description="Field to iterate over")
    repeat_until: Optional[str] = Field(
        default=None, description="Condition to repeat until"
    )
    timeout_seconds: Optional[int] = Field(default=None, description="Step timeout")
    retry_config: Optional[Dict[str, Any]] = Field(
        default=None, description="Retry configuration"
    )
    dependencies: List[str] = Field(
        default_factory=list, description="List of step IDs this step depends on"
    )
    
    # State management fields
    status: FlowStepStatus = Field(default=FlowStepStatus.PENDING, description="Step status")
    start_time: Optional[datetime] = Field(default=None, description="Step start time")
    end_time: Optional[datetime] = Field(default=None, description="Step end time")
    result: Optional[str] = Field(default=None, description="Step result")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    quality_score: Optional[float] = Field(default=None, description="Quality score")
    retry_count: int = Field(default=0, description="Number of retries attempted")
    max_retries: int = Field(default=3, description="Maximum number of retries")

    def start(self):
        """Mark step as started"""
        self.status = FlowStepStatus.IN_PROGRESS
        self.start_time = datetime.now()

    def complete(self, result: str, quality_score: Optional[float] = None):
        """Mark step as completed"""
        self.status = FlowStepStatus.COMPLETED
        self.end_time = datetime.now()
        self.result = result
        if quality_score is not None:
            self.quality_score = quality_score

    def fail(self, error_message: str):
        """Mark step as failed"""
        self.status = FlowStepStatus.FAILED
        self.end_time = datetime.now()
        self.error_message = error_message
        self.retry_count += 1

    def can_retry(self) -> bool:
        """Check if step can be retried"""
        return (
            self.retry_count < self.max_retries and self.status == FlowStepStatus.FAILED
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary"""
        return {
            "step_id": self.step_id,
            "step_name": self.step_name,
            "agent_type": self.agent_type,
            "description": self.description,
            "config": self.config,
            "conditions": self.conditions,
            "parallel": self.parallel,
            "for_each": self.for_each,
            "repeat_until": self.repeat_until,
            "timeout_seconds": self.timeout_seconds,
            "retry_config": self.retry_config,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "result": self.result,
            "error_message": self.error_message,
            "quality_score": self.quality_score,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }


class ThinkingFlow(BaseModel):
    """Complete thinking flow definition"""

    name: str = Field(..., description="Flow name")
    description: Optional[str] = Field(default=None, description="Flow description")
    version: str = Field(default="1.0", description="Flow version")
    steps: List[FlowStep] = Field(..., description="Ordered list of flow steps")
    error_handling: Optional[Dict[str, Any]] = Field(
        default=None, description="Error handling configuration"
    )
    global_config: Dict[str, Any] = Field(
        default_factory=dict, description="Global flow configuration"
    )
    prerequisites: List[str] = Field(
        default_factory=list, description="Prerequisites for this flow"
    )
    expected_outputs: List[str] = Field(
        default_factory=list, description="Expected output types"
    )
    estimated_duration: Optional[int] = Field(
        default=None, description="Estimated duration in minutes"
    )
