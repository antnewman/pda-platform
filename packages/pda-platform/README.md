# pda-platform

**99 MCP tools for UK government IPA Gate Review assurance.**

Connects Claude and other AI assistants to the full IPA assurance framework: schedule analysis, risk registers, earned value, benefits realisation, gate readiness, change control, resource capacity, portfolio health, and pre-loaded IPA benchmark data.

Production-deployed. Used by assurance practitioners, project managers, SROs, and portfolio managers on GMPP-registered programmes.

## Install

```bash
pip install pda-platform
```

This installs all three constituent packages:
- `agent-task-planning` — AI reliability framework (confidence scoring, outlier detection)
- `pm-data-tools` — parsers, validators, AssuranceStore (SQLite)
- `pm-mcp-servers` — 99 MCP tools across 14 modules

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
| pm-analyse | 6 | Risk identification, forecasting, health scoring |
| pm-validate | 4 | Structural, semantic, and NISTA validation |
| pm-nista | 5 | GMPP reporting and NISTA submission |
| pm-assure | 27 | P1–P14 assurance framework |
| pm-brm | 10 | Benefits Realisation Management |
| pm-gate-readiness | 5 | IPA Gate Review readiness scoring |
| pm-portfolio | 5 | Cross-project health rollup |
| pm-ev | 2 | Earned Value metrics and dashboard |
| pm-synthesis | 2 | AI executive health summaries |
| pm-risk | 9 | Risk register, heat map, velocity, stale-risk detection |
| pm-change | 5 | Change control log and pressure analysis |
| pm-resource | 5 | Resource loading, conflicts, and capacity |
| pm-financial | 5 | Budget baseline, actuals, and EAC forecasting |
| pm-knowledge | 8 | IPA benchmarks, reference class forecasting, pre-mortem |
| **Total** | **99** | |

## Documentation

Full documentation, practitioner guides, and prompt library at [github.com/antnewman/pda-platform](https://github.com/antnewman/pda-platform/tree/main/docs).

## Licence

MIT
