# Changelog

All notable changes to the PDA Platform are documented here. Versions
align across the four packages (`pda-platform`, `pm-mcp-servers`,
`pm-data-tools`, `agent-task-planning`) and follow [Semantic
Versioning](https://semver.org/).

## 2.1.0 — 2026-05-26

Multipass-audit remediation cycle. Closes 28 of the 71 findings from
[`docs/audits/multipass-audit-v1.md`](docs/audits/multipass-audit-v1.md);
the remaining 43 are deferred per the audit's own sequence (multi-worker
concurrency, MEDIUM operability polish, LOW cosmetic).

### Added

- **`pm_mcp_servers._validation`** — dispatch-layer input validation seam.
  `sanitise_arguments()` enforces an alphanumeric `project_id` shape and
  caps free-text fields at 50 K characters; `validate_payload_size()`
  caps the JSON payload at 1 MiB; `error_envelope()` returns the
  canonical error shape (`{"error": {"code", "message", "context",
  "schema_version": 1}}`). All three are wired into the unified
  dispatcher so every one of the 126 tools is covered without per-tool
  changes. Addresses audit findings P4.F01, P4.F03, P5.F05.
- **`pm_mcp_servers._audit.safe_record_decision()`** — central wrapper
  that replaces the five module-local `try/except: pass` patterns.
  Catches all exceptions (tool output must not break), logs via the
  stdlib logger, increments a per-module counter exposed by `/health`.
  Closes audit findings P1.F01, P1.F02, P5.F01.
- **`pm_mcp_servers._audit.rotate_if_needed()` + `chain_sizes()`** —
  size-driven rotation for the audit JSONL files (default 10 MiB,
  `PDA_AUDIT_ROTATION_SIZE_BYTES` env-tunable). Numbered archives
  (`<module>.jsonl.1`, `.2`, …); hydration reads archives in order so
  the chain remains unbroken across process restart. Closes audit
  finding P5.F04.
- **`pm_mcp_servers._redteam.load_corpus()`** + starter corpus
  (`corpus/v1.yaml`). 10 adversarial test cases across five categories
  (prompt-injection, unicode-evasion, schema-abuse, oversized-input,
  baseline) plus a four-rule policy. Wired to a regression test that
  feeds the corpus through the L7 harness. Closes audit findings
  P4.F10, P6.F12.
- **JSON-schema enforcement at dispatch** — `call_tool` validates
  inbound arguments against the per-tool `inputSchema` before invoking
  the handler. Malformed inputs now return a clean rejection envelope
  rather than crashing the handler. Closes audit finding P4.F07.
- **`AuditEntry.schema_version`** — new field defaulting to `1`.
  Backward-compatible: entries hydrated from disk without the field
  carry `None` and are excluded from the hash payload, so
  pre-versioning chains still verify byte-for-byte. Closes audit
  finding P3.F03.
- **`/health` endpoint deepened** with `uptime_seconds`,
  `anthropic_api_key_present`, `audit_signing_key_present`,
  `dashboard_token_required`, `audit_failure_count` (per-module dict),
  `audit_chain_size_bytes` (per-module dict). Closes audit findings
  P5.F02, P5.F06, P5.F08.
- **Per-invocation structured logging** in `call_tool` —
  `tool_call_ok` / `tool_call_rejected` / `tool_call_failed` with tool
  name, project_id, elapsed_ms. Closes audit finding P5.F03.
- **Cold-start bootstrap logging** in `pda_platform.remote` — replaces
  raw stderr prints with `_log_bootstrap_phase()` emitting
  `T+s.ss phase=…` entries through the stdlib logger. Closes audit
  finding P5.F07.

### Changed

- **L5 fail-safe (P3.F07)** — a guardrail rule whose `condition`
  raises is now treated as a violation at the rule's *nominal*
  severity. Crashing `BLOCK` → REJECTED; crashing `WARN` → FLAGGED;
  crashing `INFO` → trail-only. Pre-fix behaviour silently downgraded
  to UNKNOWN+APPROVED. One existing test renamed and updated to pin
  the new behaviour.
