# PDA Platform

**Open-source infrastructure for AI-enabled project delivery.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18133574.svg)](https://doi.org/10.5281/zenodo.18133574)
[![PyPI - pm-data-tools](https://img.shields.io/pypi/v/pm-data-tools)](https://pypi.org/project/pm-data-tools/)

## Acknowledgement

This project is a fork of https://github.com/PDA-Task-Force/pda-platform originally developed by the PDA Task Force. This fork is maintained independently by https://github.com/antnewman and is not affiliated with the original creators.

## Overview

The PDA Platform provides the data infrastructure needed for AI to improve project delivery. Built to support the NISTA Programme and Project Data Standard trial.

This work was made possible by:
- The **PDA Task Force White Paper** identifying AI implementation barriers in UK project delivery
- The **NISTA Programme and Project Data Standard** and its 12-month trial period

## The Problem

UK major infrastructure projects have a success rate of approximately 0.5%. The Government Major Projects Portfolio shows 84% of projects rated Amber or Red. AI has potential to help, but lacks standardised data infrastructure.

## The Solution

| Component | Description | Status |
|-----------|-------------|--------|
| **pm-data-tools** | Universal PM data parser (8 formats + NISTA) | v0.2.0 ✅ |
| **agent-task-planning** | AI reliability framework | v1.0.0 ✅ |
| **pm-mcp-servers** | MCP servers for Claude integration | Phase 1 ✅ |
| **Specifications** | Canonical model, benchmarks, synthetic data | Published ✅ |

## Quick Start

```bash
# Install the core library
pip install pm-data-tools

# Parse any PM file
from pm_data_tools import parse_project
project = parse_project("schedule.mpp")

# Validate NISTA compliance
from pm_data_tools.validators import NISTAValidator
result = NISTAValidator().validate(project)
print(f"Compliance: {result.compliance_score}%")
```

## Packages

### pm-data-tools
Universal parser and validator for project management data.
- **Formats**: MS Project, Primavera P6, Jira, Monday, Asana, Smartsheet, GMPP, NISTA
- **Features**: Parse, validate, convert, migrate
- **Install**: `pip install pm-data-tools`

### agent-task-planning
AI reliability framework with confidence extraction and outlier mining.
- **Features**: Multi-sample consensus, diverse alternative generation
- **Install**: `pip install agent-task-planning`

### pm-mcp-servers
MCP servers enabling Claude to interact with PM data.
- **Servers**: pm-data, pm-validate, pm-analyse, pm-benchmark
- **Install**: `pip install pm-mcp-servers`

## Specifications

All specifications are in the `specs/` directory:

| Spec | Description |
|------|-------------|
| [Canonical Model](specs/canonical-model/) | 12-entity JSON Schema for PM data |
| [MCP Servers](specs/mcp-servers/) | 4 servers, 19 tools for AI integration |
| [Benchmarks](specs/benchmarks/) | 5 evaluation tasks for PM AI |
| [Synthetic Data](specs/synthetic-data/) | Privacy-preserving data generation |

## Repository Structure

```
pda-platform/
├── specs/           # Technical specifications
├── packages/        # Python packages (each publishable to PyPI)
│   ├── pm-data-tools/
│   ├── agent-task-planning/
│   └── pm-mcp-servers/
├── docs/            # Documentation
└── examples/        # Usage examples
```

## License

MIT License - see [LICENSE](LICENSE)

## Authors

Members of the PDA Task Force

## Acknowledgments

- PDA Task Force White Paper on AI implementation barriers
- NISTA Programme and Project Data Standard
- The open-source community

---

*Built to support the NISTA trial and improve UK project delivery.*
