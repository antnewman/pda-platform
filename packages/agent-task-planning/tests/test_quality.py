"""Regression tests for the quality-score primitive (Layer 3 foundation).

Anchored to the four boundary conditions the paper §6.3 makes explicit
in its test suite:

1. Entropy below 0.5 incurs no penalty.
2. Maximum entropy penalty is exactly 0.25.
3. High entropy pushes a borderline-quality output below the threshold.
4. The strict greater-than comparison at the hallucination threshold:
   entropy exactly at 0.7 is NOT flagged; 0.701 is.
"""

from __future__ import annotations

import pytest

from agent_planning.quality import (
    DEFAULT_HALLUCINATION_THRESHOLD,
    DEFAULT_QUALITY_THRESHOLD,
    QualityScore,
    Sample,
    compute_pass_rate,
    compute_quality_score,
    flag_potential_hallucinations,
)


# ─────────────────────────────────────────────────────────────────────────
# 1. The four boundary conditions from paper §6.3
# ─────────────────────────────────────────────────────────────────────────


class TestPaperBoundaryConditions:
    """The flagship tests from §6.3 — the four behaviours the paper
    explicitly verifies."""

    def test_entropy_below_half_incurs_no_penalty(self):
        """entropy = 0.3 and entropy = 0.5 produce identical overall scores."""
        a = compute_quality_score(0.8, 0.8, 0.8, semantic_entropy=0.3)
        b = compute_quality_score(0.8, 0.8, 0.8, semantic_entropy=0.5)
        assert a.overall == b.overall
        assert a.entropy_penalty == 0.0
        assert b.entropy_penalty == 0.0

    def test_max_entropy_penalty_is_quarter(self):
        """At entropy 1.0, the penalty is exactly 0.25."""
        zero = compute_quality_score(0.8, 0.8, 0.8, semantic_entropy=0.0)
        full = compute_quality_score(0.8, 0.8, 0.8, semantic_entropy=1.0)
        difference = zero.overall - full.overall
        assert abs(difference - 0.25) < 1e-9

    def test_high_entropy_pushes_borderline_below_threshold(self):
        """A sample with otherwise acceptable quality (overall 0.7 without
        penalty) can be pushed below 0.6 by high entropy alone."""
        # Coherence/Relevance/Completeness all 0.7 → weighted = 0.7
        # With entropy 1.0, penalty = 0.25 → overall = 0.45
        borderline = compute_quality_score(0.7, 0.7, 0.7, semantic_entropy=1.0)
        assert borderline.overall < DEFAULT_QUALITY_THRESHOLD
        assert not borderline.passed_threshold

    def test_strict_greater_than_at_hallucination_threshold(self):
        """entropy exactly at 0.7 is NOT flagged; 0.701 is."""
        at_threshold = Sample(
            id="at",
            quality=compute_quality_score(0.8, 0.8, 0.8, semantic_entropy=0.7),
        )
        just_above = Sample(
            id="above",
            quality=compute_quality_score(0.8, 0.8, 0.8, semantic_entropy=0.701),
        )
        flagged = flag_potential_hallucinations([at_threshold, just_above])
        assert "at" not in flagged
        assert "above" in flagged


# ─────────────────────────────────────────────────────────────────────────
# 2. Quality score arithmetic
# ─────────────────────────────────────────────────────────────────────────


class TestQualityScoreFormula:
    """The composite formula matches §6.3 weights exactly."""

    def test_perfect_inputs_produce_perfect_overall(self):
        result = compute_quality_score(1.0, 1.0, 1.0, semantic_entropy=0.0)
        assert result.overall == 1.0
        assert result.passed_threshold

    def test_zero_inputs_produce_zero_overall(self):
        result = compute_quality_score(0.0, 0.0, 0.0, semantic_entropy=0.0)
        assert result.overall == 0.0
        assert not result.passed_threshold

    def test_weighted_sum_is_correct(self):
        """coherence * 0.4 + relevance * 0.4 + completeness * 0.2 — no entropy."""
        result = compute_quality_score(0.5, 0.75, 1.0, semantic_entropy=0.0)
        expected = 0.5 * 0.4 + 0.75 * 0.4 + 1.0 * 0.2
        assert abs(result.overall - expected) < 1e-9

    def test_overall_clamped_to_zero(self):
        """A combination of zero quality and max entropy could go negative.
        The result is clamped to [0.0, 1.0]."""
        result = compute_quality_score(0.0, 0.0, 0.0, semantic_entropy=1.0)
        assert result.overall == 0.0


# ─────────────────────────────────────────────────────────────────────────
# 3. Input validation
# ─────────────────────────────────────────────────────────────────────────


