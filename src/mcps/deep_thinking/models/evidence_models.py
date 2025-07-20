"""
Evidence and search related Pydantic models
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


class SourceType(str, Enum):
    """Types of evidence sources"""

    ACADEMIC = "academic"
    NEWS = "news"
    GOVERNMENT = "government"
    BLOG = "blog"
    WIKI = "wiki"
    FORUM = "forum"
    SOCIAL_MEDIA = "social_media"
    BOOK = "book"
    REPORT = "report"
    OTHER = "other"


class SearchStrategy(str, Enum):
    """Search strategies for evidence gathering"""

    COMPREHENSIVE = "comprehensive"
    FOCUSED = "focused"
    DIVERSE = "diverse"
    ACADEMIC_ONLY = "academic_only"
    RECENT_ONLY = "recent_only"


class CredibilityLevel(str, Enum):
    """Credibility assessment levels"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class SearchQuery(BaseModel):
    """Search query configuration"""

    query_text: str = Field(..., description="The search query text")
    keywords: List[str] = Field(..., description="Key search terms")
    domain_filters: List[str] = Field(
        default_factory=list, description="Domain restrictions"
    )
    source_type_filters: List[SourceType] = Field(
        default_factory=list, description="Source type filters"
    )
    date_range: Optional[Dict[str, str]] = Field(
        default=None, description="Date range for search"
    )
    language: str = Field(default="en", description="Language preference")
    max_results: int = Field(default=10, description="Maximum number of results")
    strategy: SearchStrategy = Field(
        default=SearchStrategy.COMPREHENSIVE, description="Search strategy"
    )


class EvidenceSource(BaseModel):
    """Individual evidence source"""

    id: str = Field(..., description="Unique source identifier")
    url: Optional[HttpUrl] = Field(default=None, description="Source URL")
    title: str = Field(..., description="Source title")
    summary: str = Field(..., description="Content summary")
    full_content: Optional[str] = Field(
        default=None, description="Full content if available"
    )
    credibility_score: float = Field(
        ..., ge=0.0, le=1.0, description="Credibility score (0-1)"
    )
    credibility_level: CredibilityLevel = Field(
        ..., description="Assessed credibility level"
    )
    source_type: SourceType = Field(..., description="Type of source")
    publication_date: Optional[str] = Field(
        default=None, description="Publication date"
    )
    author: Optional[str] = Field(default=None, description="Author information")
    key_claims: List[str] = Field(
        default_factory=list, description="Key claims from this source"
    )
    supporting_evidence: List[str] = Field(
        default_factory=list, description="Supporting evidence mentioned"
    )
    citation_count: int = Field(default=0, description="Number of times cited")
    relevance_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Relevance to query"
    )
    bias_indicators: List[str] = Field(
        default_factory=list, description="Potential bias indicators"
    )
    fact_check_status: Optional[str] = Field(
        default=None, description="Fact-checking status if available"
    )
    retrieved_at: datetime = Field(
        default_factory=datetime.now, description="When this source was retrieved"
    )


class ConflictingInformation(BaseModel):
    """Information that conflicts between sources"""

    claim_a: str = Field(..., description="First conflicting claim")
    claim_b: str = Field(..., description="Second conflicting claim")
    source_a_ids: List[str] = Field(..., description="Sources supporting claim A")
    source_b_ids: List[str] = Field(..., description="Sources supporting claim B")
    conflict_type: str = Field(
        ..., description="Type of conflict (factual, interpretive, etc.)"
    )
    severity: float = Field(..., ge=0.0, le=1.0, description="Severity of conflict")
    resolution_suggestion: Optional[str] = Field(
        default=None, description="Suggested resolution approach"
    )
    requires_further_investigation: bool = Field(
        default=False, description="Whether more investigation is needed"
    )


class EvidenceCollection(BaseModel):
    """Collection of evidence for a specific query or topic"""

    query_used: SearchQuery = Field(
        ..., description="Query that generated this collection"
    )
    sources: List[EvidenceSource] = Field(..., description="List of evidence sources")
    total_sources_found: int = Field(..., description="Total number of sources found")
    source_diversity_score: float = Field(
        ..., ge=0.0, le=1.0, description="Diversity score of sources"
    )
    average_credibility: float = Field(
        ..., ge=0.0, le=1.0, description="Average credibility of sources"
    )
    conflicting_information: List[ConflictingInformation] = Field(
        default_factory=list, description="Detected conflicts"
    )
    coverage_assessment: Optional[str] = Field(
        default=None, description="Assessment of topic coverage"
    )
    gaps_identified: List[str] = Field(
        default_factory=list, description="Identified information gaps"
    )
    search_quality_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Overall search quality"
    )
    collection_timestamp: datetime = Field(
        default_factory=datetime.now, description="When collection was created"
    )
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Last update timestamp"
    )


class SearchResult(BaseModel):
    """Raw search result before processing"""

    query: str = Field(..., description="Original search query")
    url: Optional[HttpUrl] = Field(default=None, description="Result URL")
    title: str = Field(..., description="Result title")
    snippet: str = Field(..., description="Result snippet/description")
    rank: int = Field(..., description="Search result ranking")
    search_engine: str = Field(..., description="Search engine used")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    retrieved_at: datetime = Field(
        default_factory=datetime.now, description="Retrieval timestamp"
    )


class SearchSession(BaseModel):
    """Complete search session"""

    session_id: str = Field(..., description="Unique session identifier")
    queries: List[SearchQuery] = Field(..., description="All queries in this session")
    raw_results: List[SearchResult] = Field(
        default_factory=list, description="Raw search results"
    )
    processed_evidence: List[EvidenceCollection] = Field(
        default_factory=list, description="Processed evidence collections"
    )
    search_strategy_used: SearchStrategy = Field(
        ..., description="Overall search strategy"
    )
    total_search_time: Optional[float] = Field(
        default=None, description="Total search time in seconds"
    )
    success_rate: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Success rate of searches"
    )
    session_start: datetime = Field(
        default_factory=datetime.now, description="Session start time"
    )
    session_end: Optional[datetime] = Field(
        default=None, description="Session end time"
    )
