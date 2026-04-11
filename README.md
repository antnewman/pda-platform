# PDA Platform

**The Model Context Protocol platform purpose-built for UK government IPA Gate Review assurance.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI - pda-platform](https://img.shields.io/pypi/v/pda-platform)](https://pypi.org/project/pda-platform/)
[![PyPI - pm-mcp-servers](https://img.shields.io/pypi/v/pm-mcp-servers)](https://pypi.org/project/pm-mcp-servers/)
[![PyPI - pm-data-tools](https://img.shields.io/pypi/v/pm-data-tools)](https://pypi.org/project/pm-data-tools/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18133574.svg)](https://doi.org/10.5281/zenodo.18133574)

**99 tools · 14 modules · Production-deployed · Published on PyPI**

---

PDA Platform gives Claude and other MCP-compatible AI assistants the tools to perform rigorous, evidence-based project delivery assurance aligned to IPA Gate Reviews (Gates 0–5), HM Treasury Green Book appraisal, and GMPP reporting standards. It is the only open-source MCP platform specifically designed for Senior Responsible Owners, Project Managers, Independent Assurance Reviewers, and Portfolio Managers working in UK government major project delivery.

Connect Claude to the platform and ask it to conduct a full gate readiness assessment, generate a Delivery Confidence Assessment, run an Earned Value analysis, detect stale risk registers, benchmark cost estimates against IPA historical data, or produce board-ready health summaries — all grounded in real project data, IPA methodology, and pre-loaded government benchmark statistics.

**Live demo:** `https://pda-platform-i33p.onrender.com/sse` — connect any MCP client in under 60 seconds, no installation required.

---

## Who is this for?

| Role | What the platform does for you |
|------|-------------------------------|
| **Senior Responsible Owner** | Board-ready health summaries, delivery confidence assessments, benefits realisation status, gate readiness position — in plain English, grounded in data |
| **Project Manager** | Schedule health, critical path analysis, Earned Value (SPI/CPI/EAC), risk velocity tracking, resource conflict detection, change pressure analysis |
| **Independent Assurance Reviewer** | Full IPA Gate Review workflow (13 steps), confidence divergence detection, ARMM maturity assessment, pre-mortem question generation, reference class benchmarking |
| **Portfolio Manager** | Cross-project health rollup, aggregate benefit confidence, systemic risk detection, portfolio coherence scoring, intervention prioritisation |

---

## Connect in 60 seconds

**No installation — remote connection:**

Connect any MCP-compatible client directly to the hosted endpoint:
```
https://pda-platform-i33p.onrender.com/sse
```

**Claude Desktop — local install:**
```bash
pip install pda-platform
```

Add to `claude_desktop_config.json`:
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

**Deploy your own:**

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/antnewman/pda-platform)

See the full **[Connection Guide](docs/connection-guide.md)** for Claude.ai, Claude Desktop, ChatGPT, Gemini, and other MCP clients.

---

## What Claude can do with 99 tools

Once connected, Claude can answer questions like:

- *"Run a full IPA Gate 3 readiness assessment for Project Alpha and produce a Delivery Confidence Assessment."*
- *"Our cost estimate is £42m. Is that realistic for an IT programme of this scale compared to similar government projects?"*
- *"Which risks on Project Beta are accelerating? Has the risk register been actively maintained?"*
- *"Produce a board-ready summary of portfolio health for the investment committee."*
- *"Generate pre-mortem challenge questions for the Gate 3 review panel."*
- *"Run an Earned Value analysis and tell me if this project's cost trajectory is sustainable."*
- *"Which of my six projects needs the most urgent assurance intervention this quarter?"*

---

## Key Features

- **IPA Gate Review alignment** — Gates 0–5 and PAR, 8-dimension DCA scoring with gate-specific weighting, conditions vs recommendations distinction
- **HMT Green Book compliance** — benefits management, optimism bias detection, reference class forecasting against IPA historical benchmarks
- **GMPP-ready reporting** — RAG ratings, NISTA compliance tracking, quarterly data returns
- **Production-grade risk intelligence** — risk velocity tracking, stale register detection, quantified risk exposure
- **Earned Value Management** — SPI, CPI, EAC, TCPI, VAC with HTML dashboard generation
- **Benefits Realisation Management** — P3M3-aligned maturity scoring, dependency network, drift detection, Green Book narrative generation
- **Portfolio intelligence** — cross-project health rollup, aggregate DCA distribution, systemic risk detection
- **Pre-loaded IPA knowledge base** — benchmark statistics from IPA Annual Reports 2019–2024, 8 evidence-based failure patterns, guidance references (Green Book, Cabinet Office Controls, GovS002)
- **Pre-mortem question generation** — structured challenge questions for Gates 0–5, targeting optimism bias, groupthink, and known cognitive failure modes
- **ARMM maturity assessment** — 251-criterion AI readiness assessment across 4 dimensions and 28 topics
- **8 schedule data format parsers** — MSPDI, Primavera P6, Jira, Monday, Asana, Smartsheet, GMPP, NISTA
- **AI-powered narrative generation** — multi-sample consensus with confidence scoring, IPA-format executive summaries
- **Agent Readiness Maturity Model** — governance framework for AI deployment on major projects

---

## 14 MCP Modules

| Module | Tools | What it does |
|--------|------:|-------------|
| pm-data | 6 | Project loading, querying, format conversion across 8 PM data formats |
| pm-analyse | 6 | AI risk analysis, schedule forecasting, health assessment, baseline comparison |
| pm-validate | 4 | Structural, semantic, and NISTA compliance validation |
| pm-nista | 5 | GMPP quarterly reporting, NISTA integration, longitudinal compliance |
| pm-assure | 27 | Assurance lifecycle: artefact currency, gate readiness, ARMM, assumption drift, workflow engine |
| pm-brm | 10 | Benefits Realisation Management: register, measurement, dependency network, drift, maturity |
| pm-portfolio | 5 | Cross-project portfolio aggregation, health rollup, systemic risk detection |
| pm-ev | 2 | Earned Value metrics (SPI/CPI/EAC/TCPI) and HTML S-curve dashboard |
| pm-synthesis | 2 | AI-generated executive health summaries and cross-project comparison |
| pm-risk | 9 | Risk register, heat map, mitigations, velocity tracking, stale register detection |
| pm-change | 5 | Change control log, impact analysis, change pressure analysis |
| pm-resource | 5 | Resource loading, conflict detection, portfolio capacity planning |
| pm-financial | 5 | Budget baseline, period actuals, EAC forecasting, spend profile |
| pm-knowledge | 8 | IPA benchmarks, failure patterns, guidance references, reference class checks, pre-mortem questions |
| **Total** | **99** | One unified endpoint · One connection |

---

## Prompt Library

The platform ships with a curated prompt library (`docs/prompts/`) for immediate use:

- **IPA Gate Review methodology prompt** — system prompt encoding Gates 0–5, DCA rating scale, 8 assessment dimensions, conditions vs recommendations, gate-specific artefact requirements
- **Role-based system prompts** — calibrated for SRO, Project Manager, Independent Assurance Reviewer, and Portfolio Manager
- **Research prompts** — three structured multi-step analytical workflows: Full Gate Readiness Analysis (13 steps), Benefits Realisation Review (9 steps, Green Book-aligned), Schedule and Cost Health Review (11 steps with Earned Value)

---

## Architecture

```
PDA Platform
├── packages/
│   ├── pm-data-tools/          Core library: parsers, validators, AssuranceStore (SQLite)
│   ├── pda-platform/           Meta-package: pip install pda-platform installs everything
│   ├── pm-mcp-servers/         14 MCP modules, 99 tools for AI integration
│   └── agent-task-planning/    AI reliability: confidence extraction, outlier mining
├── docs/                       Practitioner guides, prompt library, technical references
├── specs/                      Canonical data model, benchmarks, synthetic data specs
├── examples/                   Usage examples and integration guides
└── dashboards/                 Monitoring and reporting dashboards
```

---

## Documentation

### Practitioner guides (by role)

| Guide | Audience |
|-------|----------|
| [SRO Guide](docs/guides/sro-guide.md) | Senior Responsible Owners |
| [Project Manager Guide](docs/guides/pm-guide.md) | Project Managers |
| [Assurance Reviewer Guide](docs/guides/assurance-reviewer-guide.md) | Independent Assurance Reviewers |
| [Portfolio Manager Guide](docs/guides/portfolio-manager-guide.md) | Portfolio Managers |

### Module practitioner guides

| Guide | Module |
|-------|--------|
| [Assurance](docs/assurance-for-practitioners.md) | pm-assure |
| [Gate Readiness](docs/gate-readiness-for-practitioners.md) | pm-assure |
| [Benefits Realisation](docs/brm-for-practitioners.md) | pm-brm |
| [Risk](docs/risk-for-practitioners.md) | pm-risk |
| [Financial](docs/financial-for-practitioners.md) | pm-financial |
| [Resource](docs/resource-for-practitioners.md) | pm-resource |
| [Change Control](docs/change-for-practitioners.md) | pm-change |
| [Portfolio](docs/portfolio-for-practitioners.md) | pm-portfolio |
| [Earned Value](docs/ev-for-practitioners.md) | pm-ev |
| [AI Synthesis](docs/synthesis-for-practitioners.md) | pm-synthesis |
| [Knowledge Base](docs/knowledge-for-practitioners.md) | pm-knowledge |
| [Data](docs/data-for-practitioners.md) | pm-data |
| [Analysis](docs/analyse-for-practitioners.md) | pm-analyse |
| [Validation](docs/validate-for-practitioners.md) | pm-validate |

### Technical references

| Document | Description |
|----------|-------------|
| [Architecture Overview](docs/architecture-overview.md) | System architecture and component interactions |
| [MCP Tools Reference](docs/mcp-tools-reference.md) | Parameter-level reference for all 99 tools |
| [Connection Guide](docs/connection-guide.md) | Connect Claude.ai, Claude Desktop, ChatGPT, Gemini |
| [Getting Started](docs/getting-started.md) | Installation, configuration, and first steps |
| [Data Model Reference](docs/data-model-reference.md) | Canonical data model and entity relationships |
| [Database Schema](docs/database-schema.md) | SQLite AssuranceStore schema |

### Prompt library

| Prompt | Purpose |
|--------|---------|
| [IPA Gate Review Methodology](docs/prompts/ipa-gate-review-methodology.md) | System prompt encoding full IPA Gate Review framework |
| [Role System Prompts](docs/prompts/role-system-prompts.md) | SRO, PM, Assurance Reviewer, Portfolio Manager |
| [Research Prompts](docs/prompts/research-prompts.md) | Gate readiness, benefits review, schedule and cost health |

---

## Development Setup

**Prerequisites:** Python 3.11+

```bash
# Install everything
pip install pda-platform

# Or install packages individually for development
pip install -e "packages/agent-task-planning[mining,anthropic]"
pip install -e packages/pm-data-tools
pip install -e packages/pm-mcp-servers
```

**Run tests:**
```bash
cd packages/pm-mcp-servers && python -m pytest   # 48 tests, 99 tools
cd packages/pm-data-tools && python -m pytest
```

**Run locally:**
```bash
pda-platform-server        # stdio transport (Claude Desktop)
pda-platform-remote        # SSE transport (Claude.ai, remote clients)
```

---

## Citation

```
Newman, A. (2026) From Policy to Practice: An Open Framework for AI-Ready Project Delivery.
London: Tortoise AI. DOI: https://doi.org/10.5281/zenodo.18711384
```

---

## License

MIT — see [LICENSE](LICENSE).

---

## Authors and Contributors

**Maintained by:** Ant Newman ([github.com/antnewman](https://github.com/antnewman)), CEO and Co-Founder, Tortoise AI

**Contributors:**
- [Lawrence Rowland](https://github.com/lawrencerowland) — requirements and conceptual design for confidence extraction and outlier mining in `agent-task-planning`
- [Malia Hosseini](https://github.com/maliah1010) — implementation of the outlier mining module

---

## Acknowledgement

This project builds on [github.com/PDA-Task-Force/pda-platform](https://github.com/PDA-Task-Force/pda-platform), originally developed by the PDA Task Force. This fork is maintained independently by [github.com/antnewman](https://github.com/antnewman) and is not affiliated with the original creators.

NISTA compliance scores are indicative assessments against the trial standard and do not constitute formal certification. Provided as-is under the MIT licence.
