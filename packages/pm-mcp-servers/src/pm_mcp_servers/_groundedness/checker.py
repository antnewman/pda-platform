"""Token-overlap groundedness checker.

Implements the §9.3 reference: tokenise the answer and the source
documents, remove stop words, measure what fraction of substantive
answer tokens appear in at least one source. The overall fraction is
the *groundedness score*. The score's complement — the tokens that
appear in no source — is the *ungrounded terms list*.

Per-source *citation scores* report how well each individual source
supports the answer, identifying which document supports which claims.

The implementation is intentionally simple and transparent. Production
deployments would swap in an NLI-based checker for semantic entailment
(per paper §9.4 limitation note); the architecture (retrieve, check,
cite, produce provenance trail) is identical at any level of
sophistication.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

__all__ = [
    "GroundednessResult",
    "Verdict",
    "compute_groundedness",
]

Verdict = Literal["GROUNDED", "UNGROUNDED"]

# Default threshold from paper §6.3 / §9.3
DEFAULT_THRESHOLD: float = 0.7

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9'-]*")


# ─────────────────────────────────────────────────────────────────────────
# Stop-word loading
# ─────────────────────────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def _load_stopwords() -> frozenset[str]:
    """Read the stop-word list from ``_data/stopwords_en.txt``.

    Cached at module load. Lines starting with ``#`` and blank lines are
    skipped.
    """
    path = Path(__file__).resolve().parent.parent / "_data" / "stopwords_en.txt"
    words: set[str] = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip().lower()
            if not stripped or stripped.startswith("#"):
                continue
            words.add(stripped)
    return frozenset(words)


def _tokenise(text: str) -> list[str]:
    """Lowercase + extract alphanumeric tokens (apostrophes and hyphens
    preserved inside tokens). Stop-words filtered out."""
    stop = _load_stopwords()
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in stop]


# ─────────────────────────────────────────────────────────────────────────
# Result type
# ─────────────────────────────────────────────────────────────────────────


@dataclass
class GroundednessResult:
    """Outcome of :func:`compute_groundedness`.

    Attributes:
        grounded: True if ``overall_score >= threshold``.
        verdict: ``"GROUNDED"`` or ``"UNGROUNDED"`` for downstream
            consumers that prefer strings to booleans.
        overall_score: Fraction of substantive answer tokens that appear
            in at least one source. In ``[0.0, 1.0]``.
        ungrounded_terms: Substantive answer tokens that appear in
            NO source. These are the most-likely hallucinations.
        per_source_citation_scores: Per-document scores. For each source
            ``id``, the fraction of answer tokens that appear in that
            specific source. Identifies which document supports which
            claims when there are multiple sources.
        answer_token_count: Number of substantive tokens in the answer
            after stop-word removal (the denominator of overall_score).
        provenance_trail: Human-readable audit string composing the query
            (if supplied), retrieved sources, answer, and verdict. Suitable
            for inclusion in a board-level audit log.
        threshold: The threshold used for the verdict.
    """

    grounded: bool
    verdict: Verdict
    overall_score: float
    ungrounded_terms: list[str]
    per_source_citation_scores: dict[str, float]
    answer_token_count: int
    provenance_trail: str
    threshold: float = DEFAULT_THRESHOLD

    def to_dict(self) -> dict[str, Any]:
        """Plain-dict representation. Suitable for inclusion in an MCP
        tool response under the ``_groundedness`` field, or for
        cryptographic audit chains."""
        return {
            "grounded": self.grounded,
            "verdict": self.verdict,
            "overall_score": self.overall_score,
            "ungrounded_terms": list(self.ungrounded_terms),
            "per_source_citation_scores": dict(self.per_source_citation_scores),
            "answer_token_count": self.answer_token_count,
            "provenance_trail": self.provenance_trail,
            "threshold": self.threshold,
        }


# ─────────────────────────────────────────────────────────────────────────
# Core API
# ─────────────────────────────────────────────────────────────────────────


def compute_groundedness(
    answer: str,
    sources: list[dict[str, Any]],
    query: str | None = None,
    threshold: float = DEFAULT_THRESHOLD,
) -> GroundednessResult:
    """Measure how well ``answer`` is grounded in ``sources``.

    Args:
        answer: The AI-authored text to check.
        sources: List of source documents. Each must have an ``id`` and
            either ``content`` (preferred) or ``text``. Other fields
            (``title``, ``source``, ``url``) are passed through to the
            provenance trail unchanged.
        query: Optional original query string. Included in the provenance
            trail when supplied.
        threshold: Score above which the answer counts as ``GROUNDED``.
            Default 0.7 per paper §9.3.

    Returns:
        :class:`GroundednessResult` with score, terms, citation scores,
        and provenance trail.

    Raises:
        ValueError: If ``sources`` is empty or any source lacks ``id``.
    """
    if not sources:
        raise ValueError(
            "compute_groundedness requires at least one source. To indicate "
            "an answer was generated without sources, the caller should mark "
            "the response as UNGROUNDED explicitly rather than passing []."
        )
    for i, source in enumerate(sources):
        if "id" not in source:
            raise ValueError(f"Source at index {i} is missing required 'id' field.")

    answer_tokens = _tokenise(answer)
    if not answer_tokens:
        # No substantive tokens to ground — treat as trivially grounded.
        return GroundednessResult(
            grounded=True,
            verdict="GROUNDED",
            overall_score=1.0,
            ungrounded_terms=[],
            per_source_citation_scores={s["id"]: 1.0 for s in sources},
            answer_token_count=0,
            provenance_trail=_build_provenance_trail(
                query=query, sources=sources, answer=answer,
                verdict="GROUNDED", overall_score=1.0,
                ungrounded_terms=[], threshold=threshold,
            ),
            threshold=threshold,
        )

    # Per-source token sets
    source_token_sets: dict[str, set[str]] = {}
    for source in sources:
        text = source.get("content") or source.get("text") or ""
        source_token_sets[source["id"]] = set(_tokenise(text))

    # All-source union
    all_source_tokens: set[str] = set()
    for token_set in source_token_sets.values():
        all_source_tokens |= token_set

    # Overall: fraction of answer tokens that appear in at least one source
    grounded_tokens = [t for t in answer_tokens if t in all_source_tokens]
    overall_score = len(grounded_tokens) / len(answer_tokens)

    # Ungrounded terms: preserve order of first appearance, deduplicate
    ungrounded_terms = _dedupe_preserve_order(
        t for t in answer_tokens if t not in all_source_tokens
    )

    # Per-source: fraction of answer tokens that appear in this specific source
    per_source: dict[str, float] = {}
    for source_id, source_tokens in source_token_sets.items():
        hits = sum(1 for t in answer_tokens if t in source_tokens)
        per_source[source_id] = hits / len(answer_tokens)

    grounded = overall_score >= threshold
    verdict: Verdict = "GROUNDED" if grounded else "UNGROUNDED"

    provenance_trail = _build_provenance_trail(
        query=query,
        sources=sources,
        answer=answer,
        verdict=verdict,
        overall_score=overall_score,
        ungrounded_terms=ungrounded_terms,
        threshold=threshold,
    )

    return GroundednessResult(
        grounded=grounded,
        verdict=verdict,
        overall_score=overall_score,
        ungrounded_terms=ungrounded_terms,
        per_source_citation_scores=per_source,
        answer_token_count=len(answer_tokens),
        provenance_trail=provenance_trail,
        threshold=threshold,
    )


# ─────────────────────────────────────────────────────────────────────────
# Internal: helpers
# ─────────────────────────────────────────────────────────────────────────


def _dedupe_preserve_order(items) -> list[str]:
    """De-duplicate while preserving order of first appearance."""
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _build_provenance_trail(
    *,
    query: str | None,
    sources: list[dict[str, Any]],
    answer: str,
    verdict: Verdict,
    overall_score: float,
    ungrounded_terms: list[str],
    threshold: float,
) -> str:
    """Compose a human-readable audit string.

    Format::

        Provenance trail
        ----------------
        Query: <query or "(not provided)">

        Sources retrieved:
        - [doc-1] Title (relevance source-string)
        - [doc-2] ...

        Answer:
        <answer>

        Verdict: GROUNDED / UNGROUNDED (overall_score=0.85, threshold=0.7)
        Ungrounded terms: [list, or "none"]
    """
    lines = [
        "Provenance trail",
        "----------------",
        f"Query: {query or '(not provided)'}",
        "",
        "Sources retrieved:",
    ]
    for source in sources:
        sid = source["id"]
        title = source.get("title") or source.get("source") or "(untitled)"
        lines.append(f"- [{sid}] {title}")
    lines.extend([
        "",
        "Answer:",
        answer.strip(),
        "",
        f"Verdict: {verdict} (overall_score={overall_score:.3f}, threshold={threshold:.2f})",
        f"Ungrounded terms: {ungrounded_terms or 'none'}",
    ])
    return "\n".join(lines)
