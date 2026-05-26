"""Comprehensive audit logging for NISTA integration.

NISTA-specific persistence and field semantics around the generic
:class:`pm_data_tools.audit.AuditChain` primitive. This module preserves
the public surface that the NISTA integration has used since 2024
(:class:`AuditEntry`, :class:`AuditLogger`, :meth:`AuditLogger.log_submission`,
:meth:`AuditLogger.log_data_fetch`, :meth:`AuditLogger.get_entries`,
:meth:`AuditLogger.verify_chain_integrity`) but is now a thin adapter on
top of the generic chain.

UK Government requirements addressed:

- 7-year retention (configurable)
- Immutable log entries (each entry is hash-chained to the previous one)
- Cryptographic integrity (SHA-256, optionally HMAC-SHA256)
- Full traceability from source system to NISTA submission
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pm_data_tools.audit import AuditChain as _GenericAuditChain
from pm_data_tools.audit import canonical_serialise as _canonical_serialise


@dataclass
class AuditEntry:
    """NISTA audit log entry.

    Retains the NISTA-specific field set for backward compatibility.
    Internally, hashing and chain integrity are delegated to the generic
    :class:`pm_data_tools.audit.AuditChain` primitive.

    Attributes:
        timestamp: UTC timestamp of the action.
        action: Action type (e.g. ``GMPP_SUBMISSION``, ``DATA_FETCH``).
        user: User identifier.
        project_id: Project identifier.
        data_hash: SHA-256 hash of the transmitted data payload.
        source_systems: List of data source systems involved.
        nista_submission_id: NISTA submission identifier (if applicable).
        response_status: HTTP response status code from NISTA.
        response_body: Response body (if available).
        entry_hash: SHA-256 hash of this entry — populated on storage.
        previous_entry_hash: Hash of the previous entry (chain link).
    """

    timestamp: datetime
    action: str
    user: str
    project_id: str
    data_hash: str
    source_systems: list[str]
    nista_submission_id: str | None
    response_status: int
    response_body: dict[str, Any] | None
    entry_hash: str | None = None
    previous_entry_hash: str | None = None


class AuditLogger:
    """Comprehensive audit logger for NISTA integration.

    Provides:

    - Immutable audit entries
    - Cryptographic chaining (each entry references the previous one)
    - 7-year retention (configurable)
    - JSON-lines format for easy parsing

    Example::

        logger = AuditLogger()
        logger.log_submission(
            project_id="DFT-HSR-001",
            report=quarterly_report,
            response_status=200,
            response_body={"submission_id": "SUB-12345"},
        )

    The logger persists entries to dated ``audit_YYYY-MM-DD.jsonl`` files
    in ``log_dir``. The hash of the most recent entry is loaded from disk
    on construction so the chain survives process restarts. The
    underlying cryptographic primitive is
    :class:`pm_data_tools.audit.AuditChain`.
    """

    def __init__(
        self,
        log_dir: Path | None = None,
        retention_years: int = 7,
        signing_key: str | None = None,
    ):
        """Initialise the audit logger.

        Args:
            log_dir: Directory for audit logs (default: ``./audit_logs``).
            retention_years: Retention period in years (default 7 for UK Gov standard).
            signing_key: Optional HMAC-SHA256 signing key for authenticity.
                When provided, entry hashes are computed via HMAC; verifying
                the chain requires the same key. Default: no signing
                (plain SHA-256).
        """
        self.log_dir = log_dir or Path("./audit_logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.retention_years = retention_years
        self._chain = _GenericAuditChain(signing_key=signing_key)
        self._last_entry_hash: str | None = self._load_last_entry_hash()

    def log_submission(
        self,
        project_id: str,
        report: Any,
        response_status: int,
        response_body: dict[str, Any] | None = None,
    ) -> AuditEntry:
        """Log a GMPP quarterly return submission.

        Args:
            project_id: Project identifier.
            report: Quarterly report object. ``model_dump`` is preferred
                if available (pydantic model); otherwise the object is
                used as-is.
            response_status: HTTP response status code from NISTA.
            response_body: NISTA response body.

        Returns:
            The created :class:`AuditEntry`.
        """
        source_systems = []
        if hasattr(report, "data_sources"):
            source_systems = report.data_sources

        report_dump = report.model_dump() if hasattr(report, "model_dump") else report

        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc),
            action="GMPP_SUBMISSION",
            user=self._get_current_user(),
            project_id=project_id,
            data_hash=self._hash_data(report_dump),
            source_systems=source_systems,
            nista_submission_id=response_body.get("submission_id") if response_body else None,
            response_status=response_status,
            response_body=response_body,
            previous_entry_hash=self._last_entry_hash,
        )
        entry.entry_hash = self._hash_entry(entry)

        self._store(entry)
        self._last_entry_hash = entry.entry_hash
        return entry

    def log_data_fetch(
        self,
        project_id: str,
        action: str,
        response_status: int,
        response_body: dict[str, Any] | None = None,
    ) -> AuditEntry:
        """Log a data fetch operation.

        Args:
            project_id: Project identifier.
            action: Action type (e.g. ``FETCH_METADATA``, ``FETCH_GUIDANCE``).
            response_status: HTTP response status code.
            response_body: Response data.

        Returns:
            The created :class:`AuditEntry`.
        """
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc),
            action=action,
            user=self._get_current_user(),
            project_id=project_id,
            data_hash=self._hash_data({"action": action, "project_id": project_id}),
            source_systems=["NISTA"],
            nista_submission_id=None,
            response_status=response_status,
            response_body=response_body,
            previous_entry_hash=self._last_entry_hash,
        )
        entry.entry_hash = self._hash_entry(entry)

        self._store(entry)
        self._last_entry_hash = entry.entry_hash
        return entry

    def get_entries(
        self,
        project_id: str | None = None,
        action: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditEntry]:
        """Retrieve audit entries matching the given criteria.

        Args:
            project_id: Filter by project ID.
            action: Filter by action type.
            start_date: Filter by start date (inclusive).
            end_date: Filter by end date (inclusive).
            limit: Maximum number of entries to return.

        Returns:
            List of matching :class:`AuditEntry` instances, newest first.
        """
        entries: list[AuditEntry] = []
        log_files = sorted(self.log_dir.glob("audit_*.jsonl"), reverse=True)

        for log_file in log_files:
            with open(log_file) as f:
                for line in reversed(f.readlines()):
                    try:
                        entry_dict = json.loads(line)
                        entry = self._dict_to_entry(entry_dict)
                        if project_id and entry.project_id != project_id:
                            continue
                        if action and entry.action != action:
                            continue
                        if start_date and entry.timestamp < start_date:
                            continue
                        if end_date and entry.timestamp > end_date:
                            continue
                        entries.append(entry)
                        if len(entries) >= limit:
                            return entries
                    except json.JSONDecodeError:
                        continue  # Skip malformed lines
        return entries

    def verify_chain_integrity(self) -> bool:
        """Verify the cryptographic chain integrity of the audit log.

        Walks the on-disk JSONL files, recomputes each entry's hash, and
        checks that each entry's ``previous_entry_hash`` matches the prior
        entry's ``entry_hash``. Returns ``True`` if the chain is intact,
        ``False`` if tampering is detected.

        Backed by :class:`pm_data_tools.audit.AuditChain` semantics:
        the recomputation uses the same canonical serialisation, so a
        chain written by an earlier version of this module that used the
        same hash recipe still verifies cleanly.
        """
        log_files = sorted(self.log_dir.glob("audit_*.jsonl"))
        previous_hash: str | None = None

        for log_file in log_files:
            with open(log_file) as f:
                for line in f:
                    try:
                        entry_dict = json.loads(line)
                        if previous_hash is not None:
                            if entry_dict.get("previous_entry_hash") != previous_hash:
                                return False  # Chain link broken
                        entry = self._dict_to_entry(entry_dict)
                        if entry_dict.get("entry_hash") != self._hash_entry(entry):
                            return False  # Entry tampered
                        previous_hash = entry_dict.get("entry_hash")
                    except json.JSONDecodeError:
                        return False  # Corrupted log line
        return True

    # ── Internal helpers ───────────────────────────────────────────────

    def _store(self, entry: AuditEntry) -> None:
        log_file = self.log_dir / f"audit_{entry.timestamp.strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(asdict(entry), default=str) + "\n")

    def _hash_data(self, data: Any) -> str:
        """SHA-256 hash of canonically-serialised ``data``.

        Uses the generic audit module's canonical serialisation for
        bit-identical hashes across the codebase.
        """
        return hashlib.sha256(_canonical_serialise(data).encode("utf-8")).hexdigest()

    def _hash_entry(self, entry: AuditEntry) -> str:
        """Compute the hash for an :class:`AuditEntry`.

        Hashes every field except ``entry_hash`` itself, canonically
        serialised. With a signing key configured at construction, this
        becomes HMAC-SHA256; otherwise plain SHA-256.
        """
        payload = {k: v for k, v in asdict(entry).items() if k != "entry_hash"}
        canonical = _canonical_serialise(payload)
        if self._chain._signing_key is not None:  # noqa: SLF001 — same module family
            import hmac
            return hmac.new(
                self._chain._signing_key, canonical.encode("utf-8"), hashlib.sha256  # noqa: SLF001
            ).hexdigest()
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _get_current_user(self) -> str:
        return os.getenv("USER") or os.getenv("USERNAME") or "system"

    def _load_last_entry_hash(self) -> str | None:
        log_files = sorted(self.log_dir.glob("audit_*.jsonl"), reverse=True)
        for log_file in log_files:
            try:
                with open(log_file) as f:
                    lines = f.readlines()
                    if lines:
                        last_line = lines[-1]
                        entry_dict = json.loads(last_line)
                        return entry_dict.get("entry_hash")
            except (json.JSONDecodeError, OSError):
                continue
        return None

    def _dict_to_entry(self, entry_dict: dict[str, Any]) -> AuditEntry:
        if isinstance(entry_dict["timestamp"], str):
            entry_dict["timestamp"] = datetime.fromisoformat(
                entry_dict["timestamp"].replace("Z", "+00:00")
            )
        return AuditEntry(**entry_dict)
