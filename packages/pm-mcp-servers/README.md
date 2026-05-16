# pm-mcp-servers

**126 MCP tools across 18 modules for UK government IPA Gate Review assurance.**

Part of the [PDA Platform](https://github.com/antnewman/pda-platform). Connects Claude and other AI assistants to schedule data, risk registers, earned value, benefits realisation, gate readiness, portfolio health, calibration evaluation, four-tier escalation routing, and pre-loaded IPA benchmark data. Implements the nine-layer **Verified Autonomy** framework (Newman et al., May 2026, DOI [10.5281/zenodo.19096229](https://doi.org/10.5281/zenodo.19096229)) end-to-end — deterministic guardrails, groundedness checking, tamper-evident audit chains, conformal prediction intervals, and formally-verified RAG monotonicity.

## Install

```bash
pip install pm-mcp-servers
```

Or install the meta-package which pulls in all dependencies:

```bash
pip install pda-platform
```

## Connect to Claude Desktop

Add the unified server to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pda-platform": {
      "command": "pda-platform-server",
      "args": [],
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-..."
      }
    }
  }
}
```

Or use the hosted SSE endpoint directly from Claude.ai:

```
https://pda-platform-i33p.onrender.com/sse
```

## Modules

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
| pm-assumptions | 8 | Assumption drift detection, confidence scoring, live external signals, AI executive reports |
| **Total** | **126** | |

## Verified Autonomy framework

Every AI-authored response now carries trust-signal annotations alongside the original output:

- `_groundedness` — token-overlap verdict + ungrounded terms + provenance trail (L6)
- `_quality` — quality score + `potential_hallucinations` boolean (L3)
- `_calibration` — conformal prediction interval (L4, Monte Carlo and reference-class)
- L5 deterministic guardrails gate every AI-authored prose output before it reaches the consumer
- L8 cryptographic audit chains record every decision-producing handler invocation

See [`docs/verified-autonomy-overview.md`](https://github.com/antnewman/pda-platform/blob/main/docs/verified-autonomy-overview.md) for the consumer-facing summary.

## Example questions Claude can answer

- "What is the current DCA rating for Project ALPHA and which gate conditions are outstanding?"
- "Run a reference class check on our £240m cost estimate — how does it compare to IPA benchmarks for IT projects, and what's the 80% confidence band?"
- "Which risks in the register are stale or accelerating? Generate pre-mortem questions for Gate 3."
- "Produce an earned value dashboard and interpret SPI and CPI trends."
- "Summarise the benefits realisation status and flag any benefits without an identified owner."
- "Evaluate the calibration of our last quarter's DCA forecasts against actual gate outcomes."
- "Should the assumption-confidence outputs for this project be routed to expert review?"

## Documentation

Full documentation, practitioner guides, persona guides, and prompt library at [github.com/antnewman/pda-platform/tree/main/docs](https://github.com/antnewman/pda-platform/tree/main/docs).

## UK Government Compliance

- **Transparency:** MIT open source, full code visibility
- **Accountability:** Evidence trails on all AI outputs with confidence scoring, groundedness verdicts, and tamper-evident audit chains
- **Human oversight:** All outputs are advisory; governance decisions require human review. Four-tier escalation router (`route_outputs_to_review`) surfaces which outputs need it
- **Safety:** Documented limitations and model cards for all AI-powered modules; deterministic L5 guardrails block overclaim and template-leak failure modes before they reach consumers

## Licence

MIT
