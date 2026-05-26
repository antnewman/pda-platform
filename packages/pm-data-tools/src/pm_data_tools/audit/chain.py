"""Generic cryptographic audit chain primitive.

Implementation of the chained-decision audit and structural-consistency
hashing primitives described in *Verified Autonomy* §11.3–§11.4.

The chain is intentionally storage-agnostic. The in-memory list of entries
is the source of truth; persistence (file, database, blob store) is a
concern of consumers, who can call :meth:`AuditChain.export_json` and
:meth:`AuditChain.from_json` to ferry the chain between processes.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

__all__ = [
    "AuditChain",
    "AuditEntry",
    "VerificationResult",
    "canonical_serialise",
    "compute_consistency_hash",
]


# ─────────────────────────────────────────────────────────────────────────
# Canonical serialisation
# ─────────────────────────────────────────────────────────────────────────


def canonical_serialise(payload: Any) -> str:
    """Return a deterministic JSON string for ``payload``.

    Keys are sorted; whitespace is minimal; datetimes are ISO 8601 strings.

    Two structurally-identical payloads always produce the same string,
    regardless of how their callers built them. This is the property the
    paper's §11.3 hash chain depends on — two callers running the same
    decision must produce the same entry hash for the verification step
    to be meaningful.
    """
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=_json_default)


def _json_default(value: Any) -> Any:
    """``json.dumps`` ``default`` callback that handles common non-JSON types."""
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "model_dump"):  # pydantic v2
        return value.model_dump()
    if hasattr(value, "dict"):  # pydantic v1
        return value.dict()
    return str(value)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _hmac_sha256(key: bytes, text: str) -> str:
    return hmac.new(key, text.encode("utf-8"), hashlib.sha256).hexdigest()


# ─────────────────────────────────────────────────────────────────────────
# Structural-consistency hash (paper §11.4)
# ─────────────────────────────────────────────────────────────────────────


def compute_consistency_hash(decision: dict[str, Any]) -> str:
    """Return SHA-256 of a canonically-serialised decision dict.

    The structural-consistency primitive from *Verified Autonomy* §11.4.
    Two replays of the same input that produce structurally-identical
    decision dicts will have the same consistency hash. Replays whose
    decisions differ — different verdict, different counts, different
    flag set — produce different hashes.

    Use this in conjunction with the chained-decision audit
    (:class:`AuditChain`) to answer two related but distinct regulator
    questions: *what was decided* (chain) and *is the system deciding
    consistently across replays* (consistency hash).
    """
    return _sha256(canonical_serialise(decision))


# ─────────────────────────────────────────────────────────────────────────
# Audit entry
# ─────────────────────────────────────────────────────────────────────────


# Audit finding P3.F03. The current schema for an :class:`AuditEntry`
# carries no version marker. If a future PR adds a required field, old
# chains deserialised from disk lack it and verification silently
# changes shape. Adding a version field is the standard fix, but it
# must not break verification of pre-existing chains — entries written
# without the field already have a stored ``entry_hash`` computed
# over the older payload shape. The implementation keeps backward
# compatibility by:
#
#   * marking new entries with ``schema_version = 1``;
#   * keeping ``schema_version = None`` for entries hydrated from disk
#     that lack the field (these are de-facto "v0");
#   * excluding ``schema_version`` from the hash payload when its value
#     is ``None`` — so a v0 entry rehashes to the same digest it had
#     when written.
#
# A bump beyond v1 in the future would add a ``from_dict`` branch on
# the value rather than mutating this class in place.
AUDIT_ENTRY_SCHEMA_VERSION = 1


@dataclass
class AuditEntry:
    """Immutable audit log entry. One per decision.

    The ``input_hash`` and ``output_hash`` are SHA-256 hashes of the
    canonical serialisation of the input arguments and output result. The
    actual content is not stored, supporting both compactness and the
    EU GDPR right-to-erasure (the hash is one-way; the input itself can
    be deleted from any source-of-truth store without breaking the chain).

    ``decision`` is the short verdict string (e.g. ``"APPROVED"``,
    ``"REJECTED"``, ``"GMPP_SUBMITTED"``). ``metadata`` is a free-form
    dict for module-specific context (model version, gate stage, etc.).

    ``entry_hash`` and ``previous_entry_hash`` form the tamper-evident
    chain. They are populated by :meth:`AuditChain.record`; consumers
    should not set them by hand.

    ``schema_version`` flags the entry shape (audit finding P3.F03).
    Entries written by the current code default to
    :data:`AUDIT_ENTRY_SCHEMA_VERSION`. Entries hydrated from older
    on-disk JSONL files that predate the field carry ``None``; those
    are treated as v0 and excluded from the hash payload so their
    stored digest still verifies.
    """

    timestamp: datetime
    action: str
    input_hash: str
    output_hash: str
    decision: str
    metadata: dict[str, Any] = field(default_factory=dict)
    previous_entry_hash: str | None = None
    entry_hash: str | None = None
    schema_version: int | None = AUDIT_ENTRY_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Return a plain-dict form suitable for JSON encoding.

        Pre-version entries (``schema_version is None``) omit the field
        so the hash payload exactly matches what was used at write
        time. New entries include it.
        """
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp
        if self.schema_version is None:
            d.pop("schema_version", None)
        return d

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> AuditEntry:
        """Inverse of :meth:`to_dict`.

        Entries without a ``schema_version`` key in the raw dict are
        treated as v0 (pre-versioning) — the field is set to ``None``
        so :meth:`to_dict` omits it from the hash payload and
        verification still passes.
        """
        ts = raw.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return cls(
            timestamp=ts,
            action=raw["action"],
            input_hash=raw["input_hash"],
            output_hash=raw["output_hash"],
            decision=raw["decision"],
            metadata=raw.get("metadata", {}) or {},
            previous_entry_hash=raw.get("previous_entry_hash"),
            entry_hash=raw.get("entry_hash"),
            schema_version=raw.get("schema_version"),
        )


