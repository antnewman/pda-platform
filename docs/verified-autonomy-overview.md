# Verified Autonomy on the PDA Platform — Consumer Overview

**Status:** Production. All nine layers wired and shipping in tool responses as of v1.2.0.

**Paper:** Newman, A. et al. *Verified Autonomy: A Nine-Layer Framework for AI Reliability in High-Stakes Decision Support.* May 2026. DOI: [10.5281/zenodo.19096229](https://doi.org/10.5281/zenodo.19096229)

---

## What is Verified Autonomy?

Verified Autonomy is a nine-layer framework for making AI-assisted decisions defensible under regulator scrutiny. Each layer addresses a specific failure mode that affects large-language-model outputs in high-stakes settings: overclaim, hallucination, miscalibration, leak of scaffolding, fabricated rationale, untraceable decision provenance, and lack of formal guarantees on the small kernels that matter most.

The PDA Platform is the **production reference** cited by the paper for Layers 1–3, and now implements all nine layers end-to-end. Every AI-authored response from the platform's nine prose-bearing tools (board exception reports, gate review summaries, narrative-divergence analyses, pre-mortem questions, benefits narratives, portfolio summaries, lessons sections, PIR templates, and assumption reports) passes through a layered pipeline before reaching the consumer: deterministic guardrails (L5) gate the output, groundedness checking (L6) annotates it, quality scoring (L3) flags potential hallucinations, calibration (L4) wraps point forecasts in coverage-guaranteed intervals, the four-tier router (L2) decides whether human review is required, and a tamper-evident audit chain (L8) records the decision.

This document explains what each layer means in practice, where it lives in the platform's code, and what the consumer sees in tool responses.

---

## The nine layers, as implemented on the platform

### L1 — Inverse Confidence Weighting

**What it does.** When the platform aggregates a set of field-level confidence scores into an overall confidence, it weights the low-confidence fields more heavily (formula: `weight = 2.0 - conf`). A single low-confidence field drags the aggregate down disproportionately — the conservative fail-safe.

**Where it lives.** `agent_planning.confidence.compute_overall_confidence` (legacy float-returning API) and `agent_planning.confidence.compute_overall_confidence_with_gap` (returns `{"weighted": w, "plain_mean": p, "gap": p - w}` so the consumer sees how much the inverse-weighting differs from naive averaging).

**What the consumer sees.** When the gap is large, the naive mean is hiding low-confidence fields. Surface both numbers and let the reviewer judge.

### L2 — Outlier Detection as Hard Escalation

**What it does.** A four-tier router decides whether AI output needs human review: `EXPERT_REQUIRED` / `DETAILED_REVIEW` / `SPOT_CHECK` / `NONE`. The crucial property is the **OR fail-safe**: outliers OR low confidence each independently trigger escalation. Only the AND-clean path (no outliers AND confidence ≥ 0.8) gets to auto-process.

**Where it lives.** `agent_planning.escalation.route`.

**Consumer-facing tool:** `route_outputs_to_review` (pm-assure). Reads stored assumption-confidence scores, aggregates them, dispatches to the router, and returns the routing decision with the reason, consensus, and per-sample outlier reports.

### L3 — Making Failures Visible

**What it does.** Composes the four reliability components (coherence, relevance, completeness, semantic entropy) into a single quality score, and produces a `potential_hallucinations` boolean. A "low-quality" or "potentially hallucinated" verdict surfaces the failure mode rather than hiding it inside a high-confidence number.

**Where it lives.** `agent_planning.quality.compute_quality_score`. Composition into MCP responses happens via `pm_mcp_servers._quality.derive_quality_from_groundedness`.

**What the consumer sees.** A top-level `_quality` field on every AI-authored response carrying `overall_score`, `components`, `flagged_as_low_quality`, and `potential_hallucinations`. The boolean fires when (a) groundedness verdict is `UNGROUNDED` OR (b) more than 30% of answer tokens are ungrounded — two independent triggers.

### L4 — Calibration and Conformal Prediction

**What it does.** Two related primitives. **Calibration measurement** (Expected Calibration Error, reliability diagrams) tells you whether stated confidence matches observed accuracy. **Conformal prediction** wraps point estimates in coverage-guaranteed intervals — under exchangeability, the interval contains the true value with probability at least `1 - alpha` regardless of how miscalibrated the underlying model is.

**Where it lives.** `agent_planning.calibration` — `compute_ece`, `find_temperature`, `apply_temperature_scaling`, `calibrate_conformal`, `conformal_predict`, `evaluate_coverage`, `conformal_predict_band`.

**Consumer-facing tools and fields:**
- `evaluate_calibration` (pm-analyse) — new MCP tool returning ECE + per-bin reliability data + temperature-scaling pointer.
- `run_schedule_simulation` (pm-simulation) — every response now carries a `_calibration` field with conformal P50/P80 bands when the project has at least 5 stored residuals per quantile. Without history: `status: "NOT_COMPUTED"` with the reason.
- `run_reference_class_check` (pm-knowledge) — every response carries a `_calibration` field with a conformal band around the IPA P80, synthesised from the bundled IPA descriptors (median + P80 + mean).

### L5 — Deterministic Guardrails

**What it does.** Before an AI-authored prose output reaches the consumer, it passes through a deterministic policy engine. Forbidden phrases (overclaim like "100% certain", template leaks like "INSERT NARRATIVE HERE") cause the engine to either FLAG the output (annotation added) or REJECT it (output replaced with structured error JSON, original prose suppressed). The pattern is **"model proposes, rule decides"** — the rules are transparent Python and a regulator can re-derive the verdict by hand.

**Where it lives.** `pm_mcp_servers._guardrails` — `Rule`, `Severity`, `Verdict`, `evaluate`, four helper builders (`build_range_rule`, `build_required_field_rule`, `build_allowed_values_rule`, `build_forbidden_phrase_rule`), `wrap_tool_output` decorator.

**What the consumer sees.** A clean AI-authored response when the output passes. A `_guardrail_flags` annotation when WARN rules fire (current policies use BLOCK only; reserved for future use). A structured rejection JSON `{"error": "guardrail_rejected", "verdict": "REJECTED", "triggered": [...], "evaluations": [...]}` when BLOCK rules fire — the original prose is **not** returned. Consumers should detect this shape and surface a retry/escalation path.

Tools gated: `generate_board_exception_report`, `generate_assumption_report`, `generate_gate_review_summary`, `detect_narrative_divergence`, `generate_premortem_questions`, `generate_benefits_narrative`, `generate_portfolio_summary`, `generate_lessons_section`, `generate_pir_template`.

### L6 — RAG as Explainability

**What it does.** Token-overlap groundedness checking. Compares the AI's answer against the source data that fed the prompt; produces an overall score (fraction of answer tokens supported by at least one source), per-source citation scores (which source supports which fragments), and the list of **ungrounded terms** — tokens in the answer that appear in no source, the most likely hallucinations.

**Where it lives.** `pm_mcp_servers._groundedness.compute_groundedness`.

**What the consumer sees.** A `_groundedness` field on every AI-authored response with `verdict` (`GROUNDED` / `UNGROUNDED`), `overall_score`, `ungrounded_terms`, `per_source_citation_scores`, and `provenance_trail` (a human-readable audit string composing the query, sources, answer, and verdict). Markdown-output tools embed this as JSON inside an HTML comment at the end of the document; JSON-output tools attach it as a top-level field. When you see `ungrounded_terms: ["zeppelin", "convoy"]`, those are the two terms in the AI's prose that have no source backing — the focus of any challenge.

### L7 — Adversarial Testing

**What it does.** A red-team harness for running adversarial input suites against a system-under-test and reporting findings by severity (`CRITICAL` / `HIGH` / `MEDIUM` / `LOW` / `NONE`). Forbidden-pattern matching is case-insensitive substring (transparent and auditable per paper §10.5); a crashing system produces a CRITICAL finding rather than a harness failure.

**Where it lives.** `pm_mcp_servers._redteam` — `PolicyRule`, `TestCase`, `RedTeamHarness`, `run_suite`.

**Operator-facing only.** Not invoked at request time; used by the platform team to validate that the L5 guardrails stay effective against new attack patterns and that L6 groundedness catches the hallucination scenarios the paper describes.

### L8 — Cryptographic Audit Trails

**What it does.** Every decision-producing handler in five MCP modules records a tamper-evident entry to a per-module hash chain. Each entry contains the SHA-256 hash of the entry before it; tampering with any past entry breaks every subsequent hash. With an HMAC signing key (set via `PDA_AUDIT_SIGNING_KEY`) the chain is also authenticatable.

**Where it lives.** `pm_data_tools.audit.AuditChain` (the generic primitive) and `pm_mcp_servers._audit` (the file-backed wrapper with per-module persistence). Chains live as JSONL files under `$PDA_AUDIT_DIR` (defaults to `~/.pm_data_tools/audit/`).

**Modules audited:**
- `pm_assure` — `assess_gate_readiness`, `scan_for_red_flags`, `log_override_decision`, `run_assurance_workflow`, `route_outputs_to_review`
- `pm_assumptions` — `score_assumption_confidence`, `detect_external_drift`, `generate_assumption_report`
- `pm_reporting` — every `generate_*` tool (recorded inside the L5 guardrail helper, so the chain captures the L5 verdict)
- `pm_knowledge` — `run_reference_class_check`, `generate_premortem_questions`
- `pm_simulation` — `run_schedule_simulation`

**Operator-facing.** Verify chain integrity by calling `pm_mcp_servers._audit.verify_chain("<module_name>")` from a Python shell. Returns `VerificationResult(status="VALID"|"TAMPERED"|"EMPTY", failed_at_index=...)`. Audit-chain failures during tool invocation are caught and swallowed so a disk-full or permissions error never breaks tool output — the operator sees the gap when verifying.

### L9 — Formal Verification

**What it does.** Small, critical kernels of the platform's logic are encoded in Z3 (an SMT solver) and **proven** rather than tested. The current property: the mapping from confidence score (0–100) to RAG (`RED` / `AMBER` / `GREEN`) is **monotone non-decreasing** with respect to the labels' semantic ordering — higher confidence never produces a worse RAG. This catches the common bug of writing labels in descending instead of ascending order: the verifier returns a concrete counterexample showing the inversion.

**Where it lives.** `agent_planning.verified.verify_rag_mapping` (Z3-backed) and `agent_planning.verified.evaluate_rag` (pure-Python reference implementation matching `pm_assumptions._rag` byte-for-byte).

**Operator-facing.** Run from a Python shell:
```python
from agent_planning.verified import verify_rag_mapping
result = verify_rag_mapping()  # uses pm-assumptions defaults
assert result.is_proven
```

---

## What this means for the consumer

### For a board / IPA reviewer

When you read a board exception report or gate review summary produced by the platform, the document has already been gated by L5 (no overclaim, no template leaks), annotated by L6 (ungrounded terms surfaced), and quality-scored by L3 (potential-hallucinations flag set or unset). You can see this directly in the document — the markdown footer carries:

```
*Groundedness: 0.87 (GROUNDED). Ungrounded terms: zeppelin, convoy*

<!-- _groundedness: {"verdict": "GROUNDED", "overall_score": 0.87, ...} -->
```

When the **Ungrounded terms** list is non-empty, those are the words in the AI's prose that have no support in the project data. They are the **focus of your challenge**: ask the team where those terms came from, what evidence supports them, and whether they belong in the document at all.

When the L5 layer rejects an output, you receive a structured error JSON rather than prose. This is by design — the platform is telling you "this output failed the deterministic gate; do not render it as content." Re-running the tool or escalating to expert review is the next step.

When a forecast (Monte Carlo schedule, IPA P80 estimate) carries a `_calibration.band`, that's a **coverage-guaranteed interval** — under reasonable assumptions, the true outcome lies in the band with probability `1 - alpha` (default 80%). Use the band for budget-setting, not the point estimate.

### For a developer integrating the platform

Every AI-authored response now has the same shape:

```jsonc
{
  // ... existing tool-specific fields ...

  "_groundedness": {  // L6
    "verdict": "GROUNDED",
    "overall_score": 0.87,
    "ungrounded_terms": ["zeppelin"],
    "per_source_citation_scores": {...},
    "provenance_trail": "..."
  },
  "_quality": {  // L3
    "verdict": "COMPUTED",
    "overall_score": 0.83,
    "components": {"coherence": 1.0, "relevance": 0.87, ...},
    "potential_hallucinations": false
  },
  "_calibration": {  // L4, where applicable
    "status": "COMPUTED",
    "band": {"lower": 95.2, "upper": 124.8, "half_width": 14.8},
    "alpha": 0.2,
    "coverage_pct": 80.0
  }
}
```

When L5 rejects, the response body is **replaced** with `{"error": "guardrail_rejected", "verdict": "REJECTED", "triggered": [...], "evaluations": [...]}` — detect the `"error"` key and route appropriately rather than trying to render the body.

You cannot opt out. The layers are always on. This is by design — the framework's guarantees only hold if every output passes through every layer.

### For an auditor

Five modules write tamper-evident JSONL audit logs at `~/.pm_data_tools/audit/<module>.jsonl`:

```python
from pm_mcp_servers._audit import verify_chain
for module in ("pm_assure", "pm_assumptions", "pm_reporting",
               "pm_knowledge", "pm_simulation"):
    result = verify_chain(module)
    print(f"{module}: {result.status} ({len(result.entries) if result.is_valid else '?'} entries)")
```

If `result.status == "TAMPERED"`, `result.failed_at_index` gives the first compromised entry. Each entry records the action name, the SHA-256 hash of the input, the SHA-256 hash of the output, the decision string, and module-specific metadata. Set `PDA_AUDIT_SIGNING_KEY` to an HMAC key for authenticated chains.

---

## How to verify the layers are working

Quick smoke tests after a deploy:

1. **L4 calibration tool surfaces.**
   ```
   evaluate_calibration —
     predictions: [0.9, 0.8, 0.7, 0.6]
     actuals:     [1,   1,   0,   1]
   ```
   Expect: `ece` in `[0, 1]`, `bins[]` length matching `n_bins`, `interpretation` string.

2. **L2 escalation router surfaces.**
   ```
   score_assumption_confidence — project_id: "SMOKE-001"
   route_outputs_to_review    — project_id: "SMOKE-001"
   ```
   Expect: `level` is one of the four enum values; `triggered_by_outliers` / `triggered_by_confidence` populated.

3. **L5/L6 attached to AI-authored tools.**
   ```
   generate_premortem_questions — gate: "ANY"
   ```
   Expect: response carries top-level `_groundedness` (verdict GROUNDED) and `_quality` (potential_hallucinations false). No L5 rejection on the bundled questions.

4. **L8 audit chain populated.**
   ```python
   from pm_mcp_servers._audit import verify_chain
   verify_chain("pm_assure").is_valid  # → True
   verify_chain("pm_simulation").is_valid  # → True after one simulation run
   ```

5. **L9 monotonicity proven.**
   ```python
   from agent_planning.verified import verify_rag_mapping
   verify_rag_mapping().is_proven  # → True
   ```

---

## References

- Newman, A. et al. *Verified Autonomy: A Nine-Layer Framework for AI Reliability in High-Stakes Decision Support.* May 2026. DOI: [10.5281/zenodo.19096229](https://doi.org/10.5281/zenodo.19096229).
- Internal: `docs/verified-autonomy-backlog-created.md` — mapping from layer to issue numbers.
- Internal: `~/.claude/plans/serene-sleeping-globe.md` — the plan that delivered the implementation.
- For tool-level parameter detail, see [`mcp-tools-reference.md`](mcp-tools-reference.md).
- For module-level practitioner guidance, see `docs/<module>-for-practitioners.md`.
