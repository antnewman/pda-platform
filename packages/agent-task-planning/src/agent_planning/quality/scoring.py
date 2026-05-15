"""Quality-score and hallucination-flag primitives.

Faithful implementation of the §6.3 formulas:

    entropy_penalty = max(0, semantic_entropy - 0.5) * 0.5
    overall = coherence * 0.4 + relevance * 0.4 + completeness * 0.2
              - entropy_penalty

The weights (0.4, 0.4, 0.2) are deliberately exposed as module
constants so production deployments can override them per domain — a
factual extraction system may weight relevance higher; a creative
writing system may weight completeness higher.

The entropy penalty activates only above 0.5 (a modest amount of
variation is tolerated, per §6.3) and scales linearly. At maximum
entropy of 1.0, the penalty is 0.25 — enough to push a borderline
output below the default quality threshold of 0.6.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "COMPLETENESS_WEIGHT",
    "COHERENCE_WEIGHT",
    "DEFAULT_HALLUCINATION_THRESHOLD",
    "DEFAULT_QUALITY_THRESHOLD",
    "ENTROPY_PENALTY_SCALE",
    "ENTROPY_TOLERATED",
    "QualityScore",
    "RELEVANCE_WEIGHT",
    "Sample",
    "compute_pass_rate",
    "compute_quality_score",
    "flag_potential_hallucinations",
]


# ─────────────────────────────────────────────────────────────────────────
# Module-level constants (overridable for domain-specific deployments)
# ─────────────────────────────────────────────────────────────────────────

COHERENCE_WEIGHT: float = 0.4
RELEVANCE_WEIGHT: float = 0.4
COMPLETENESS_WEIGHT: float = 0.2

ENTROPY_TOLERATED: float = 0.5  # No penalty below this entropy
ENTROPY_PENALTY_SCALE: float = 0.5  # Multiplier on entropy above tolerated

DEFAULT_QUALITY_THRESHOLD: float = 0.6
DEFAULT_HALLUCINATION_THRESHOLD: float = 0.7


# ─────────────────────────────────────────────────────────────────────────
# Quality score
# ─────────────────────────────────────────────────────────────────────────


@dataclass
class QualityScore:
    """Composite quality score for a single AI sample.

    Attributes:
        coherence: Internal consistency in ``[0.0, 1.0]``.
        relevance: How on-topic the output is in ``[0.0, 1.0]``.
        completeness: How fully the output addresses the request in
            ``[0.0, 1.0]``.
        semantic_entropy: Variance across repeated model runs for the
            same prompt in ``[0.0, 1.0]``. Above ``ENTROPY_TOLERATED``
            (0.5), a linear penalty is applied to the overall score.
        entropy_penalty: The computed penalty (always non-negative).
        overall: The composite score after penalty.
        passed_threshold: True iff ``overall >= threshold``.
        threshold: The threshold used.
    """

    coherence: float
    relevance: float
    completeness: float
    semantic_entropy: float
    entropy_penalty: float
    overall: float
    passed_threshold: bool
    threshold: float = DEFAULT_QUALITY_THRESHOLD

    def to_dict(self) -> dict[str, Any]:
        """JSON-serialisable representation for MCP tool responses and
        audit chain entries."""
        return {
            "coherence": self.coherence,
            "relevance": self.relevance,
            "completeness": self.completeness,
            "semantic_entropy": self.semantic_entropy,
            "entropy_penalty": self.entropy_penalty,
            "overall": self.overall,
            "passed_threshold": self.passed_threshold,
            "threshold": self.threshold,
        }


def compute_quality_score(
    coherence: float,
    relevance: float,
    completeness: float,
    semantic_entropy: float,
    threshold: float = DEFAULT_QUALITY_THRESHOLD,
) -> QualityScore:
    """Compute the composite quality score for one sample.

    Args:
        coherence: ``[0.0, 1.0]`` — internal consistency.
        relevance: ``[0.0, 1.0]`` — how on-topic the output is.
        completeness: ``[0.0, 1.0]`` — how fully the output addresses the request.
        semantic_entropy: ``[0.0, 1.0]`` — variance across repeated runs.
        threshold: Score above which the sample passes (default 0.6).

    Returns:
        :class:`QualityScore` with the computed components.

    Raises:
        ValueError: If any input is outside ``[0.0, 1.0]``.
    """
    for name, value in (
        ("coherence", coherence),
        ("relevance", relevance),
        ("completeness", completeness),
        ("semantic_entropy", semantic_entropy),
    ):
        if not 0.0 <= value <= 1.0:
            raise ValueError(
                f"{name} must be in [0.0, 1.0]; got {value!r}"
            )

    # Composite — the formula from §6.3
    weighted = (
        coherence * COHERENCE_WEIGHT
        + relevance * RELEVANCE_WEIGHT
        + completeness * COMPLETENESS_WEIGHT
    )
    entropy_penalty = max(0.0, semantic_entropy - ENTROPY_TOLERATED) * ENTROPY_PENALTY_SCALE
    overall = weighted - entropy_penalty

    # The overall is bounded by [-0.25, 1.0] from the formula (penalty can
    # take a 0.0-quality score to -0.25). Clamp to [0.0, 1.0] for sanity.
    overall = max(0.0, min(1.0, overall))

    return QualityScore(
        coherence=coherence,
        relevance=relevance,
        completeness=completeness,
        semantic_entropy=semantic_entropy,
        entropy_penalty=entropy_penalty,
        overall=overall,
        passed_threshold=overall >= threshold,
        threshold=threshold,
    )


# ─────────────────────────────────────────────────────────────────────────
# Hallucination flagging
# ─────────────────────────────────────────────────────────────────────────


@dataclass
class Sample:
    """One AI-generated sample with its quality score.

    Attributes:
        id: Unique identifier for the sample (a string the reviewer can
            use to look the sample up).
        quality: The composite quality score from
            :func:`compute_quality_score`.
        metadata: Optional free-form context (e.g. model version,
            prompt id, retrieval set).
    """

    id: str
    quality: QualityScore
    metadata: dict[str, Any] = field(default_factory=dict)


def flag_potential_hallucinations(
    samples: list[Sample],
    threshold: float = DEFAULT_HALLUCINATION_THRESHOLD,
) -> list[str]:
    """Return the IDs of samples whose semantic entropy exceeds the
    threshold (default 0.7 from §6.3).

    The comparison is strict greater-than: entropy exactly at the
    threshold is NOT flagged. This is the boundary semantic the paper
    specifies — see its discussion of the strict-greater-than choice in
    §6.3.

    Args:
        samples: The samples to evaluate.
        threshold: Entropy strictly above which a sample is flagged.

    Returns:
        Sorted list of flagged sample IDs (sort is by insertion order,
        not alphabetical).
    """
    return [
        s.id for s in samples
        if s.quality.semantic_entropy > threshold
    ]


def compute_pass_rate(samples: list[Sample]) -> float:
    """Return the fraction of samples that cleared the quality bar.

    A system-level health metric per §6.3. If this number is dropping
    over time, the model's reliability is degrading — the system needs
    attention before anyone notices from the outputs alone.

    Returns ``0.0`` for an empty input (no samples, no pass rate; do not
    confuse with "all failed").
    """
    if not samples:
        return 0.0
    passed = sum(1 for s in samples if s.quality.passed_threshold)
    return passed / len(samples)
