# pda-platform

**126 MCP tools across 18 modules for UK government IPA Gate Review assurance.**

Connects Claude and other AI assistants to the full IPA assurance framework: schedule analysis, risk registers, earned value, benefits realisation, gate readiness, change control, resource capacity, portfolio health, calibration evaluation, four-tier escalation routing, and pre-loaded IPA benchmark data. Implements the nine-layer **Verified Autonomy** framework (Newman et al., May 2026, DOI [10.5281/zenodo.19096229](https://doi.org/10.5281/zenodo.19096229)) end-to-end — deterministic guardrails, groundedness checking, tamper-evident audit chains, conformal prediction intervals, and formally-verified RAG monotonicity.

Production-deployed. Used by assurance practitioners, project managers, SROs, and portfolio managers on GMPP-registered programmes.

## Install

```bash
pip install pda-platform
```

This installs all four constituent packages:
- `agent-task-planning` — AI reliability framework (confidence scoring, outlier detection, calibration, escalation routing, formal verification kernel)
- `pm-data-tools` — parsers, validators, AssuranceStore (SQLite), generic cryptographic audit-chain primitive
- `pm-mcp-servers` — 126 MCP tools across 18 modules

## Connect to Claude Desktop

Add the unified server to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pda-platform": {
      "command": "pda-platform-server",
      "args": []
    }
  }
}
```

Or connect Claude.ai directly to the hosted SSE endpoint:

```
https://pda-platform-i33p.onrender.com/sse
```

## What's included

| Module | Tools | Capability |
|--------|------:|-----------|
| pm-data | 6 | Schedule loading, querying, format conversion |
| pm-analyse | 8 | Risk identification, forecasting, health scoring, narrative divergence, calibration evaluation |
| pm-validate | 4 | Structural, semantic, and NISTA validation |
| pm-nista | 5 | GMPP reporting and NISTA submission |
| pm-assure | 29 | P1–P14 assurance framework, cross-module red flag scanner, four-tier escalation routing |
| pm-brm | 12 | Benefits Realisation Management, outturn forecasting, trajectory tracking |
| pm-portfolio | 5 | Cross-project health rollup |
| pm-ev | 2 | Earned Value metrics and dashboard |
| pm-synthesis | 2 | AI executive health summaries |
| pm-risk | 9 | Risk register, heat map, velocity, stale-risk detection |
| pm-change | 5 | Change control log and pressure analysis |
| pm-resource | 5 | Resource loading, conflicts, and capacity |
| pm-financial | 5 | Budget baseline, actuals, and EAC forecasting |
| pm-knowledge | 8 | IPA benchmarks, reference class forecasting with conformal bands, pre-mortem |
| pm-simulation | 2 | Monte Carlo schedule simulation with conformal P50/P80 intervals |
| pm-lessons | 5 | AI lessons extraction from gate reviews/PIRs, systemic pattern analysis |
| pm-reporting | 6 | IPA-format gate review summaries, SRO dashboards, board exception reports, PIR templates, UDS export |
| pm-assumptions | 8 | Assumption drift detection, confidence scoring, live external signals, executive AI reports, cascade analysis, UDS dashboard |
| **Total** | **126** | One unified endpoint · One connection |

## Documentation

Full documentation, practitioner guides, and prompt library at [github.com/antnewman/pda-platform](https://github.com/antnewman/pda-platform/tree/main/docs).

See [`docs/verified-autonomy-overview.md`](https://github.com/antnewman/pda-platform/blob/main/docs/verified-autonomy-overview.md) for the nine-layer Verified Autonomy implementation summary.

## Licence

MIT
