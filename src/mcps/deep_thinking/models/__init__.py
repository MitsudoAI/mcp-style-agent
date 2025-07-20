"""
Deep Thinking Engine - Core Data Models

This module contains all the Pydantic models and data transfer objects (DTOs)
used throughout the deep thinking engine system.
"""

# Import models explicitly to avoid linting issues
from .agent_models import AgentConfig, AgentInput, AgentMetadata, AgentOutput
from .evaluation_models import (
    BiasAnalysis,
    DebateResults,
    InnovationResults,
    PaulElderEvaluation,
    ReflectionGuidance,
)
from .evidence_models import (
    ConflictingInformation,
    EvidenceCollection,
    EvidenceSource,
    SearchQuery,
)
from .thinking_models import (
    QuestionDecomposition,
    SubQuestion,
    ThinkingSession,
    ThinkingTrace,
)

__all__ = [
    # Agent Models
    "AgentInput",
    "AgentOutput",
    "AgentConfig",
    "AgentMetadata",
    # Thinking Models
    "ThinkingSession",
    "ThinkingTrace",
    "QuestionDecomposition",
    "SubQuestion",
    # Evidence Models
    "EvidenceSource",
    "EvidenceCollection",
    "SearchQuery",
    "ConflictingInformation",
    # Evaluation Models
    "PaulElderEvaluation",
    "BiasAnalysis",
    "DebateResults",
    "InnovationResults",
    "ReflectionGuidance",
]
