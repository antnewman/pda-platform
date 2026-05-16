"""Confidence extraction module for reliable PM data extraction."""

from .aggregation import (
    compute_overall_confidence,
    compute_overall_confidence_with_gap,
)
from .extractor import (
    ConfidenceExtractor,
    confidence_extract,
    confidence_extract_batch,
)
from .models import (
    BatchConfidenceResult,
    ConfidenceResult,
    EstimateMode,
    OutlierReport,
    ReviewLevel,
)
from .schemas import (
    BarrierItem,
    CustomSchema,
    EstimateItem,
    MilestoneItem,
    OutcomeMeasureItem,
    RecommendationItem,
    RiskItem,
    SchemaType,
    StakeholderImpactItem,
)

__all__ = [
    # Main classes
    "ConfidenceExtractor",

    # Convenience functions
    "confidence_extract",
    "confidence_extract_batch",

    # Aggregation primitives (Verified Autonomy Layer 1)
    "compute_overall_confidence",
    "compute_overall_confidence_with_gap",

    # Result models
    "ConfidenceResult",
    "BatchConfidenceResult",
    "OutlierReport",
    "ReviewLevel",
    "EstimateMode",

    # Schema types
    "SchemaType",
    "CustomSchema",

    # PM data classes
    "RiskItem",
    "EstimateItem",
    "RecommendationItem",
    "MilestoneItem",
    "BarrierItem",
    "OutcomeMeasureItem",
    "StakeholderImpactItem",
]