class TestInputValidation:
    """Out-of-range inputs raise ValueError with the offending field named."""

    def test_coherence_above_one_rejected(self):
        with pytest.raises(ValueError, match="coherence"):
            compute_quality_score(1.5, 0.5, 0.5, semantic_entropy=0.0)

    def test_relevance_below_zero_rejected(self):
        with pytest.raises(ValueError, match="relevance"):
            compute_quality_score(0.5, -0.1, 0.5, semantic_entropy=0.0)

    def test_completeness_above_one_rejected(self):
        with pytest.raises(ValueError, match="completeness"):
            compute_quality_score(0.5, 0.5, 1.1, semantic_entropy=0.0)

    def test_entropy_above_one_rejected(self):
        with pytest.raises(ValueError, match="semantic_entropy"):
            compute_quality_score(0.5, 0.5, 0.5, semantic_entropy=1.1)


# ─────────────────────────────────────────────────────────────────────────
# 4. Hallucinations list + pass rate
# ─────────────────────────────────────────────────────────────────────────


class TestHallucinationsListAndPassRate:
    """The three-output-category architecture: trusted, flagged, rejected.
    Flagging is by entropy; passing is by overall score. They can disagree."""

    def test_flag_returns_only_high_entropy_samples(self):
        samples = [
            Sample(id="a", quality=compute_quality_score(0.9, 0.9, 0.9, 0.2)),
            Sample(id="b", quality=compute_quality_score(0.7, 0.7, 0.7, 0.8)),
            Sample(id="c", quality=compute_quality_score(0.8, 0.8, 0.8, 0.3)),
            Sample(id="d", quality=compute_quality_score(0.6, 0.6, 0.6, 0.9)),
        ]
        flagged = flag_potential_hallucinations(samples)
        assert flagged == ["b", "d"]

    def test_flag_preserves_insertion_order(self):
        """The flagged list preserves the input order, not alphabetical."""
        samples = [
            Sample(id="z", quality=compute_quality_score(0.5, 0.5, 0.5, 0.9)),
            Sample(id="m", quality=compute_quality_score(0.5, 0.5, 0.5, 0.9)),
            Sample(id="a", quality=compute_quality_score(0.5, 0.5, 0.5, 0.9)),
        ]
        flagged = flag_potential_hallucinations(samples)
        assert flagged == ["z", "m", "a"]

    def test_pass_rate_correct(self):
        samples = [
            Sample(id="a", quality=compute_quality_score(0.9, 0.9, 0.9, 0.2)),  # passes
            Sample(id="b", quality=compute_quality_score(0.3, 0.3, 0.3, 0.2)),  # fails
            Sample(id="c", quality=compute_quality_score(0.9, 0.9, 0.9, 0.2)),  # passes
            Sample(id="d", quality=compute_quality_score(0.3, 0.3, 0.3, 0.2)),  # fails
        ]
        assert compute_pass_rate(samples) == 0.5

    def test_pass_rate_empty_input_returns_zero(self):
        assert compute_pass_rate([]) == 0.0

    def test_high_entropy_clean_overall_is_flagged_but_passes_threshold(self):
        """A subtle property: a sample with high quality components but high
        entropy may pass the quality threshold (overall ≥ 0.6) yet still
        be flagged for hallucination (entropy > 0.7). The two judgements
        are independent — the paper's whole point about three categories."""
        sample = Sample(
            id="s",
            quality=compute_quality_score(1.0, 1.0, 1.0, semantic_entropy=0.8),
        )
        # overall = 1.0 - (0.8-0.5)*0.5 = 0.85 → passes
        assert sample.quality.passed_threshold
        # entropy 0.8 > 0.7 → flagged
        assert flag_potential_hallucinations([sample]) == ["s"]


# ─────────────────────────────────────────────────────────────────────────
# 5. to_dict round-trip
# ─────────────────────────────────────────────────────────────────────────


class TestToDict:
    """The QualityScore.to_dict shape is the contract Phase 3 PR B28
    will attach to AI-authored MCP tool responses under the `_quality`
    field."""

    def test_to_dict_includes_all_fields(self):
        score = compute_quality_score(0.5, 0.6, 0.7, semantic_entropy=0.4)
        d = score.to_dict()
        for key in (
            "coherence", "relevance", "completeness", "semantic_entropy",
            "entropy_penalty", "overall", "passed_threshold", "threshold",
        ):
            assert key in d

    def test_to_dict_is_json_serialisable(self):
        import json
        score = compute_quality_score(0.5, 0.6, 0.7, semantic_entropy=0.4)
        json.dumps(score.to_dict())
