"""Formally-verified properties of the AI-reliability stack.

Verified Autonomy Layer 9 (Formal Verification), §12.3 reference
implementation. The paper acknowledges that Layer 9 is rarely
applicable to neural-network-shaped systems but that small critical
components — threshold mappings, ordering predicates, lookup tables —
remain tractable for SMT-based formal verification.

This module ships one formally-verified property: the mapping from a
confidence score to a Red/Amber/Green status is monotone
non-decreasing — a higher confidence never produces a worse RAG.
The property is encoded as Z3 constraints and proven (or refuted with
a counterexample) by the Z3 SMT solver.

Currently this property is encoded implicitly across many tools
(pm-assumptions, pm-analyse, pm-assure, …). Formalising it means
any module wishing to define its own RAG mapping can have the
property checked by the same verifier, with the same proof — and
the proof's counterexample telling a developer exactly which
threshold ordering is wrong.

Default thresholds and labels are sourced from
``pm_mcp_servers.pm_assumptions``: ``RED < 40, AMBER 40–69, GREEN
>= 70``.
"""

from agent_planning.verified.monotonicity import (
    DEFAULT_RAG_LABELS,
    DEFAULT_RAG_ORDERING,
    DEFAULT_RAG_THRESHOLDS,
    ProofResult,
    evaluate_rag,
    verify_rag_mapping,
)

__all__ = [
    "ProofResult",
    "verify_rag_mapping",
    "evaluate_rag",
    "DEFAULT_RAG_THRESHOLDS",
    "DEFAULT_RAG_LABELS",
    "DEFAULT_RAG_ORDERING",
]
