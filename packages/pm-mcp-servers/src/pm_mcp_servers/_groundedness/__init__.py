"""Groundedness checking for AI-authored MCP tool outputs.

Verified Autonomy Layer 6 (RAG as Explainability), §9.3 reference
implementation. Shifts the trust question from "do I trust the model?"
to "do I trust these sources?" — a question a human reviewer can answer
without understanding the model.

The :func:`compute_groundedness` function takes an answer string and a
list of source documents, and returns a verdict (``GROUNDED`` /
``UNGROUNDED``), an overall score, the per-source citation scores, and
crucially the list of *ungrounded terms* — tokens in the answer that
appear in no source. These are the terms most likely to have been
hallucinated.

Usage::

    from pm_mcp_servers._groundedness import compute_groundedness

    result = compute_groundedness(
        answer="The training environment will be ready by Q2.",
        sources=[
            {"id": "doc-1", "content": "The training environment is scheduled for Q2 readiness."},
            {"id": "doc-2", "content": "User capability training requires the environment."},
        ],
    )
    result.grounded                      # True / False
    result.overall_score                 # 0.0 - 1.0
    result.ungrounded_terms              # list of unsupported tokens
    result.per_source_citation_scores    # {"doc-1": 0.83, "doc-2": 0.33}
    result.provenance_trail              # human-readable audit string
"""

from pm_mcp_servers._groundedness.checker import (
    GroundednessResult,
    Verdict,
    compute_groundedness,
)

__all__ = [
    "GroundednessResult",
    "Verdict",
    "compute_groundedness",
]
