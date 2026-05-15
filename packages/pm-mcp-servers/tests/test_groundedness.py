"""Regression tests for the groundedness checker (Layer 6 foundation).

Anchored to the four scenarios the paper §9.3 demands:

1. GROUNDED — faithful citation produces a high score and an empty
   ungrounded-terms list.
2. UNGROUNDED — answer that goes beyond the sources is caught, with the
   specific fabricated tokens identified by name.
3. Per-source citation scores correctly attribute support between
   multiple documents.
4. Provenance trail composes query, retrieved sources, answer, and
   verdict into a single human-readable string.

Plus boundary cases (empty answer, missing source id, custom threshold)
and the public ``to_dict`` round-trip used by Phase 3 integration PRs.
"""

from __future__ import annotations

import pytest

from pm_mcp_servers._groundedness import (
    GroundednessResult,
    compute_groundedness,
)


# ─────────────────────────────────────────────────────────────────────────
# 1. GROUNDED scenarios
# ─────────────────────────────────────────────────────────────────────────


class TestGrounded:
    """Faithful answers, drawn from the sources, must verify as GROUNDED."""

    def test_answer_drawn_directly_from_source_is_grounded(self):
        sources = [{
            "id": "doc-001",
            "content": "Developers must maintain audit logs for a minimum of five years.",
        }]
        result = compute_groundedness(
            answer="Developers must maintain audit logs for a minimum of five years.",
            sources=sources,
        )
        assert result.grounded
        assert result.verdict == "GROUNDED"
        assert result.overall_score >= 0.99
        assert result.ungrounded_terms == []

    def test_paraphrased_within_source_vocabulary_is_grounded(self):
        """If the answer uses words present in the source, even rephrased,
        the token-overlap check still rates it as grounded. (The paper
        notes this is a known limitation of token overlap — see §9.4.)"""
        sources = [{
            "id": "doc-001",
            "content": (
                "All AI systems deployed in critical infrastructure must "
                "undergo independent safety assessments. Developers must "
                "maintain audit logs for a minimum of five years."
            ),
        }]
        result = compute_groundedness(
            answer="Audit logs must be maintained for five years minimum.",
            sources=sources,
        )
        assert result.grounded

    def test_empty_answer_is_trivially_grounded(self):
        """An empty answer has nothing to ground or to hallucinate. The
        consumer can act on the empty answer separately."""
        sources = [{"id": "doc-001", "content": "Something."}]
        result = compute_groundedness(answer="", sources=sources)
        assert result.grounded
        assert result.answer_token_count == 0
        assert result.ungrounded_terms == []


# ─────────────────────────────────────────────────────────────────────────
# 2. UNGROUNDED scenarios — hallucinations caught
# ─────────────────────────────────────────────────────────────────────────


class TestUngrounded:
    """The §9.3 Scenario 2: the model retrieved documents but generated
    claims that go beyond what they say. The score drops, and the
    specific fabricated terms are identified."""

    def test_hallucinated_claim_caught_with_specific_terms(self):
        """The answer mentions criminal sanctions and euros. The source
        says nothing about either. Verdict UNGROUNDED, and both terms
        appear in ungrounded_terms."""
        sources = [{
            "id": "doc-001",
            "content": "Developers must maintain audit logs for a minimum of five years.",
        }]
        result = compute_groundedness(
            answer=(
                "Non-compliance triggers criminal sanctions and fines up to "
                "ten million euros against senior executives."
            ),
            sources=sources,
        )
        assert not result.grounded
        assert result.verdict == "UNGROUNDED"
        assert "criminal" in result.ungrounded_terms
        assert "sanctions" in result.ungrounded_terms
        assert "euros" in result.ungrounded_terms

    def test_completely_unrelated_answer_scores_low(self):
        sources = [{"id": "doc-001", "content": "Audit logs and safety assessments."}]
        result = compute_groundedness(
            answer="The cargo vessel arrives in Singapore on Thursday.",
            sources=sources,
        )
        assert not result.grounded
        assert result.overall_score < 0.2

    def test_ungrounded_terms_deduped(self):
        """A hallucinated term appearing multiple times in the answer
        should appear once in the ungrounded_terms list."""
        sources = [{"id": "doc-001", "content": "Audit logs."}]
        result = compute_groundedness(
            answer="Penalties penalties penalties await offenders.",
            sources=sources,
        )
        assert result.ungrounded_terms.count("penalties") == 1


# ─────────────────────────────────────────────────────────────────────────
# 3. Per-source citation scores
# ─────────────────────────────────────────────────────────────────────────


