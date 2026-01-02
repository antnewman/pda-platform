"""Data models for outlier mining."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from .config import MiningConfig


class DifferenceType(Enum):
    """Types of differences between candidates."""
    HIGHER = "higher"              # Numeric value is higher
    LOWER = "lower"                # Numeric value is lower
    ALTERNATIVE = "alternative"    # Different categorical value
    ADDITIONAL = "additional"      # Has element others don't
    MISSING = "missing"            # Missing element others have
    STRUCTURAL = "structural"      # Different structure/approach
    ASSUMPTION = "assumption"      # Different underlying assumption


@dataclass
class QualityScore:
    """Quality assessment of a generated response."""
    coherence: float               # 0-1, internal consistency
    relevance: float               # 0-1, addresses the query
    completeness: float            # 0-1, covers required aspects
    semantic_entropy: float        # 0-1, higher = more uncertain/confabulated
    overall: float                 # Composite quality score
    passed_threshold: bool         # Met minimum quality

    @classmethod
    def compute(cls, coherence: float, relevance: float, completeness: float,
                entropy: float, threshold: float = 0.6) -> "QualityScore":
        """Compute quality score from components."""
        # Penalise high entropy (potential hallucination)
        entropy_penalty = max(0, entropy - 0.5) * 0.5
        overall = (coherence * 0.4 + relevance * 0.4 + completeness * 0.2) - entropy_penalty
        return cls(
            coherence=coherence,
            relevance=relevance,
            completeness=completeness,
            semantic_entropy=entropy,
            overall=max(0, overall),
            passed_threshold=overall >= threshold
        )


@dataclass
class DifferenceReport:
    """Details about a difference from consensus."""
    field: str                          # Which field differs
    difference_type: DifferenceType     # Type of difference
    consensus_value: Any                # Consensus value
    candidate_value: Any                # This candidate's value
    magnitude: float = 0.0              # Magnitude of difference (for numeric)
    explanation: str = ""               # Human-readable explanation
    significance: float = 0.5           # How significant is this difference (0-1)


@dataclass
class AssumptionReport:
    """An implicit assumption identified in a candidate."""
    assumption: str                     # The assumption text
    confidence: float                   # Confidence in this extraction (0-1)
    category: str                       # timeline, resource, technical, etc.
    shared_by: list[str] = field(default_factory=list)  # Other candidate IDs with same assumption
    unique_to_candidate: bool = True    # Whether this is unique to this candidate


@dataclass
class ClusterInfo:
    """Information about a cluster of similar responses."""
    cluster_id: str                         # Unique identifier
    size: int                               # Number of samples in cluster
    summary: str                            # LLM-generated summary
    distinctive_theme: str                  # What makes this cluster unique
    sample_indices: list[int]               # Which samples are in this cluster
    centroid_distance: float                # Average distance to centroid
    is_singleton: bool                      # Single-member cluster (true outlier)


@dataclass
class SaturationSignal:
    """Signal about generation saturation."""
    samples_checked: int                    # How many samples checked
    semantic_consistency: float             # Semantic consistency score (0-1)
    structural_consistency: float           # Structural consistency score (0-1)
    should_stop: bool                       # Whether to stop generating
    reason: str                             # Why we should/shouldn't stop


@dataclass
class MiningCandidate:
    """A candidate response from outlier mining."""
    id: str                                      # Unique identifier
    cluster_id: str                              # Which cluster this belongs to
    sample_indices: list[int]                    # Source samples (if representative)
    content: dict[str, Any]                      # Extracted structured content
    raw_response: str                            # Original LLM response text

    # Quality metrics
    quality: QualityScore                        # Quality assessment

    # Characterisation
    approach_summary: str                        # One-line summary of approach
    distinctive_features: list[str]              # What makes this unique
    assumptions: list[AssumptionReport]          # Implicit assumptions

    # Scoring
    novelty_score: float                         # How novel compared to others (0-1)
    coherence_score: float                       # Internal coherence (0-1)
    coverage_score: float                        # Coverage of query/schema (0-1)
    composite_score: float                       # Weighted combination

    # Relationships
    differences_from_consensus: list[DifferenceReport]  # Diffs from consensus
    similar_candidates: list[str] = field(default_factory=list)  # Similar candidate IDs

    # Generation metadata
    generation_rank: int = 0                     # Order generated
    token_count: int = 0                         # Tokens in response
    temperature_used: float = 0.8                # Temperature for this sample
    prompt_variant: str = "base"                 # Which prompt variant used


@dataclass
class MiningResult:
    """Result of an outlier mining operation."""
    query: str                                   # Original query
    context: Optional[str]                       # Context document (if provided)
    schema_used: str                             # Schema name used

    # Candidates
    candidates: list[MiningCandidate]            # Top candidates (sorted by score)
    consensus_baseline: Optional[dict[str, Any]] # What consensus mode would return

    # Clustering
    num_clusters: int                            # Number of distinct approaches found
    clusters: list[ClusterInfo]                  # Cluster summaries
    silhouette_score: float                      # Clustering quality (0-1)

    # Diversity metrics
    diversity_score: float                       # Overall diversity (0-1)
    effective_diversity: float                   # Diversity × quality_pass_rate

    # Generation metadata
    convergence_point: Optional[int]             # Sample where saturation detected
    samples_generated: int                       # Total samples generated
    samples_passed_quality: int                  # Samples passing quality filter
    quality_pass_rate: float                     # Pass rate (0-1)
    saturation_signals: list[SaturationSignal]   # Saturation check history

    # Recommendations
    review_priority: list[str]                   # Candidate IDs in priority order
    high_novelty_candidates: list[str]           # Candidates with novelty > 0.7
    potential_hallucinations: list[str]          # Candidates flagged for high entropy

    # Cost tracking
    tokens_used: int                             # Total tokens
    cost_usd: float                              # Total cost
    characterisation_cost_usd: float = 0.0       # Cost of characterisation step
    config: MiningConfig = field(default_factory=MiningConfig)  # Config used
    latency_ms: int = 0                          # Total latency


@dataclass
class BatchMiningResult:
    """Result of batch mining operation."""
    results: list[MiningResult]
    total_cost_usd: float
    total_tokens: int
    total_latency_ms: int
    queries_succeeded: int
    queries_failed: int
