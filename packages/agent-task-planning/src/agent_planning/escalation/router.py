"""Four-tier escalation router.

Composes the existing IQR-based outlier detection (in
:mod:`agent_planning.confidence.aggregation`) with an explicit four-tier
routing decision that fails safe via the OR condition the paper
specifies in §5.3.

The router is intentionally separable from detection. Detection answers
"are these samples consistent?". Routing answers "what does the system
do about it?". Production deployments may want to swap the detection
algorithm (e.g. for heavy-tailed distributions) without touching the
routing logic; or to parameterise the thresholds without touching the
detector.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from statistics import median
from typing import Any

from agent_planning.confidence.aggregation import detect_numeric_outliers
from agent_planning.confidence.models import OutlierReport

__all__ = [
    "EscalationLevel",
    "RoutingDecision",
    "route",
]


# ─────────────────────────────────────────────────────────────────────────
# Defaults from paper §5.3
# ─────────────────────────────────────────────────────────────────────────

DEFAULT_EXPERT_THRESHOLD: float = 0.4   # below this → EXPERT_REQUIRED on confidence alone
DEFAULT_DETAILED_THRESHOLD: float = 0.6  # below this (and at-or-above expert) → DETAILED_REVIEW
DEFAULT_SPOT_THRESHOLD: float = 0.8     # below this (and at-or-above detailed) → SPOT_CHECK


# ─────────────────────────────────────────────────────────────────────────
# Escalation level
# ─────────────────────────────────────────────────────────────────────────


class EscalationLevel(str, Enum):
    """Where an output should be routed for human review.

    String enum so the level is JSON-serialisable for inclusion in
    MCP tool responses and audit chain entries.
    """

    EXPERT_REQUIRED = "EXPERT_REQUIRED"
    DETAILED_REVIEW = "DETAILED_REVIEW"
    SPOT_CHECK = "SPOT_CHECK"
    NONE = "NONE"

    @property
    def description(self) -> str:
        return {
            EscalationLevel.EXPERT_REQUIRED: (
                "Route to a domain expert. Output is not acted upon until reviewed."
            ),
            EscalationLevel.DETAILED_REVIEW: (
                "A human reads every output in this tier before action."
            ),
            EscalationLevel.SPOT_CHECK: (
                "Periodic sampling — a proportion of outputs are reviewed."
            ),
            EscalationLevel.NONE: (
                "No human review required. Auto-process."
            ),
        }[self]


# ─────────────────────────────────────────────────────────────────────────
# Routing decision dataclass
# ─────────────────────────────────────────────────────────────────────────


@dataclass
class RoutingDecision:
    """Outcome of :func:`route`.

    The whole point of separating detection from routing is so a consumer
    can act on this single object without re-running anything: the level
    is the action, the reason explains why, the consensus is the median
    output the system thinks should be acted on (if any), and the
    outliers list is the per-sample detail for the audit trail.

    Attributes:
        level: Which tier this output falls in.
        reason: Plain-English explanation of why this tier was chosen.
            Includes both the confidence-based and outlier-based triggers
            so a reviewer can see the full picture.
        consensus: The median sample value — the agreed reference point
            for what the system thinks the answer is.
        confidence: The overall confidence score passed in.
        outliers: List of :class:`OutlierReport` from the detector. Each
            carries its own ``reason`` string for the reviewer.
        triggered_by_outliers: True iff an outlier triggered escalation.
        triggered_by_confidence: True iff low confidence triggered.
            Both can be true simultaneously.
        thresholds_used: The threshold tuple in effect (expert, detailed,
            spot).
    """

    level: EscalationLevel
    reason: str
    consensus: float
    confidence: float
    outliers: list[OutlierReport] = field(default_factory=list)
    triggered_by_outliers: bool = False
    triggered_by_confidence: bool = False
    thresholds_used: tuple[float, float, float] = (
        DEFAULT_EXPERT_THRESHOLD,
        DEFAULT_DETAILED_THRESHOLD,
        DEFAULT_SPOT_THRESHOLD,
    )

    def to_dict(self) -> dict[str, Any]:
        """JSON-serialisable representation for MCP tool responses
        and audit chain entries."""
        return {
            "level": self.level.value,
            "reason": self.reason,
            "consensus": self.consensus,
            "confidence": self.confidence,
            "outliers": [
                {
                    "field": o.field,
                    "consensus_value": o.consensus_value,
                    "outlier_value": o.outlier_value,
                    "sample_index": o.sample_index,
                    "divergence_score": o.divergence_score,
                    "reason": o.reason,
                }
                for o in self.outliers
            ],
            "triggered_by_outliers": self.triggered_by_outliers,
            "triggered_by_confidence": self.triggered_by_confidence,
            "thresholds_used": list(self.thresholds_used),
        }


# ─────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────


def route(
    values: list[float],
    confidence: float,
    labels: list[str] | None = None,
    field_name: str = "value",
    iqr_multiplier: float = 1.5,
    expert_threshold: float = DEFAULT_EXPERT_THRESHOLD,
    detailed_threshold: float = DEFAULT_DETAILED_THRESHOLD,
    spot_threshold: float = DEFAULT_SPOT_THRESHOLD,
) -> RoutingDecision:
    """Run outlier detection and return a four-tier routing decision.

    The fail-safe property is the OR condition: outliers OR low
    confidence each independently trigger escalation. A high-confidence
    output with a single outlier still escalates. A low-confidence
    output with no outliers still escalates. The only path to
    auto-processing is confidence ≥ spot_threshold AND no outliers.

    Args:
        values: List of numeric values from repeated model samples.
        confidence: Overall confidence score for this output in
            ``[0.0, 1.0]``. Typically from the inverse-weighted
            aggregator in :mod:`agent_planning.confidence.aggregation`.
        labels: Optional per-sample labels (e.g. agent names). When
            present, the outlier reasons include the label. Defaults
            to numeric indices.
        field_name: Field name for outlier reason strings.
        iqr_multiplier: Multiplier on IQR for fence width (default 1.5
            from Tukey; can be widened for heavy-tailed distributions).
        expert_threshold: Confidence below this triggers EXPERT_REQUIRED
            on confidence alone. Default 0.4 from paper.
        detailed_threshold: Confidence below this (and at-or-above
            expert) triggers DETAILED_REVIEW. Default 0.6.
        spot_threshold: Confidence below this (and at-or-above
            detailed) triggers SPOT_CHECK. Default 0.8.

    Returns:
        :class:`RoutingDecision` with level, reason, consensus, outlier
        detail, and the trigger flags.

    Raises:
        ValueError: If ``values`` is empty, ``confidence`` is outside
            ``[0.0, 1.0]``, or the thresholds are not strictly
            increasing.
    """
    # Input validation
    if not values:
        raise ValueError("route requires at least one value")
    if not 0.0 <= confidence <= 1.0:
        raise ValueError(
            f"confidence must be in [0.0, 1.0]; got {confidence!r}"
        )
    if not (expert_threshold < detailed_threshold < spot_threshold):
        raise ValueError(
            f"thresholds must be strictly increasing; got "
            f"expert={expert_threshold}, detailed={detailed_threshold}, "
            f"spot={spot_threshold}"
        )

    # Run detection
    sample_indices = list(range(len(values)))
    consensus, outliers = detect_numeric_outliers(
        values=values,
        sample_indices=sample_indices,
        field_name=field_name,
        iqr_multiplier=iqr_multiplier,
    )

    # If labels supplied, replace numeric indices in reason strings
    if labels and len(labels) == len(values):
        labelled_outliers: list[OutlierReport] = []
        for o in outliers:
            label = labels[o.sample_index]
            new_reason = (
                f"{label}: {o.reason}"
                if not o.reason.startswith(label)
                else o.reason
            )
            labelled_outliers.append(OutlierReport(
                field=o.field,
                consensus_value=o.consensus_value,
                outlier_value=o.outlier_value,
                sample_index=o.sample_index,
                divergence_score=o.divergence_score,
                reason=new_reason,
            ))
        outliers = labelled_outliers

    # Apply the OR fail-safe
    triggered_by_outliers = len(outliers) > 0
    triggered_by_confidence = confidence < expert_threshold

    if triggered_by_outliers or triggered_by_confidence:
        level = EscalationLevel.EXPERT_REQUIRED
    elif confidence < detailed_threshold:
        level = EscalationLevel.DETAILED_REVIEW
    elif confidence < spot_threshold:
        level = EscalationLevel.SPOT_CHECK
    else:
        level = EscalationLevel.NONE

    reason = _compose_reason(
        level=level,
        confidence=confidence,
        outlier_count=len(outliers),
        triggered_by_outliers=triggered_by_outliers,
        triggered_by_confidence=triggered_by_confidence,
        thresholds=(expert_threshold, detailed_threshold, spot_threshold),
    )

    return RoutingDecision(
        level=level,
        reason=reason,
        consensus=consensus,
        confidence=confidence,
        outliers=outliers,
        triggered_by_outliers=triggered_by_outliers,
        triggered_by_confidence=triggered_by_confidence,
        thresholds_used=(expert_threshold, detailed_threshold, spot_threshold),
    )


# ─────────────────────────────────────────────────────────────────────────
# Internal: reason composition
# ─────────────────────────────────────────────────────────────────────────


def _compose_reason(
    *,
    level: EscalationLevel,
    confidence: float,
    outlier_count: int,
    triggered_by_outliers: bool,
    triggered_by_confidence: bool,
    thresholds: tuple[float, float, float],
) -> str:
    """Build the plain-English reason for the decision.

    The reason names both possible triggers so a reviewer sees the full
    picture, even when only one fired.
    """
    expert, detailed, spot = thresholds

    if level == EscalationLevel.EXPERT_REQUIRED:
        if triggered_by_outliers and triggered_by_confidence:
            return (
                f"EXPERT_REQUIRED: {outlier_count} statistical outlier(s) detected "
                f"AND confidence {confidence:.2f} is below the expert threshold "
                f"({expert}). Both triggers fired; route to a domain expert."
            )
        if triggered_by_outliers:
            return (
                f"EXPERT_REQUIRED: {outlier_count} statistical outlier(s) detected. "
                f"Confidence {confidence:.2f} alone would not have escalated, but "
                f"the OR fail-safe routes any outlier to a domain expert."
            )
        return (
            f"EXPERT_REQUIRED: confidence {confidence:.2f} is below the expert "
            f"threshold ({expert}). No outliers detected, but confidence alone "
            f"is sufficient to require expert review."
        )

    if level == EscalationLevel.DETAILED_REVIEW:
        return (
            f"DETAILED_REVIEW: confidence {confidence:.2f} is between the expert "
            f"({expert}) and detailed ({detailed}) thresholds. No outliers "
            f"detected. A human reads every output at this tier."
        )

    if level == EscalationLevel.SPOT_CHECK:
        return (
            f"SPOT_CHECK: confidence {confidence:.2f} is between the detailed "
            f"({detailed}) and spot ({spot}) thresholds. No outliers detected. "
            f"Periodic sampling for review."
        )

    return (
        f"NONE: confidence {confidence:.2f} is at or above the spot threshold "
        f"({spot}). No outliers detected. Auto-process without human review."
    )
