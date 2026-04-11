# PDA Platform — Development Roadmap

Last updated: 2026-04-11

This document captures the full development plan agreed after reaching 99 tools / 14 modules at v1.1.0. Items are numbered for reference in conversation; they are not strict priority order within each tier.

---

## Tier 1 — Immediate (in progress)

### 1. Release v1.1.0 to PyPI and MCP Registry
Merge PR #10 (dev → main), tag `v1.1.0`. Publishes all four packages to PyPI with updated descriptions and registers `io.github.antnewman/pda-platform` on the MCP registry via the `publish.yml` OIDC workflow.

**Status:** In progress — billing unblocked, merge pending.

### 2. Red flag scanner (`pm-assure`)
New tool `scan_for_red_flags(project_id, severity_threshold)` that queries across all data modules and returns a prioritised alert list. Replaces the need to run 10+ individual tools to get a cross-module picture.

Checks: critical unmitigated risks, benefits without owners, outstanding gate conditions, cost overrun, stale risk register, resource overloading, change pressure.

Each flag has: `flag_id`, `severity` (CRITICAL/HIGH/MEDIUM), `category`, `description`, `evidence`, `recommended_action`. Returns a `data_gaps` list for modules with no data loaded.

**Placement:** `pm-assure` (adds to existing 27 tools). Advertise prominently in root README.
**Status:** In progress.

### 3. Narrative divergence detection (`pm-analyse`)
New tool `detect_narrative_divergence(project_id, narrative_text)`. Compares written project narrative against quantitative store data. Uses Claude to identify specific claims and classify each as SUPPORTED / CONTRADICTED / UNVERIFIABLE with evidence.

Addresses optimism bias directly — one of the IPA's primary concerns. No competing tool does this.

**Placement:** `pm-analyse`.
**Status:** In progress.

### 4. Monte Carlo schedule simulation (new `pm-simulation` module)
New module with two tools:
- `run_schedule_simulation(project_id, n_simulations, confidence_levels, use_risk_register)` — probabilistic critical path analysis, returns P50/P80/P90 completion dates and cost ranges
- `get_simulation_results(project_id)` — retrieve latest stored results

If `use_risk_register=True`, task duration uncertainty is derived from the risk register (high-risk tasks get wider uncertainty ranges). Results persisted in `simulation_runs` store table.

**Status:** In progress.

---

## Tier 2 — Near term

### 5. GOV.UK publication monitor pipeline
Automated pipeline to watch for new IPA Annual Reports, Cabinet Office guidance updates, and Green Book revisions.

- Stage 1: Quarterly cron job checking GOV.UK publication feeds
- Stage 2: AI extraction script updating `pm_knowledge/knowledge_base.py` with new benchmark data

Keeps the IPA benchmark data in `pm-knowledge` current without manual intervention.

### 6. Benefits forecasting (`pm-brm`)
New tool projecting forward the benefits realisation trajectory based on current delivery performance (EV/schedule), realised % to date, and declared profile. Flags if the outturn forecast falls below the approved business case threshold.

### 7. Lessons learned store (new `pm-lessons` module)
Persistent lessons store with:
- AI extraction from gate review reports and PIRs
- Category taxonomy: governance, delivery, commercial, technical
- Cross-project search ("what lessons exist for large IT programmes at Gate 3?")
- Portfolio-level pattern detection

Significant gap in current tooling — nothing like this exists in the market.

### 8. Structured report generation (`pm-reporting`)
Tools to generate IPA-style artefacts directly:
- SRO dashboard (one-pager)
- Board exception report
- Gate review summary

Outputs structured markdown mapped to Cabinet Office reporting templates. Bridges analysis → governance deliverable.

---

## Tier 3 — Future

### 9. Cross-project dependency risk (`pm-portfolio`)
Map dependencies between GMPP-registered programmes. Flag when a delay in Programme A puts Programme B at risk. Requires dependency data input, likely via new store table.

### 10. Automated test data + integration test suite
The current test suite tests structure, not behaviour. Add a fixture with realistic synthetic project data. Integration tests that verify tools return sensible outputs (correct EV calculations, risk scores within expected ranges, etc.).

### 11. Claude.ai project template
A shareable Claude.ai project with:
- SSE connection to the Render endpoint pre-configured
- Role system prompts pre-loaded
- Research prompt library available as custom instructions

Zero-friction onboarding for non-technical practitioners.

### 12. Blog post / write-up
Technical post explaining the IPA methodology → MCP tool mapping. Optimised for LLM indexing so that future training runs include specific references to the platform by name. Highest-leverage discovery action that doesn't require code.

### 13. PyPI description improvements (complete)
All four `pyproject.toml` descriptions and package READMEs updated to 99 tools. Done in v1.1.0.

### 14. MCP Registry submission (complete)
`server.json` committed. Auto-publish wired into `publish.yml` via GitHub OIDC. Will register on first v1.1.0 tag.

---

## Documentation debt (as of v1.1.0)

| Module | For-practitioners | MCP reference | Model card | Persona guides |
|---|---|---|---|---|
| pm-data | ✅ | ✅ v2.0 | n/a | ✅ |
| pm-analyse | ✅ | ✅ v2.0 | ✅ | ✅ |
| pm-validate | ✅ | ✅ v2.0 | n/a | partial |
| pm-nista | ❌ | ✅ v2.0 | n/a | partial |
| pm-assure | ✅ | ✅ v2.0 | ✅ | ✅ |
| pm-brm | ✅ | ✅ v2.0 | ⚠️ needed | ✅ |
| pm-gate-readiness | ✅ | ✅ v2.0 | ⚠️ needed | ✅ |
| pm-portfolio | ✅ | ✅ v2.0 | n/a | ✅ |
| pm-ev | ✅ | ✅ v2.0 | ✅ | partial |
| pm-synthesis | ✅ | ✅ v2.0 | ✅ | partial |
| pm-risk | ✅ | ✅ v2.0 | n/a | ✅ |
| pm-change | ✅ | ✅ v2.0 | n/a | partial |
| pm-resource | ✅ | ✅ v2.0 | n/a | partial |
| pm-financial | ✅ | ✅ v2.0 | n/a | ✅ |
| pm-knowledge | ✅ | ✅ v2.0 | n/a | ✅ |