class TestPerSourceCitations:
    """When several sources are available, the per-source citation
    scores identify which document supports which claims."""

    def test_per_source_scores_reflect_individual_overlap(self):
        sources = [
            {"id": "doc-A", "content": "Audit logs."},
            {"id": "doc-B", "content": "Safety assessments."},
        ]
        # Answer overlaps only with doc-A
        result = compute_groundedness(answer="Audit logs.", sources=sources)
        assert result.per_source_citation_scores["doc-A"] >= 0.99
        assert result.per_source_citation_scores["doc-B"] == 0.0

    def test_per_source_scores_can_overlap(self):
        """When a token appears in multiple sources, both per-source
        scores reflect the hit independently. (Per-source scores do not
        sum to overall_score; the overall is the union, per-source is
        the intersection.)"""
        sources = [
            {"id": "doc-A", "content": "The audit logs must persist."},
            {"id": "doc-B", "content": "The audit framework requires logs."},
        ]
        result = compute_groundedness(answer="audit logs", sources=sources)
        # "audit" and "logs" both appear in both sources, so per-source
        # citation scores should both be 1.0
        assert result.per_source_citation_scores["doc-A"] == 1.0
        assert result.per_source_citation_scores["doc-B"] == 1.0


# ─────────────────────────────────────────────────────────────────────────
# 4. Provenance trail
# ─────────────────────────────────────────────────────────────────────────


class TestProvenanceTrail:
    """The provenance trail is a single human-readable string composing
    query, sources, answer, and verdict. Used for board-level audit logs
    and the paper's §9.5 "system that shows its working" property."""

    def test_provenance_trail_contains_all_components(self):
        sources = [
            {"id": "doc-1", "title": "AI Safety Framework", "content": "Audit logs required."},
        ]
        result = compute_groundedness(
            answer="Audit logs are required.",
            sources=sources,
            query="What does the framework require?",
        )
        trail = result.provenance_trail
        assert "Provenance trail" in trail
        assert "What does the framework require?" in trail
        assert "doc-1" in trail
        assert "AI Safety Framework" in trail
        assert "Audit logs are required." in trail
        assert "GROUNDED" in trail

    def test_provenance_trail_handles_missing_query(self):
        sources = [{"id": "doc-1", "content": "X."}]
        result = compute_groundedness(answer="X.", sources=sources)
        assert "(not provided)" in result.provenance_trail


# ─────────────────────────────────────────────────────────────────────────
# 5. Threshold + boundary cases
# ─────────────────────────────────────────────────────────────────────────


class TestThresholdAndBoundary:
    """Threshold is configurable; boundary conditions are predictable."""

    def test_custom_threshold_lower_admits_more(self):
        sources = [{"id": "doc-1", "content": "audit logs"}]
        # Half the answer tokens are grounded
        answer = "audit logs and penalties"
        loose = compute_groundedness(answer=answer, sources=sources, threshold=0.4)
        strict = compute_groundedness(answer=answer, sources=sources, threshold=0.8)
        assert loose.grounded
        assert not strict.grounded
        assert loose.overall_score == strict.overall_score  # same score, different verdict

    def test_empty_sources_raises(self):
        with pytest.raises(ValueError, match="at least one source"):
            compute_groundedness(answer="hello", sources=[])

    def test_source_without_id_raises(self):
        with pytest.raises(ValueError, match="missing required 'id'"):
            compute_groundedness(
                answer="hello",
                sources=[{"content": "no id here"}],
            )

    def test_source_uses_text_field_if_content_missing(self):
        """Some retrievers use ``text`` rather than ``content``. The
        checker accepts either, preferring ``content`` if both are
        present."""
        result = compute_groundedness(
            answer="audit logs",
            sources=[{"id": "doc-1", "text": "audit logs are required"}],
        )
        assert result.grounded


# ─────────────────────────────────────────────────────────────────────────
# 6. to_dict round-trip (for MCP tool response field)
# ─────────────────────────────────────────────────────────────────────────


class TestToDict:
    """Phase 3 integration PRs will attach the result as a `_groundedness`
    field on MCP tool responses. The to_dict shape is the contract."""

    def test_to_dict_includes_all_expected_keys(self):
        result = compute_groundedness(
            answer="audit logs.",
            sources=[{"id": "doc-1", "content": "audit logs"}],
        )
        d = result.to_dict()
        for key in (
            "grounded", "verdict", "overall_score", "ungrounded_terms",
            "per_source_citation_scores", "answer_token_count",
            "provenance_trail", "threshold",
        ):
            assert key in d

    def test_to_dict_is_json_serialisable(self):
        import json
        result = compute_groundedness(
            answer="audit logs.",
            sources=[{"id": "doc-1", "content": "audit logs"}],
        )
        json.dumps(result.to_dict())  # raises if not serialisable
