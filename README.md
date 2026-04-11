# PDA Platform

**The Model Context Protocol platform purpose-built for UK government IPA Gate Review assurance.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI - pda-platform](https://img.shields.io/pypi/v/pda-platform)](https://pypi.org/project/pda-platform/)
[![PyPI - pm-mcp-servers](https://img.shields.io/pypi/v/pm-mcp-servers)](https://pypi.org/project/pm-mcp-servers/)
[![PyPI - pm-data-tools](https://img.shields.io/pypi/v/pm-data-tools)](https://pypi.org/project/pm-data-tools/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18133574.svg)](https://doi.org/10.5281/zenodo.18133574)

**116 tools · 17 modules · Production-deployed · Published on PyPI**

---

PDA Platform gives Claude and other MCP-compatible AI assistants **116 structured tools** to perform rigorous, evidence-based project delivery assurance aligned to IPA Gate Reviews (Gates 0–5), HM Treasury Green Book appraisal, and GMPP reporting standards. It is the only open-source MCP platform specifically designed for Senior Responsible Owners, Project Managers, Independent Assurance Reviewers, and Portfolio Managers working in UK government major project delivery.

Think of it as a **semantic layer for project data**: it ingests schedules from Primavera, MSP, Jira, and 5 other formats; normalises them into a consistent delivery model; pre-loads IPA benchmark statistics from five years of Annual Reports; and exposes everything through a structured API that AI can reason about directly — without parsing raw XML or making things up.

Connect Claude to the platform and ask it to conduct a full gate readiness assessment, scan across all delivery dimensions simultaneously for critical red flags, benchmark cost estimates against real IPA historical data, run Monte Carlo simulations, detect narrative optimism bias, or produce board-ready exception reports — all grounded in your project data, IPA methodology, and evidence from comparable government programmes.

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

## Start here: scan for red flags

The fastest way to get value from the platform is a single tool call:

```
scan_for_red_flags — project_id: "PROJ-001"
```

This queries risk registers, benefits status, gate conditions, cost performance, change pressure, and resource conflicts **simultaneously** and returns a prioritised CRITICAL / HIGH / MEDIUM alert list with evidence trails. One call replaces six separate queries. Use it at the start of every assurance session to focus attention where it matters most.

---

## What Claude can do with 116 tools

Once connected, Claude can answer questions like:

- *"Scan Project Alpha for red flags across all delivery dimensions and tell me what needs immediate SRO attention."*
- *"Run a full IPA Gate 3 readiness assessment and produce a Delivery Confidence Assessment."*
- *"Our cost estimate is £42m. Is that realistic for an IT programme of this scale compared to similar government projects?"*
- *"The project narrative says delivery is on track. Is the quantitative data consistent with that?"*
- *"Which risks on Project Beta are accelerating? Has the risk register been actively maintained?"*
- *"Run a Monte Carlo simulation and give me P50, P80, and P90 delivery dates."*
- *"Produce an IPA-format Gate Review Summary document ready for submission."*
- *"Extract lessons from this gate review report and identify patterns recurring across my portfolio."*
- *"Produce a board exception report — board language, escalation items only, no jargon."*
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
- **Cross-module red flag scanner** — `scan_for_red_flags` queries risk, benefits, gate conditions, cost, change, and resources simultaneously; returns prioritised CRITICAL/HIGH/MEDIUM alerts with evidence trails — the fastest way to identify where assurance attention is needed
- **Narrative divergence detection** — `detect_narrative_divergence` compares written project narrative against quantitative store data, classifying claims as SUPPORTED/CONTRADICTED/UNVERIFIABLE; directly targets optimism bias and groupthink
- **Monte Carlo schedule simulation** — probabilistic P50/P80/P90 delivery dates using PERT distributions, optionally calibrated against risk register likelihood/impact scores
- **AI lessons extraction** — `extract_lessons` parses gate review reports and PIRs to extract structured lessons (category, severity, root cause, recommendation); `get_systemic_patterns` identifies recurring issues across the portfolio corpus
- **IPA-format governance document generation** — gate review summaries, SRO dashboards, board exception reports, portfolio summaries, and PIR templates; pre-populated from store data, written in IPA language
- **Universal Dashboard Specification output** — `export_sro_dashboard_data` exports delivery metrics as static JSON for the UDS Renderer; visualise DCA rating, schedule confidence, cost variance, risks, and benefits in a browser dashboard
- **AI-powered narrative generation** — multi-sample consensus with confidence scoring, IPA-format executive summaries
- **Agent Readiness Maturity Model** — governance framework for AI deployment on major projects

---

## 17 MCP Modules

| Module | Tools | What it does |
|--------|------:|-------------|
| pm-data | 6 | Project loading, querying, format conversion across 8 PM data formats |
| pm-analyse | 7 | AI risk analysis, schedule forecasting, health assessment, narrative divergence detection |
| pm-validate | 4 | Structural, semantic, and NISTA compliance validation |
| pm-nista | 5 | GMPP quarterly reporting, NISTA integration, longitudinal compliance |
| pm-assure | 28 | Assurance lifecycle: artefact currency, gate readiness, ARMM, assumption drift, workflow engine, **cross-module red flag scanning** |
| pm-brm | 12 | Benefits Realisation Management: register, measurement, dependency network, drift, maturity, outturn forecasting, trajectory tracking |
| pm-portfolio | 5 | Cross-project portfolio aggregation, health rollup, systemic risk detection |
| pm-ev | 2 | Earned Value metrics (SPI/CPI/EAC/TCPI) and HTML S-curve dashboard |
| pm-synthesis | 2 | AI-generated executive health summaries and cross-project comparison |
| pm-risk | 9 | Risk register, heat map, mitigations, velocity tracking, stale register detection |
| pm-change | 5 | Change control log, impact analysis, change pressure analysis |
| pm-resource | 5 | Resource loading, conflict detection, portfolio capacity planning |
| pm-financial | 5 | Budget baseline, period actuals, EAC forecasting, spend profile |
| pm-knowledge | 8 | IPA benchmarks, failure patterns, guidance references, reference class checks, pre-mortem questions |
| pm-simulation | 2 | Monte Carlo schedule simulation with PERT distributions, P50/P80/P90 delivery dates |
| pm-lessons | 5 | AI extraction of lessons from gate reviews/PIRs, cross-project keyword search, systemic pattern analysis |
| pm-reporting | 6 | IPA-format gate review summaries, SRO dashboards, board exception reports, portfolio summaries, PIR templates, UDS export |
| **Total** | **116** | One unified endpoint · One connection |

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
│   ├── pm-mcp-servers/         17 MCP modules, 116 tools for AI integration
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
| [Lessons Learned](docs/lessons-for-practitioners.md) | pm-lessons |
| [Reporting](docs/reporting-for-practitioners.md) | pm-reporting |

### Technical references

| Document | Description |
|----------|-------------|
| [Architecture Overview](docs/architecture-overview.md) | System architecture and component interactions |
| [MCP Tools Reference](docs/mcp-tools-reference.md) | Parameter-level reference for all 116 tools |
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
cd packages/pm-mcp-servers && python -m pytest   # 68 tests, 116 tools
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
