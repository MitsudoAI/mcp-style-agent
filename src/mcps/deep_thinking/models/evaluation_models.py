"""
Evaluation and assessment related Pydantic models
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BiasType(str, Enum):
    """Types of cognitive biases"""

    CONFIRMATION_BIAS = "confirmation_bias"
    ANCHORING = "anchoring"
    AVAILABILITY_HEURISTIC = "availability_heuristic"
    REPRESENTATIVENESS = "representativeness"
    OVERCONFIDENCE = "overconfidence"
    HINDSIGHT_BIAS = "hindsight_bias"
    FRAMING_EFFECT = "framing_effect"
    SUNK_COST_FALLACY = "sunk_cost_fallacy"
    GROUPTHINK = "groupthink"
    HALO_EFFECT = "halo_effect"


class LogicalFallacy(str, Enum):
    """Types of logical fallacies"""

    AD_HOMINEM = "ad_hominem"
    STRAW_MAN = "straw_man"
    FALSE_DICHOTOMY = "false_dichotomy"
    SLIPPERY_SLOPE = "slippery_slope"
    CIRCULAR_REASONING = "circular_reasoning"
    HASTY_GENERALIZATION = "hasty_generalization"
    APPEAL_TO_AUTHORITY = "appeal_to_authority"
    APPEAL_TO_EMOTION = "appeal_to_emotion"
    RED_HERRING = "red_herring"
    BANDWAGON = "bandwagon"


class InnovationMethod(str, Enum):
    """Innovation methods"""

    SCAMPER = "SCAMPER"
    TRIZ = "TRIZ"
    LATERAL_THINKING = "lateral_thinking"
    DESIGN_THINKING = "design_thinking"
    BRAINSTORMING = "brainstorming"


class ReflectionType(str, Enum):
    """Types of reflection"""

    PROCESS = "process"
    OUTCOME = "outcome"
    METACOGNITIVE = "metacognitive"
    EMOTIONAL = "emotional"


class PaulElderDimension(BaseModel):
    """Individual Paul-Elder evaluation dimension"""

    score: float = Field(
        ..., ge=0.0, le=1.0, description="Score for this dimension (0-1)"
    )
    feedback: str = Field(..., description="Detailed feedback for this dimension")
    evidence: List[str] = Field(
        default_factory=list, description="Evidence supporting this score"
    )
    improvement_suggestions: List[str] = Field(
        default_factory=list, description="Specific improvement suggestions"
    )


class PaulElderEvaluation(BaseModel):
    """Complete Paul-Elder critical thinking evaluation"""

    overall_score: float = Field(
        ..., ge=0.0, le=1.0, description="Overall evaluation score"
    )
    detailed_scores: Dict[str, PaulElderDimension] = Field(
        ..., description="Scores for each of the 9 dimensions"
    )
    content_evaluated: str = Field(..., description="The content that was evaluated")
    evaluation_context: Optional[str] = Field(
        default=None, description="Context for the evaluation"
    )
    strengths: List[str] = Field(
        default_factory=list, description="Identified strengths"
    )
    weaknesses: List[str] = Field(
        default_factory=list, description="Identified weaknesses"
    )
    improvement_suggestions: List[str] = Field(
        default_factory=list, description="Overall improvement suggestions"
    )
    requires_revision: bool = Field(..., description="Whether revision is required")
    revision_priority: str = Field(..., description="Priority level for revision")
    logical_fallacies: List[LogicalFallacy] = Field(
        default_factory=list, description="Detected logical fallacies"
    )
    evaluation_timestamp: datetime = Field(
        default_factory=datetime.now, description="When evaluation was performed"
    )
    evaluator_confidence: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Evaluator's confidence in assessment"
    )


class DetectedBias(BaseModel):
    """Individual detected cognitive bias"""

    bias_type: BiasType = Field(..., description="Type of bias detected")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in detection"
    )
    evidence_text: str = Field(..., description="Text evidence of the bias")
    explanation: str = Field(
        ..., description="Explanation of why this is considered biased"
    )
    severity: float = Field(..., ge=0.0, le=1.0, description="Severity of the bias")
    mitigation_strategies: List[str] = Field(
        ..., description="Suggested strategies to mitigate this bias"
    )
    context: Optional[str] = Field(
        default=None, description="Context where bias was detected"
    )


class BiasAnalysis(BaseModel):
    """Complete bias analysis results"""

    content_analyzed: str = Field(..., description="Content that was analyzed for bias")
    detected_biases: List[DetectedBias] = Field(
        ..., description="List of detected biases"
    )
    overall_bias_score: float = Field(
        ..., ge=0.0, le=1.0, description="Overall bias score (higher = more biased)"
    )
    bias_categories: Dict[str, int] = Field(
        default_factory=dict, description="Count of biases by category"
    )
    recommendations: List[Dict[str, str]] = Field(
        default_factory=list, description="Actionable recommendations"
    )
    debiasing_techniques: List[str] = Field(
        default_factory=list, description="Suggested debiasing techniques"
    )
    analysis_timestamp: datetime = Field(
        default_factory=datetime.now, description="When analysis was performed"
    )
    requires_attention: bool = Field(
        default=False, description="Whether immediate attention is required"
    )


class DebateParticipant(BaseModel):
    """Individual debate participant"""

    agent_id: str = Field(..., description="Unique agent identifier")
    position: str = Field(..., description="Position or stance taken")
    role: str = Field(..., description="Role in the debate")
    arguments: List[Dict[str, Any]] = Field(
        default_factory=list, description="Arguments presented"
    )
    evidence_cited: List[str] = Field(
        default_factory=list, description="Evidence sources cited"
    )
    rebuttals_made: List[str] = Field(
        default_factory=list, description="Rebuttals to other participants"
    )
    quality_score: Optional[float] = Field(
        default=None, description="Quality score of participation"
    )


class DebateResults(BaseModel):
    """Results from multi-agent debate"""

    topic: str = Field(..., description="Debate topic")
    participants: List[DebateParticipant] = Field(
        ..., description="All debate participants"
    )
    total_rounds: int = Field(..., description="Total number of debate rounds")
    key_disagreements: List[str] = Field(
        default_factory=list, description="Major points of disagreement"
    )
    consensus_points: List[str] = Field(
        default_factory=list, description="Points of consensus"
    )
    unresolved_issues: List[str] = Field(
        default_factory=list, description="Issues that remain unresolved"
    )
    strongest_arguments: List[Dict[str, str]] = Field(
        default_factory=list, description="Strongest arguments identified"
    )
    weakest_arguments: List[Dict[str, str]] = Field(
        default_factory=list, description="Weakest arguments identified"
    )
    debate_quality_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Overall debate quality"
    )
    debate_duration: Optional[float] = Field(
        default=None, description="Debate duration in seconds"
    )
    debate_timestamp: datetime = Field(
        default_factory=datetime.now, description="When debate occurred"
    )


class InnovationIdea(BaseModel):
    """Individual innovation idea"""

    idea: str = Field(..., description="The innovation idea")
    technique_applied: str = Field(
        ..., description="Innovation technique used to generate this idea"
    )
    novelty_score: float = Field(
        ..., ge=0.0, le=1.0, description="Novelty assessment score"
    )
    feasibility_score: float = Field(
        ..., ge=0.0, le=1.0, description="Feasibility assessment score"
    )
    potential_impact: str = Field(..., description="Assessment of potential impact")
    implementation_steps: List[str] = Field(
        default_factory=list, description="Suggested implementation steps"
    )
    required_resources: List[str] = Field(
        default_factory=list, description="Resources required for implementation"
    )
    risks: List[str] = Field(default_factory=list, description="Identified risks")
    success_factors: List[str] = Field(
        default_factory=list, description="Critical success factors"
    )


class InnovationResults(BaseModel):
    """Results from innovation thinking process"""

    base_concept: str = Field(..., description="Original concept being innovated upon")
    method_used: InnovationMethod = Field(..., description="Innovation method applied")
    generated_ideas: List[InnovationIdea] = Field(
        ..., description="Generated innovation ideas"
    )
    cross_domain_applications: List[str] = Field(
        default_factory=list, description="Cross-domain applications identified"
    )
    breakthrough_potential: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Assessment of breakthrough potential"
    )
    implementation_complexity: str = Field(
        default="medium", description="Overall implementation complexity"
    )
    risk_assessment: List[str] = Field(
        default_factory=list, description="Overall risk assessment"
    )
    next_steps: List[str] = Field(
        default_factory=list, description="Recommended next steps"
    )
    innovation_timestamp: datetime = Field(
        default_factory=datetime.now, description="When innovation session occurred"
    )


class SocraticQuestion(BaseModel):
    """Individual Socratic question"""

    question: str = Field(..., description="The Socratic question")
    purpose: str = Field(..., description="Purpose of this question")
    expected_insight: str = Field(..., description="Expected insight from answering")
    question_type: str = Field(..., description="Type of Socratic question")
    difficulty_level: str = Field(
        default="medium", description="Difficulty level of the question"
    )


class ReflectionGuidance(BaseModel):
    """Guidance for reflection process"""

    reflection_type: ReflectionType = Field(
        ..., description="Type of reflection being guided"
    )
    socratic_questions: List[SocraticQuestion] = Field(
        ..., description="Socratic questions for reflection"
    )
    metacognitive_prompts: List[str] = Field(
        default_factory=list, description="Metacognitive prompts"
    )
    self_assessment_framework: Dict[str, Any] = Field(
        default_factory=dict, description="Framework for self-assessment"
    )
    reflection_template: Optional[str] = Field(
        default=None, description="Template for structured reflection"
    )
    improvement_areas: List[str] = Field(
        default_factory=list, description="Areas identified for improvement"
    )
    strengths_identified: List[str] = Field(
        default_factory=list, description="Strengths identified during reflection"
    )
    action_items: List[str] = Field(
        default_factory=list, description="Action items from reflection"
    )
    reflection_quality_indicators: List[str] = Field(
        default_factory=list, description="Indicators of quality reflection"
    )
    guidance_timestamp: datetime = Field(
        default_factory=datetime.now, description="When guidance was generated"
    )


class ContradictionDetection(BaseModel):
    """Detected contradiction in reasoning"""

    statement_a: str = Field(..., description="First contradictory statement")
    statement_b: str = Field(..., description="Second contradictory statement")
    contradiction_type: str = Field(..., description="Type of contradiction")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in contradiction detection"
    )
    severity: float = Field(
        ..., ge=0.0, le=1.0, description="Severity of the contradiction"
    )
    resolution_suggestions: List[str] = Field(
        default_factory=list, description="Suggestions for resolving contradiction"
    )
    context: Optional[str] = Field(
        default=None, description="Context where contradiction was found"
    )
    requires_clarification: bool = Field(
        default=False, description="Whether clarification is needed"
    )
