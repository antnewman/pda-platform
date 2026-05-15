"""Generic cryptographic audit chain primitive.

The :class:`AuditChain` records decisions as a tamper-evident hash chain
matching the reference architecture in *Verified Autonomy* §11.3 (Newman et
al., May 2026, DOI 10.5281/zenodo.19096229).

Two primitives are exposed:

* :class:`AuditChain` — chained-decision audit. Every entry contains the
  SHA-256 hash of the entry before it. If anyone modifies a past entry,
  every subsequent entry's hash mismatches and :meth:`AuditChain.verify`
  reports the tampering. With a signing key, entries are HMAC-SHA256
  signed so authenticity is verifiable too.
* :func:`compute_consistency_hash` — structural-consistency variant
  described in §11.4. Useful for proving an AI system is deciding
  consistently across replays of the same input (e.g. for regulator
  questions like "is this system making decisions defensibly?").

The :mod:`pm_data_tools.integrations.nista.audit` module wraps this
primitive with NISTA-specific persistence and field semantics.
"""

from pm_data_tools.audit.chain import (
    AuditChain,
    AuditEntry,
    VerificationResult,
    canonical_serialise,
    compute_consistency_hash,
)

__all__ = [
    "AuditChain",
    "AuditEntry",
    "VerificationResult",
    "canonical_serialise",
    "compute_consistency_hash",
]