- **L5 forbidden-phrase matching is Unicode-normalised** — NFKC plus
  Cf-character stripping is applied symmetrically to candidate text
  and configured needles. Catches zero-width-split, full-width Latin,
  and compatibility-ligature evasion. Distinct script digits remain a
  known residual evasion vector for a future cycle. Closes audit
  finding P4.F05.
- **SQLite hardening** — every `AssuranceStore._connect()` now sets
  `journal_mode=WAL`, `busy_timeout=5000`, `synchronous=NORMAL`,
  `foreign_keys=ON`. Default connection timeout raised to 30 s.
  Closes audit findings P2.F02, P3.F01.
- **`AssuranceStore` instances are now process-cached** via
  `pm_data_tools.db.store.get_store(db_path)`. Production
  `_get_store` helpers in `pm_simulation`, `pm_synthesis`, `pm_risk`,
  `pm_resource`, `pm_reporting` route through it; tests still
  instantiate per-test for isolation. Closes audit finding P2.F03.
- **All production `datetime.utcnow()` sites** replaced with
  `datetime.now(timezone.utc)`. Affects the audit chain core, GMPP
  narratives/aggregator, NISTA auth/client/audit, `pm_assumptions`,
  `pm_financial`, `pm_change`. ISO timestamps now include `+00:00`;
  SQLite stores them as TEXT so schemas are unaffected. Closes audit
  finding P3.F10.
- **L5 rejection envelope** now carries `schema_version: 1`. Closes
  audit finding P3.F11.
- **Dashboard endpoints (`/data/*`, `/dashboards/*`) are auth-gated**
  when `PDA_DASHBOARD_TOKEN` is set in the environment. Unset env var
  keeps the endpoint open (current demo posture) but emits a startup
  warning. Closes audit finding P4.F02.
- **Audit-chain lock-ordering convention documented and enforced** —
  modules' chains must be acquired in ascending alphabetical order.
  Violations log a warning (fail-open: preserves tool output) so
  operators can audit offending tools. Closes audit finding P2.F08.
- **`run_reference_class_check.estimate_type` enum widened** to
  include the `cost` and `schedule` aliases the handler already
  accepts. Avoids the new JSON-schema validator rejecting valid
  alias-based calls.
- **Dual lessons-table status documented inline** — `upsert_lesson`
  and `upsert_project_lesson` now carry matching banner comments
  explaining which writes to which table and pointing to a future
  consolidation. Closes audit finding P3.F02.

### Fixed

- 5 pre-existing `test_gmpp/test_models.py` failures (PR #115) —
  `DCANarrative.text` length bounds aligned with the actual prose
  shape; pydantic validators lifted to model level so they run after
  all fields are populated.

### Test impact

- Baseline: 205 passed
- After 2.1.0: 306 passed (+43 audit-fix tests; +5 from gmpp fix;
  +remaining adjustments to existing tests reflecting behaviour
  changes)
- Zero regressions

### Behaviour changes worth flagging for consumers

- **Crashing L5 rules now REJECT instead of silently APPROVE.** Any
  policy with a brittle rule may surface a previously-hidden
  rejection. Inspect `_guardrail_flags.evaluations[*].error` to find
  the offending rule.
- **JSON-schema validation at dispatch.** Tools whose handlers
  previously accepted lenient inputs (alias enum values, missing
  required fields tolerated at handler level) may now be rejected by
  the dispatcher. The widened enum on
  `run_reference_class_check.estimate_type` is the only currently
  known case; if you operate other custom tooling on top of the
  platform, audit your input schemas.
- **ISO timestamps include `+00:00`.** Any consumer that parsed naive
  ISO strings (no timezone suffix) should verify it accepts the
  aware form. Python's `datetime.fromisoformat` handles both.

### Deferred to a future cycle

Per the audit's own sequence: multi-worker concurrency findings
(`fix when scaling beyond single-worker`), MEDIUM operability polish,
LOW cosmetic. See `docs/audits/multipass-audit-v1.md` §"Recommended
remediation sequence" for the full disposition.

---

## 2.0.0 — 2026-05-16

Verified Autonomy major release. 37 PRs implementing the nine-layer
framework (L1–L9) across all 126 tools. See PR #111 for the
consolidated release notes.
