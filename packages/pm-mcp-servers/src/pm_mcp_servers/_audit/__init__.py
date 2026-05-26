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
* :func:`safe_record_decision` — best-effort wrapper used by every
  MCP server. Catches all exceptions, increments
  :data:`_FAILURE_COUNTER`, and logs a structured warning. Replaces
  the per-module ``_safe_record_decision`` + bare-``pass`` pattern
  identified by audit findings P1.F01, P1.F02, P5.F01.
* :func:`failure_stats` — snapshot of audit-chain failure counters
  exposed by the ``/health`` endpoint so operators can detect
  silent-failure regressions.

The module exposes :data:`AUDIT_DIR` and the lazy chain-cache so test
code can monkeypatch the directory to a per-test ``tmp_path``.
"""

from __future__ import annotations

import json
import logging
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
    "safe_record_decision",
    "failure_stats",
    "reset_failure_stats",
    "rotate_if_needed",
    "chain_sizes",
    "ROTATION_SIZE_BYTES",
]

logger = logging.getLogger(__name__)


# Audit finding P5.F04. The on-disk JSONL files grew without bound,
# making process restart slow and a disk-full failure mode invisible
# to the operator. The rotation policy below is size-driven (not time
# driven — simpler, deterministic, and matches the audit's "expose
# size metric" recommendation). When the current file passes the
# threshold, it is renamed to the next free numbered archive
# (e.g. ``pm_assure.jsonl.1``, ``.2``, ...). The in-memory chain is
# untouched — every entry that has been recorded since process start
# remains in the cache — so the hash chain continues unbroken from
# the next write.
#
# Hydration on a fresh process reads archives in numeric order, then
# the current file, so the recovered chain matches the live one.
ROTATION_SIZE_BYTES = int(
    os.environ.get("PDA_AUDIT_ROTATION_SIZE_BYTES", str(10 * 1024 * 1024))
)


def _archive_path(module_name: str, index: int) -> Path:
    return AUDIT_DIR / f"{module_name}.jsonl.{index}"


def _next_archive_index(module_name: str) -> int:
    """Find the next free archive index for ``module_name``."""
    index = 1
    while _archive_path(module_name, index).exists():
        index += 1
    return index


def rotate_if_needed(module_name: str) -> Path | None:
    """Rotate ``<module>.jsonl`` if it exceeds the size threshold.

    Returns the new archive path on rotation, otherwise ``None``. Safe
    to call before every write — the size check is a single ``stat()``.
    """
    log_path = _log_path(module_name)
    if not log_path.exists():
        return None
    try:
        size = log_path.stat().st_size
    except OSError:
        return None
    if size < ROTATION_SIZE_BYTES:
        return None
    archive = _archive_path(module_name, _next_archive_index(module_name))
    try:
        log_path.rename(archive)
    except OSError as exc:
        logger.warning(
            "audit_chain_rotation_failed",
            extra={
                "audit_module": module_name,
                "size_bytes": size,
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
            },
        )
        return None
    logger.info(
        "audit_chain_rotated",
        extra={
            "audit_module": module_name,
            "archive": str(archive),
            "size_bytes": size,
        },
    )
    return archive


def chain_sizes() -> dict[str, int]:
    """Return current + archive byte sizes per module.

    Exposed via ``/health`` so operators can see audit chain growth
    without parsing JSONL files. Returns ``{}`` if the audit
    directory does not exist.
    """
    sizes: dict[str, int] = {}
    if not AUDIT_DIR.exists():
        return sizes
    for path in AUDIT_DIR.iterdir():
        if not path.is_file():
            continue
        # Match ``<module>.jsonl`` and ``<module>.jsonl.<n>``.
        name = path.name
        if name.endswith(".jsonl"):
            module_name = name[: -len(".jsonl")]
        elif ".jsonl." in name:
            module_name = name.split(".jsonl.")[0]
        else:
            continue
        try:
            sizes[module_name] = sizes.get(module_name, 0) + path.stat().st_size
        except OSError:
            continue
    return sizes


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
    """Load existing entries from disk and rebuild the in-memory chain.

    Reads numbered archives in order (``<module>.jsonl.1`` …
    ``<module>.jsonl.N``) followed by the current ``<module>.jsonl``
    so the recovered chain matches the write-order across rotations
    (audit finding P5.F04).
    """
    signing_key = _signing_key()
    entries: list[dict[str, Any]] = []

    # Archives are written in ascending order of rotation: index 1
    # is the oldest. Hydration reads them in that order so the
    # rebuilt chain matches the original sequence.
    index = 1
    while True:
        archive = _archive_path(module_name, index)
        if not archive.exists():
            break
        _read_jsonl_into(archive, entries)
        index += 1

    log_path = _log_path(module_name)
    if log_path.exists():
        _read_jsonl_into(log_path, entries)

    if not entries:
        return AuditChain(signing_key=signing_key)
    return AuditChain.from_json(json.dumps(entries), signing_key=signing_key)


def _read_jsonl_into(path: Path, entries: list[dict[str, Any]]) -> None:
    """Append JSON-decodable lines from ``path`` to ``entries``.

    Malformed lines are skipped; ``verify_chain`` surfaces them when
    called rather than crashing hydration (audit finding P3.F03 also
    leans on this resilience).
    """
    with open(path, encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                entries.append(json.loads(raw))
            except ValueError:
                continue


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
        # Audit finding P5.F04 — rotate before write so the new entry
        # always lands in a sub-threshold file. Rotation is best-effort
        # (size check + rename); failure to rotate falls through to a
        # normal write so an unwritable archive name never blocks
        # tool output.
        rotate_if_needed(module_name)
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


# ──────────────────────────────────────────────────────────────────────
# Best-effort wrapper + failure-counter telemetry
# ──────────────────────────────────────────────────────────────────────
# Audit findings P1.F01, P1.F02 (silent swallow), P5.F01 (no operator
# visibility) all reduce to the same underlying problem: every MCP
# module wrapped `record_decision` in a bare `try/except: pass`, so a
# disk-full, permissions, or schema-mismatch error was invisible to
# the operator. The wrapper below replaces that pattern.
#
# Behaviour change vs the per-module wrappers:
#   - exceptions are still caught (tool output must not break);
#   - a structured warning is logged with the module + decision name;
#   - a per-module failure counter is incremented for `/health` to
#     expose. Operators can now alert on "audit failures > 0" without
#     parsing logs.

_FAILURE_COUNTER: dict[str, int] = {}
_FAILURE_COUNTER_LOCK = Lock()


def safe_record_decision(
    module_name: str,
    *,
    input_data: Any,
    output_data: Any,
    decision: str,
    action: str,
    metadata: dict[str, Any] | None = None,
) -> AuditEntry | None:
    """Best-effort audit-chain record. Logs and counts on failure.

    Replaces the per-module ``_safe_record_decision`` + bare ``pass``
    pattern flagged in audit findings P1.F01 / P1.F02 / P5.F01.

    On success returns the recorded :class:`AuditEntry`. On failure
    returns ``None`` after logging a warning and incrementing the
    module-scoped failure counter exposed via :func:`failure_stats`.
    """
    try:
        return record_decision(
            module_name,
            input_data=input_data,
            output_data=output_data,
            decision=decision,
            action=action,
            metadata=metadata,
        )
    except Exception as exc:
        with _FAILURE_COUNTER_LOCK:
            _FAILURE_COUNTER[module_name] = (
                _FAILURE_COUNTER.get(module_name, 0) + 1
            )
        logger.warning(
            "audit_chain_record_failed",
            extra={
                # NB: "module" is a reserved LogRecord attribute name;
                # use "audit_module" so structlog/json log handlers do
                # not raise a KeyError on emission.
                "audit_module": module_name,
                "action": action,
                "decision": decision,
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
            },
        )
        return None


def failure_stats() -> dict[str, int]:
    """Return a snapshot of audit-chain failure counters per module.

    Exposed via the ``/health`` endpoint so operators can detect
    silent audit-chain failures without parsing logs.
    """
    with _FAILURE_COUNTER_LOCK:
        return dict(_FAILURE_COUNTER)


def reset_failure_stats() -> None:
    """Reset the failure counter (test helper)."""
    with _FAILURE_COUNTER_LOCK:
        _FAILURE_COUNTER.clear()


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
