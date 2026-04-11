# pm-mcp-servers

**99 MCP tools across 14 modules for UK government IPA Gate Review assurance.**

Part of the [PDA Platform](https://github.com/antnewman/pda-platform). Connects Claude and other AI assistants to schedule data, risk registers, earned value, benefits realisation, gate readiness, portfolio health, and pre-loaded IPA benchmark data.

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

## Example questions Claude can answer

- "What is the current DCA rating for Project ALPHA and which gate conditions are outstanding?"
- "Run a reference class check on our £240m cost estimate — how does it compare to IPA benchmarks for IT projects?"
- "Which risks in the register are stale or accelerating? Generate pre-mortem questions for Gate 3."
- "Produce an earned value dashboard and interpret SPI and CPI trends."
- "Summarise the benefits realisation status and flag any benefits without an identified owner."

## Documentation

Full documentation, practitioner guides, persona guides, and prompt library at [github.com/antnewman/pda-platform/tree/main/docs](https://github.com/antnewman/pda-platform/tree/main/docs).

## UK Government Compliance

- **Transparency:** MIT open source, full code visibility
- **Accountability:** Evidence trails on all AI outputs with confidence scoring
- **Human oversight:** All outputs are advisory; governance decisions require human review
- **Safety:** Documented limitations and model cards for all AI-powered modules

## Licence

MIT
