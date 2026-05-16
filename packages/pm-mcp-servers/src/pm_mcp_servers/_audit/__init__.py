"""File-backed audit chain for L8 integrations across modules.

Verified Autonomy Layer 8 (Cryptographic Audit Trails), §11.3 — wraps
the generic :class:`pm_data_tools.audit.AuditChain` primitive (A1)
with persistence so every decision-producing handler in the platform
records a tamper-evident entry that survives across process restarts.

Each MCP module gets its own chain, keyed by module name (e.g.
``"pm_assure"``, ``"pm_assumptions"``). The chains live in JSONL files
under :data:`AUDIT_DIR` (one ``<module>.jsonl`` per chain). On first
record after process start, the chain is hydrated from disk so a new
entry continues the existing hash chain rather than starting a fresh
one.

Optional HMAC signing via ``PDA_AUDIT_SIGNING_KEY`` (env var). When
set, every entry's hash is HMAC-SHA256 rather than plain SHA-256;
re-verification fails without the key. The key is never persisted.

The public surface is intentionally small:

* :func:`record_decision` — append a new entry. Thread-safe per
  module.
* :func:`verify_chain` — walk the chain and check every hash. Returns
  the generic :class:`VerificationResult`.
* :func:`reset_for_testing` — clears in-memory cache and removes the
  on-disk log. Tests use this in a tmp-dir context.

The module exposes :data:`AUDIT_DIR` and the lazy chain-cache so test
code can monkeypatch the directory to a per-test ``tmp_path``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock
from typing import Any

from pm_data_tools.audit import AuditChain, AuditEntry, VerificationResult

__all__ = [
    "AUDIT_DIR",
    "record_decision",
    "verify_chain",
    "reset_for_testing",
]


def _default_audit_dir() -> Path:
    """Resolve the on-disk audit-log directory.

    Env var ``PDA_AUDIT_DIR`` overrides the default location, which is
    ``~/.pm_data_tools/audit`` to sit next to the AssuranceStore
    SQLite database. The directory is created lazily on first record.
    """
    env_override = os.environ.get("PDA_AUDIT_DIR")
    if env_override:
        return Path(env_override)
    return Path.home() / ".pm_data_tools" / "audit"


AUDIT_DIR: Path = _default_audit_dir()
"""Where module-specific audit JSONL files live.

Resolved once at import time from the ``PDA_AUDIT_DIR`` env var or
``~/.pm_data_tools/audit``. Tests monkeypatch this attribute to point
at a per-test tmp directory; the chain cache is keyed by module name
only, so tests should also call :func:`reset_for_testing` to drop the
cached in-memory chain when the directory changes.
"""


_CHAINS: dict[str, AuditChain] = {}
_LOCKS: dict[str, Lock] = {}


def _signing_key() -> str | None:
    """Read the HMAC signing key from the env at every access.

    Allows tests to monkeypatch the env var per test without re-importing
    the module.
    """
    return os.environ.get("PDA_AUDIT_SIGNING_KEY") or None


def _log_path(module_name: str) -> Path:
    return AUDIT_DIR / f"{module_name}.jsonl"


def _hydrate_chain(module_name: str) -> AuditChain:
    """Load existing entries from disk and rebuild the in-memory chain."""
    log_path = _log_path(module_name)
    signing_key = _signing_key()
    if not log_path.exists():
        return AuditChain(signing_key=signing_key)
    entries: list[dict[str, Any]] = []
    with open(log_path, encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                entries.append(json.loads(raw))
            except ValueError:
                # Skip corrupted line — verify_chain will report it
                # when called, rather than crashing during hydration.
                continue
    return AuditChain.from_json(json.dumps(entries), signing_key=signing_key)


def _get_chain(module_name: str) -> tuple[AuditChain, Lock, Path]:
    """Return the cached chain + lock + log path for ``module_name``.

    Creates them on first access. Thread-safe via the per-module lock
    that we install before exposing the chain to callers.
    """
    if module_name not in _CHAINS:
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        _CHAINS[module_name] = _hydrate_chain(module_name)
        _LOCKS[module_name] = Lock()
    return _CHAINS[module_name], _LOCKS[module_name], _log_path(module_name)


def record_decision(
    module_name: str,
    *,
    input_data: Any,
    output_data: Any,
    decision: str,
    action: str,
    metadata: dict[str, Any] | None = None,
) -> AuditEntry:
    """Append a new audit entry for ``module_name``'s chain.

    Args:
        module_name: Short identifier, e.g. ``"pm_assure"``. Used as
            the JSONL filename.
        input_data: The handler's input arguments (or a redacted
            summary). Hashed canonically; the raw content is not
            stored.
        output_data: The handler's output (or a summary). Hashed
            canonically.
        decision: Short verdict string for the entry, e.g.
            ``"GATE_READY_AMBER"``.
        action: Action label — typically the tool name, e.g.
            ``"assess_gate_readiness"``.
        metadata: Optional free-form module-specific context.

    Returns:
        The recorded :class:`AuditEntry`. The chain is mutated in
        place; the JSONL file is appended to under the chain's lock.

    Audit-chain failures are non-fatal to the caller's behaviour: a
    record failure (e.g. disk full) raises here, so callers that want
    tool execution to continue should wrap this call in ``try/except``.
    """
    chain, lock, log_path = _get_chain(module_name)
    with lock:
        entry = chain.record(
            input_data=input_data,
            output_data=output_data,
            decision=decision,
            action=action,
            metadata=metadata or {},
        )
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict(), default=str) + "\n")
        return entry


def verify_chain(module_name: str) -> VerificationResult:
    """Walk ``module_name``'s chain and check every hash + link.

    Returns the generic :class:`VerificationResult`. Non-mutating.
    """
    chain, lock, _ = _get_chain(module_name)
    with lock:
        return chain.verify()


def reset_for_testing(module_name: str | None = None) -> None:
    """Clear in-memory chain cache and (optionally) on-disk log.

    Used by tests to isolate the audit state across test cases.
    When ``module_name`` is ``None``, clears every module's chain.
    The disk log is removed only if the on-disk path is below
    :data:`AUDIT_DIR` — guards against accidentally deleting a real
    operator audit log when a test forgets to monkeypatch
    ``AUDIT_DIR``.
    """
    targets = [module_name] if module_name else list(_CHAINS.keys())
    for name in targets:
        lock = _LOCKS.get(name)
        if lock is None:
            # Not yet hydrated — just drop the on-disk file if present.
            log_path = _log_path(name)
            try:
                if log_path.exists() and log_path.is_relative_to(AUDIT_DIR):
                    log_path.unlink()
            except (AttributeError, ValueError):
                pass
            continue
        with lock:
            log_path = _log_path(name)
            try:
                if log_path.exists() and log_path.is_relative_to(AUDIT_DIR):
                    log_path.unlink()
            except (AttributeError, ValueError):
                pass
            _CHAINS.pop(name, None)
            _LOCKS.pop(name, None)


def _refresh_audit_dir_for_testing(new_dir: Path) -> None:
    """Used by tests to point the audit dir at a tmp path.

    Updates the module-level :data:`AUDIT_DIR` and drops every cached
    chain so subsequent records start fresh in the new location.
    """
    global AUDIT_DIR  # noqa: PLW0603 — test plumbing
    AUDIT_DIR = new_dir
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    _CHAINS.clear()
    _LOCKS.clear()
