"""Quality-score + potential-hallucinations derivation from L6 signals.

Verified Autonomy Layer 3 (Making Failures Visible), §6.3 reference.
Composes A6's :func:`agent_planning.quality.compute_quality_score`
formula over signals the platform's L6 groundedness check already
produces, so every AI-authored tool response can surface a
``_quality`` field alongside its existing ``_groundedness`` payload.

The platform's tools are single-shot AI calls — no multi-sample
runs at request time — so true semantic entropy is unavailable.
Instead this module models effective entropy from the L6 result:
the count and proportion of ungrounded terms acts as a proxy for
how much the output "diverges" from the source data. The
:func:`derive_quality_from_groundedness` function returns a dict
with:

* ``overall_score`` — quality score in ``[0, 1]``.
* ``components`` — coherence, relevance, completeness, semantic_entropy.
* ``flagged_as_low_quality`` — bool from A6's compute_quality_score.
* ``potential_hallucinations`` — bool. True when (a) the L6 verdict
  is UNGROUNDED, OR (b) more than ``hallucination_term_ratio`` of
  answer tokens are ungrounded.

The mapping from L6 to the four A6 components is documented inline.
A future revision can swap in genuine multi-sample entropy when the
platform supports multi-sample inference (e.g. via
``confidence_extract_batch``).
"""

from __future__ import annotations

from typing import Any

__all__ = ["derive_quality_from_groundedness"]


_DEFAULT_THRESHOLD: float = 0.6
_DEFAULT_HALLUCINATION_TERM_RATIO: float = 0.3


def derive_quality_from_groundedness(
    groundedness: dict[str, Any] | None,
    *,
    threshold: float = _DEFAULT_THRESHOLD,
    hallucination_term_ratio: float = _DEFAULT_HALLUCINATION_TERM_RATIO,
) -> dict[str, Any]:
    """Compose A6's quality score from an L6 groundedness result.

    Args:
        groundedness: The dict produced by
            :func:`pm_mcp_servers._groundedness.compute_groundedness`'s
            ``to_dict()``. When ``None`` or empty, the returned dict
            has ``verdict = "NOT_COMPUTED"`` so consumers can
            distinguish "not measured" from "low quality".
        threshold: Quality threshold below which
            ``flagged_as_low_quality`` is ``True``. Default 0.6
            (matches A6's default).
        hallucination_term_ratio: Fraction of answer tokens that must
            be ungrounded to trigger ``potential_hallucinations``
            independently of the L6 verdict. Default 0.3.

    Returns:
        ``{"verdict": "COMPUTED"|"NOT_COMPUTED", "overall_score": ...,
        "components": {...}, "flagged_as_low_quality": ...,
        "potential_hallucinations": ...}``.
    """
    if not groundedness:
        return {
            "verdict": "NOT_COMPUTED",
            "reason": "No groundedness result supplied.",
        }
    gnd_verdict = str(groundedness.get("verdict", "")).upper()
    if gnd_verdict not in ("GROUNDED", "UNGROUNDED"):
        return {
            "verdict": "NOT_COMPUTED",
            "reason": f"Groundedness verdict is {gnd_verdict or 'absent'}; cannot derive quality.",
        }

    overall = float(groundedness.get("overall_score", 0.0))
    answer_tokens = int(groundedness.get("answer_token_count", 0) or 0)
    ungrounded_terms = list(groundedness.get("ungrounded_terms", []) or [])

    # Map L6 → A6 components (transparent, documented mapping).
    # Coherence and completeness are 1.0 for a single-shot deterministic
    # call (no template gaps, no multi-sample contradictions). A future
    # revision can dial these down based on L5 FLAGGED rules etc.
    coherence = 1.0
    completeness = 1.0
    # Relevance is the groundedness score directly — measuring how well
    # the answer cites the supplied sources.
    relevance = overall
    # Effective entropy proxy: the larger the ungrounded fraction, the
    # higher the semantic spread between the answer and the sources.
    if answer_tokens > 0:
        ungrounded_fraction = min(1.0, len(ungrounded_terms) / answer_tokens)
    else:
        ungrounded_fraction = 0.0
    # Scale the fraction into the [0, 1] entropy range A6 expects.
    semantic_entropy = ungrounded_fraction

    # Deferred — A6 lives in agent-task-planning.
    from agent_planning.quality import compute_quality_score

    score = compute_quality_score(
        coherence=coherence,
        relevance=relevance,
        completeness=completeness,
        semantic_entropy=semantic_entropy,
        threshold=threshold,
    )

    potential_hallucinations = (
        gnd_verdict == "UNGROUNDED"
        or ungrounded_fraction > hallucination_term_ratio
    )

    return {
        "verdict": "COMPUTED",
        "overall_score": score.overall,
        "components": {
            "coherence": coherence,
            "relevance": relevance,
            "completeness": completeness,
            "semantic_entropy": semantic_entropy,
        },
        "entropy_penalty": score.entropy_penalty,
        "flagged_as_low_quality": not score.passed_threshold,
        "threshold": threshold,
        "potential_hallucinations": potential_hallucinations,
        "ungrounded_fraction": ungrounded_fraction,
    }