# ─────────────────────────────────────────────────────────────────────────
# Verification result
# ─────────────────────────────────────────────────────────────────────────


@dataclass
class VerificationResult:
    """Outcome of :meth:`AuditChain.verify`.

    ``status`` is one of ``"VALID"`` (every hash recomputes), ``"TAMPERED"``
    (a hash mismatched — chain integrity broken), or ``"EMPTY"`` (chain is
    empty; vacuously valid but flagged so callers can distinguish).

    ``failed_at_index`` is set when ``status == "TAMPERED"`` and identifies
    the first entry (0-indexed) where verification failed.
    """

    status: Literal["VALID", "TAMPERED", "EMPTY"]
    message: str
    failed_at_index: int | None = None

    @property
    def is_valid(self) -> bool:
        return self.status == "VALID"


# ─────────────────────────────────────────────────────────────────────────
# Audit chain
# ─────────────────────────────────────────────────────────────────────────


class AuditChain:
    """Tamper-evident chain of audit entries.

    Usage::

        chain = AuditChain(signing_key="secret-key")
        chain.record(
            input_data={"project": "PROJ-001", "amount": 15000},
            output_data={"verdict": "REJECTED", "rule": "max_amount"},
            decision="REJECTED",
            action="loan_assessment",
            metadata={"model_version": "v1.2.0"},
        )

        result = chain.verify()
        assert result.is_valid

        # Ferry to another process
        json_str = chain.export_json()
        reimported = AuditChain.from_json(json_str, signing_key="secret-key")
        assert reimported.verify().is_valid

    Construction is cheap; an empty chain holds no state. Calling
    :meth:`record` mutates the chain by appending an entry whose hash
    incorporates the prior entry's hash. The chain therefore has a single
    well-defined integrity property: every entry's stored ``entry_hash``
    must equal the hash recomputed from its other fields plus the prior
    entry's hash. :meth:`verify` walks the chain and checks this property.

    Optional HMAC signing. If constructed with ``signing_key`` (a string),
    every entry's hash is computed as ``HMAC-SHA256(signing_key, canonical)``
    rather than plain SHA-256. This binds the chain to the signing key:
    re-verifying with the wrong key fails. The key is never stored in the
    chain itself — both parties must hold it out of band.
    """

    def __init__(self, signing_key: str | None = None):
        self._entries: list[AuditEntry] = []
        self._signing_key: bytes | None = signing_key.encode("utf-8") if signing_key else None

    # ── Public API ──────────────────────────────────────────────────────

    def record(
        self,
        input_data: Any,
        output_data: Any,
        decision: str,
        action: str = "DECISION",
        metadata: dict[str, Any] | None = None,
        timestamp: datetime | None = None,
    ) -> AuditEntry:
        """Append a new entry to the chain. Return the recorded entry.

        Hashes are computed canonically. ``input_data`` and ``output_data``
        can be any JSON-serialisable value (dict, list, str, pydantic model);
        non-JSON types are stringified via the default callback.
        """
        entry = AuditEntry(
            timestamp=timestamp or datetime.now(timezone.utc),
            action=action,
            input_hash=_sha256(canonical_serialise(input_data)),
            output_hash=_sha256(canonical_serialise(output_data)),
            decision=decision,
            metadata=metadata or {},
            previous_entry_hash=self._entries[-1].entry_hash if self._entries else None,
        )
        entry.entry_hash = self._compute_entry_hash(entry)
        self._entries.append(entry)
        return entry

    def verify(self) -> VerificationResult:
        """Walk the chain and check every entry's hash and chain link.

        Returns a :class:`VerificationResult`. Non-mutating; safe to call
        as often as needed.
        """
        if not self._entries:
            return VerificationResult(status="EMPTY", message="Chain contains no entries.")

        previous_hash: str | None = None
        for i, entry in enumerate(self._entries):
            # Chain link
            if entry.previous_entry_hash != previous_hash:
                return VerificationResult(
                    status="TAMPERED",
                    message=(
                        f"Entry {i} previous_entry_hash mismatch: "
                        f"expected {previous_hash!r}, got {entry.previous_entry_hash!r}."
                    ),
                    failed_at_index=i,
                )
            # Recompute hash and compare
            recomputed = self._compute_entry_hash(entry)
            if entry.entry_hash != recomputed:
                return VerificationResult(
                    status="TAMPERED",
                    message=(
                        f"Entry {i} entry_hash mismatch: stored {entry.entry_hash!r}, "
                        f"recomputed {recomputed!r}. Entry fields have been modified, "
                        f"or the signing key is wrong."
                    ),
                    failed_at_index=i,
                )
            previous_hash = entry.entry_hash

        return VerificationResult(
            status="VALID",
            message=f"All {len(self._entries)} entries verified.",
        )

    def export_json(self) -> str:
        """Serialise the chain to a JSON array string."""
        return json.dumps([e.to_dict() for e in self._entries], sort_keys=True, default=_json_default)

    @classmethod
    def from_json(cls, json_str: str, signing_key: str | None = None) -> AuditChain:
        """Reconstruct a chain from a string previously produced by
        :meth:`export_json`. Optionally pass the signing key to allow
        subsequent :meth:`verify` calls to recompute HMAC entry hashes.
        """
        raw = json.loads(json_str)
        if not isinstance(raw, list):
            raise ValueError("AuditChain.from_json expects a JSON array at the top level.")
        chain = cls(signing_key=signing_key)
        chain._entries = [AuditEntry.from_dict(item) for item in raw]
        return chain

    # ── Read-only views ────────────────────────────────────────────────

    @property
    def entries(self) -> list[AuditEntry]:
        """Return a copy of the entry list. Mutating the copy does not
        affect the chain."""
        return list(self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    # ── Internal ───────────────────────────────────────────────────────

    def _compute_entry_hash(self, entry: AuditEntry) -> str:
        """Hash every field of ``entry`` except ``entry_hash`` itself.

        With a signing key, this is HMAC-SHA256; otherwise plain SHA-256.
        The serialisation is canonical (sorted keys, no whitespace) so
        two callers computing the hash of the same entry get the same
        digest regardless of how their dicts were built.
        """
        payload = {k: v for k, v in entry.to_dict().items() if k != "entry_hash"}
        canonical = canonical_serialise(payload)
        if self._signing_key is not None:
            return _hmac_sha256(self._signing_key, canonical)
        return _sha256(canonical)
