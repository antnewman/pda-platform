"""Data models for confidence extraction."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ReviewLevel(Enum):
    """Recommended level of human review based on confidence."""
    NONE = "none"                    # High confidence, no review needed
    SPOT_CHECK = "spot_check"        # Moderate confidence, quick glance
    DETAILED_REVIEW = "detailed"     # Low confidence, careful review
    EXPERT_REQUIRED = "expert"       # Very low confidence or outliers detected


class EstimateMode(Enum):
    """How to structure estimate outputs."""
    POINT_WITH_RANGE = "point_with_range"      # 15 days (12-20)
    THREE_POINT = "three_point"                 # O: 10, M: 15, P: 25
    RANGE_ONLY = "range_only"                   # 12-20 days


@dataclass
class OutlierReport:
    """Details about a detected outlier in extraction results."""
    field: str                          # Which field diverged
    consensus_value: Any                # What most samples produced
    outlier_value: Any                  # What this sample produced
    sample_index: int                   # Which sample (0-indexed)
    divergence_score: float             # How far from consensus (0-1 normalised)
    reason: str                         # Human-readable explanation


@dataclass
class ConfidenceResult:
    """Result of a confidence extraction query."""
    query: str                                      # Original query
    consensus: dict[str, Any]                       # Aggregated structured output
    confidence: float                               # Overall confidence 0.0-1.0
    field_confidence: dict[str, float]              # Per-field confidence scores
    outliers: list[OutlierReport]                   # Detected outliers
    raw_responses: list[dict[str, Any]]             # All individual extractions
    samples_used: int                               # Samples before early stop
    samples_requested: int                          # Original sample count
    early_stopped: bool                             # Did early stopping trigger
    cost_usd: float                                 # Total cost
    cost_saved_usd: float                           # Saved via early stopping
    tokens_used: int                                # Total tokens
    latency_ms: int                                 # Total time
    review_level: ReviewLevel                       # Recommended review level
    review_reason: Optional[str] = None             # Why review recommended

    @property
    def review_recommended(self) -> bool:
        """Whether any human review is recommended."""
        return self.review_level != ReviewLevel.NONE


@dataclass
class BatchConfidenceResult:
    """Result of a batch confidence extraction."""
    results: list[ConfidenceResult]
    total_cost_usd: float
    total_tokens: int
    total_latency_ms: int
    queries_succeeded: int
    queries_failed: int
