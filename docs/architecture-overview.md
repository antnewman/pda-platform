# PDA Platform Architecture Overview

## Executive Summary

The PDA Platform provides a modular, interoperable infrastructure for AI-enabled project delivery. Built as a response to the PDA Task Force White Paper on AI implementation barriers, the platform consists of three independently deployable packages that work together to enable AI systems to understand, validate, and analyze project management data.

The platform exposes **126 MCP tools across 18 modules** and implements the nine-layer **Verified Autonomy** framework (Newman et al., May 2026, DOI [10.5281/zenodo.19096229](https://doi.org/10.5281/zenodo.19096229)) end-to-end — deterministic guardrails, groundedness checking, tamper-evident audit chains, conformal prediction intervals, four-tier escalation routing, and formally-verified RAG monotonicity. See [`verified-autonomy-overview.md`](verified-autonomy-overview.md) for the consumer-facing summary.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        PDA Platform                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │  pm-data-tools  │  │ agent-task-      │  │ pm-mcp-servers │ │
│  │                 │  │ planning         │  │                │ │
│  │  • Parsers      │  │                  │  │  • pm-data     │ │
│  │  • Validators   │◄─┤  • Confidence    │◄─┤  • pm-validate │ │
│  │  • Exporters    │  │  • Planning      │  │  • pm-analyse  │ │
│  │  • Canonical    │  │  • Providers     │  │  • pm-benchmark│ │
│  │    Model        │  │                  │  │  • pm-nista    │ │
│  │  • Assurance    │  │                  │  │  • pm-assure   │ │
│  └─────────────────┘  └──────────────────┘  └────────────────┘ │
│         ▲                      ▲                      ▲          │
└─────────┼──────────────────────┼──────────────────────┼──────────┘
          │                      │                      │
          │                      │                      │
┌─────────┴──────────┐  ┌────────┴────────┐   ┌────────┴─────────┐
│   Data Sources     │  │  AI Providers    │   │   AI Clients     │
│                    │  │                  │   │                  │
│ • MS Project       │  │ • Anthropic      │   │ • Claude Desktop │
│ • Primavera P6     │  │ • OpenAI         │   │ • Custom Apps    │
│ • Jira             │  │ • Google AI      │   │ • Web Interfaces │
│ • Monday.com       │  │ • Ollama         │   │                  │
│ • Asana            │  │                  │   │                  │
│ • Smartsheet       │  │                  │   │                  │
│ • GMPP             │  │                  │   │                  │
│ • NISTA            │  │                  │   │                  │
└────────────────────┘  └──────────────────┘   └──────────────────┘
```

## Component Overview

### 1. pm-data-tools (Core Data Layer)

**Purpose**: Universal parser, validator, and converter for project management data

**Key Components**:

#### Parsers
- **MSPDI Parser**: Microsoft Project 2007+ XML format
- **P6 Parser**: Primavera P6 XML/XER format
- **Jira Parser**: Jira API integration
- **SaaS Parsers**: Monday, Asana, Smartsheet
- **GMPP Parser**: Government Major Projects Portfolio format
- **NISTA Parser**: NISTA Programme and Project Data Standard

#### Canonical Model
The core data structure that all formats convert to/from:

```python
# 12 core entities
- Project        # Top-level container
- Task           # Work breakdown structure
- Resource       # People, equipment, materials
- Assignment     # Task-resource allocation
- Dependency     # Task relationships (FS, SS, FF, SF)
- Calendar       # Working time definitions
- Baseline       # Saved snapshots
- Risk           # Risk register
- Issue          # Issue log
- Change         # Change requests
- Cost           # Financial data
- Milestone      # Key deliverables
```

**Design Decisions**:
- **JSON Schema-based**: Validates all data against strict schema
- **Lossless conversion**: Preserves all source data during format conversion
- **Pydantic models**: Type-safe Python objects with validation
- **Extensible**: Custom fields preserved via metadata

#### Validators
- **Structure Validator**: Checks data integrity (required fields, valid references)
- **NISTA Validator**: Validates compliance with NISTA standard
- **Custom Validators**: Extensible validation framework

#### Exporters
- **Canonical JSON**: Platform-agnostic format
- **NISTA JSON**: Government-compliant export
- **P6 XML**: For Primavera P6 import
- **Custom formats**: Extensible exporter system

**Dependencies**:
```
lxml           # XML parsing
pydantic       # Data validation
python-dateutil # Date handling
httpx          # API clients
```

### 2. agent-task-planning (AI Reliability Layer)

**Purpose**: Framework for building reliable AI agents with confidence extraction

**Key Components**:

#### Confidence Extraction
Extracts confidence scores from LLM responses:

```python
# Multi-sample consensus
responses = await agent.generate_multiple(prompt, n=5)
confidence = extractor.calculate_consensus(responses)

# Returns:
{
    "consensus_score": 0.85,  # Agreement across samples
    "outliers": [...],         # Divergent responses
    "confidence_level": "high" # Categorical assessment
}
```

#### Task Planning
Manages complex multi-step workflows:

```python
# TodoList pattern
planner = TodoListPlanner(provider)
result = await planner.execute("Complex task")

# Tracks progress
for task in result.tasks:
    print(f"[{task.status}] {task.content}")
```

#### Provider Abstraction
Unified interface for multiple LLM providers:

```python
# Swap providers without code changes
provider = AnthropicProvider(api_key="...")
# or
provider = OpenAIProvider(api_key="...")
# or
provider = OllamaProvider(endpoint="...")

agent = create_agent(provider)
```

**Design Decisions**:
- **Provider-agnostic**: Works with any LLM via unified interface
- **Async-first**: Built on asyncio for concurrent operations
- **Structured outputs**: Pydantic models ensure type safety
- **Observable**: Structured logging for debugging

**Dependencies**:
```
pydantic       # Data models
httpx          # Async HTTP
structlog      # Structured logging
anthropic      # Optional: Claude integration
openai         # Optional: GPT integration
```

### 3. pm-mcp-servers (AI Integration Layer)

**Purpose**: MCP (Model Context Protocol) servers that enable AI assistants to interact with PM data

**Architecture**:

```
┌────────────────────────────────────────────────────────┐
│                   Claude Desktop                        │
└────────────────┬───────────────────────────────────────┘
                 │ MCP Protocol
         ┌───────┴────────┐
         │                │
    ┌────▼─────┐    ┌────▼─────┐
    │pm-data   │    │pm-validate│
    │server    │    │server     │
    └────┬─────┘    └────┬──────┘
         │               │
         │    ┌──────────▼─────┐
         │    │pm-analyse      │
         │    │server          │
         │    └──────────┬─────┘
         │               │
    ┌────▼───────────────▼─────┐
    │    pm-data-tools          │
    └──────────────────────────┘
```

#### Unified Server

The **`pda-platform-server`** is a single MCP endpoint that aggregates all 126 tools
from 18 modules. Each module exports a `registry.py` with its tool definitions and a
`dispatch()` function. The unified server imports and combines them at startup.

For remote access (e.g., from Claude.ai), **`pda-platform-remote`** wraps the unified
server in an SSE transport layer using Starlette and uvicorn.

#### Server Modules

| Module | Tools | Purpose |
|--------|-------|---------|
| **pm-data** | 6 | Project data loading, querying, critical path, conversion |
| **pm-analyse** | 6 | AI-powered risk identification, forecasting, health assessment |
| **pm-validate** | 4 | Structural, semantic, and NISTA compliance validation |
| **pm-nista** | 5 | GMPP reporting, AI narratives, NISTA API integration |
| **pm-assure** | 27 | Assurance lifecycle: P1–P12 + gate readiness (P14): assumptions, compliance, findings, scheduling, overrides, lessons, overhead, workflows, domain classification, dashboards, ARMM, gate readiness |
| **pm-brm** | 10 | Benefits Realisation Management (P13): benefit register, measurement tracking, dependency network, cascade impact, drift detection, maturity scoring |
| **Total** | **58** | |

Individual servers (`pm-data-server`, `pm-assure-server`, etc.) remain available for
use cases where only a subset of tools is needed.

**Design Decisions**:
- **Stateless**: Each request is independent
- **Tool-based**: Each capability is a discrete tool
- **Composable**: Tools can be chained in prompts
- **Secure**: File system access controlled

**Dependencies**:
```
mcp            # Model Context Protocol
pm-data-tools  # Core data operations
```

## Data Flow

### Example: Parse → Validate → Analyze

```
┌──────────────┐
│ schedule.mpp │ MS Project file
└──────┬───────┘
       │
       │ 1. Parse
       ▼
┌──────────────┐
│   Parser     │ pm-data-tools
└──────┬───────┘
       │
       │ 2. Convert to Canonical Model
       ▼
┌──────────────┐
│ Project      │ Canonical JSON Schema
│ - tasks[]    │
│ - resources[]│
│ - risks[]    │
└──────┬───────┘
       │
       ├──── 3a. Validate ────►┌──────────────┐
       │                        │NISTA Validator│
       │                        └──────┬───────┘
       │                               │
       │                               ▼
       │                        ┌──────────────┐
       │                        │Result        │
       │                        │- score: 85%  │
       │                        │- issues[]    │
       │                        └──────────────┘
       │
       └──── 3b. Analyze ─────►┌──────────────┐
                                │AI Agent      │
                                │(via MCP)     │
                                └──────┬───────┘
                                       │
                                       ▼
                                ┌──────────────┐
                                │Insights      │
                                │- critical_path│
                                │- risks       │
                                │- recommendations│
                                └──────────────┘
```

## Integration Patterns

### Pattern 1: Direct Python Integration

```python
from pm_data_tools import parse_project
from pm_data_tools.validators import NISTAValidator

# Parse
project = parse_project("schedule.mpp")

# Validate
validator = NISTAValidator()
result = validator.validate(project)

# Use results
if result.compliance_score > 80:
    proceed_with_project(project)
```

### Pattern 2: MCP Server Integration (AI-Driven)

```
User → Claude: "Analyze my project schedule for risks"
        ↓
Claude → pm-data-server: read_project("schedule.mpp")
        ↓
pm-data-server → pm-data-tools: parse_project()
        ↓
pm-data-tools → Returns: Canonical Project
        ↓
Claude → pm-analyse-server: identify_risks(project)
        ↓
pm-analyse-server → Returns: Risk analysis
        ↓
Claude → User: "Here are the top 5 risks..."
```

### Pattern 3: Hybrid (Python + AI)

```python
from pm_data_tools import parse_project
from agent_planning import create_agent
from agent_planning.providers import AnthropicProvider

# Parse with pm-data-tools
project = parse_project("schedule.mpp")

# Analyze with AI
provider = AnthropicProvider(api_key="...")
agent = create_agent(provider)

# AI gets structured data as context
analysis = await agent.execute(
    "What are the schedule risks?",
    context={"project": project.model_dump()}
)
```

## Deployment Models

### Model 1: Local Development

```bash
pip install pm-data-tools agent-task-planning pm-mcp-servers

# Use directly in Python
python my_script.py

# Or via MCP servers for Claude
# (configured in Claude Desktop)
```

### Model 2: API Service (Future)

```
┌────────────┐
│   Client   │
└─────┬──────┘
      │ HTTPS
      ▼
┌────────────┐
│ FastAPI    │ REST endpoints
│ Service    │
└─────┬──────┘
      │
      ▼
┌────────────┐
│ pm-data-   │
│ tools      │
└────────────┘
```

### Model 3: Embedded (Future)

```
┌──────────────────────┐
│  Project Management  │
│  Tool (Internal)     │
│  ┌────────────────┐  │
│  │ pm-data-tools  │  │ Embedded as library
│  └────────────────┘  │
└──────────────────────┘
```

## Performance Characteristics

### Parsing Performance

| File Type | Size | Parse Time | Memory |
|-----------|------|------------|--------|
| MS Project (MSPDI) | 100 tasks | ~50ms | ~5MB |
| MS Project (MSPDI) | 1,000 tasks | ~500ms | ~50MB |
| MS Project (MSPDI) | 10,000 tasks | ~5s | ~500MB |
| P6 XML | 1,000 activities | ~300ms | ~30MB |
| Jira API | 1,000 issues | ~2s | ~20MB |

### Validation Performance

| Validator | 100 tasks | 1,000 tasks | 10,000 tasks |
|-----------|-----------|-------------|--------------|
| Structure | ~10ms | ~100ms | ~1s |
| NISTA | ~50ms | ~500ms | ~5s |

### MCP Server Response Times

| Operation | Typical Response |
|-----------|------------------|
| read_project | 50-500ms |
| validate_nista | 100ms-5s |
| analyze_schedule | 1-10s |

## Security Considerations

### Data Privacy
- **No data transmission**: All processing happens locally
- **No external APIs**: Unless explicitly configured (e.g., Jira)
- **File system isolation**: MCP servers only access specified directories

### API Keys
- **Environment variables**: Never hard-coded
- **Scoped access**: Each provider has minimal required permissions
- **Key rotation**: Supported via configuration

### Validation
- **Schema enforcement**: All data validated against JSON Schema
- **Input sanitization**: Protection against injection attacks
- **File type verification**: Only supported formats accepted

## Extensibility Points

### 1. Custom Parsers

```python
from pm_data_tools.parsers import BaseParser

class CustomParser(BaseParser):
    def parse(self, file_path: str) -> Project:
        # Custom parsing logic
        return project
```

### 2. Custom Validators

```python
from pm_data_tools.validators import BaseValidator

class CustomValidator(BaseValidator):
    def validate(self, project: Project) -> ValidationResult:
        # Custom validation logic
        return result
```

### 3. Custom MCP Tools

```python
from pm_mcp_servers import create_tool

@create_tool
async def custom_analysis(project_path: str) -> dict:
    """Custom project analysis tool"""
    # Implementation
    return results
```

### 4. Custom AI Providers

```python
from agent_planning.providers import BaseProvider

class CustomProvider(BaseProvider):
    async def generate(self, prompt: str) -> str:
        # Custom LLM integration
        return response
```

## Testing Strategy

### Unit Tests
- **Coverage target**: 100% (enforced in CI)
- **Framework**: pytest
- **Mock data**: Synthetic projects for consistent testing

### Integration Tests
- **Real data**: Sample files from each supported format
- **Round-trip tests**: Parse → Export → Parse (verify lossless)
- **Validation tests**: Known-good and known-bad samples

### End-to-End Tests
- **MCP integration**: Full Claude Desktop workflow
- **Multi-package**: Cross-package integration scenarios
- **Performance**: Benchmark tests for regression detection

## Future Architecture Considerations

### Planned Enhancements

1. **Streaming Parser**: For very large files (100k+ tasks)
2. **Incremental Validation**: Validate changes, not full project
3. **Caching Layer**: Redis/disk cache for parsed projects
4. **Distributed Processing**: Multi-process parsing for speed
5. **GraphQL API**: Alternative to REST for flexible queries
6. **Real-time Sync**: Live updates from PM tools (webhooks)

### Scalability Path

```
Current: Single-process, local files
    ↓
Phase 2: Multi-process, shared cache
    ↓
Phase 3: Distributed workers, object storage
    ↓
Phase 4: Cloud-native, auto-scaling
```

## Related Documentation

- **Getting Started**: [getting-started.md](./getting-started.md)
- **Barrier Mapping**: [barrier-mapping.md](./barrier-mapping.md)
- **Canonical Model Spec**: [../specs/canonical-model/](../specs/canonical-model/)
- **MCP Servers Spec**: [../specs/mcp-servers/](../specs/mcp-servers/)

---

**Architecture Version**: 1.1
**Last Updated**: March 2026
**Maintained by**: maliah1010 ([github.com/maliah1010](https://github.com/maliah1010))
