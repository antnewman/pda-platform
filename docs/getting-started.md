# Getting Started with PDA Platform

Welcome to the PDA Platform! This guide will help you get up and running with the infrastructure for AI-enabled project delivery.

## Overview

The PDA Platform consists of three main packages:

- **pm-data-tools**: Universal parser and validator for project management data
- **agent-task-planning**: AI reliability framework with confidence extraction
- **pm-mcp-servers**: MCP servers for Claude integration with PM data

## Prerequisites

- **Python**: 3.10 or higher
- **pip**: Latest version recommended
- **Optional**: Claude Desktop (for MCP server integration)

## Installation

### Option 1: Install Individual Packages

```bash
# Install pm-data-tools (the core library)
pip install pm-data-tools

# Install agent-task-planning (AI framework)
pip install agent-task-planning

# Install pm-mcp-servers (Claude integration)
pip install pm-mcp-servers
```

### Option 2: Install from Source (Development)

```bash
# Clone the repository
git clone https://github.com/antnewman/pda-platform.git
cd pda-platform

# Install pm-data-tools
cd packages/pm-data-tools
pip install -e ".[dev]"
cd ../..

# Install agent-task-planning
cd packages/agent-task-planning
pip install -e ".[dev]"
cd ../..

# Install pm-mcp-servers
cd packages/pm-mcp-servers
pip install -e ".[dev]"
cd ../..
```

## Quick Start Examples

### 1. Parse a Project File

Parse MS Project, Primavera P6, or other PM formats:

```python
from pm_data_tools import parse_project

# Parse an MS Project file
project = parse_project("schedule.mpp")

print(f"Project: {project.name}")
print(f"Tasks: {len(project.tasks)}")
print(f"Resources: {len(project.resources)}")

# Access task data
for task in project.tasks[:5]:
    print(f"- {task.name} ({task.start_date} to {task.finish_date})")
```

### 2. Validate NISTA Compliance

Check if your project data meets NISTA standards:

```python
from pm_data_tools import parse_project
from pm_data_tools.validators import NISTAValidator

# Parse project
project = parse_project("schedule.mpp")

# Validate against NISTA
validator = NISTAValidator()
result = validator.validate(project)

print(f"Compliance Score: {result.compliance_score}%")
print(f"Status: {result.status}")

# Review issues
for issue in result.issues:
    print(f"- {issue.severity}: {issue.message}")
```

### 3. Convert Between Formats

Export to different PM formats:

```python
from pm_data_tools import parse_project
from pm_data_tools.exporters import export_project

# Parse MS Project file
project = parse_project("schedule.mpp")

# Export to Primavera P6 XML
export_project(project, "output.xml", format="p6_xml")

# Export to NISTA JSON
export_project(project, "output.json", format="nista")

# Export to canonical JSON
export_project(project, "canonical.json", format="canonical")
```

### 4. Use AI Task Planning

Generate reliable plans with confidence extraction:

```python
from agent_planning import TodoListPlanner
from agent_planning.providers import AnthropicProvider

# Set up provider
provider = AnthropicProvider(api_key="your-key")

# Create planner
planner = TodoListPlanner(provider=provider)

# Execute a task with planning
result = await planner.execute(
    "Research competitors and draft a market analysis report"
)

# Review the plan
for task in result.tasks:
    print(f"[{task.status}] {task.content}")

# Check confidence
print(f"Confidence: {result.confidence_score}")
```

### 5. Set Up MCP Servers for Claude

Enable Claude to work with PM data:

```bash
# Install MCP servers
pip install pm-mcp-servers

# Configure in Claude Desktop config
# Location: ~/Library/Application Support/Claude/claude_desktop_config.json (macOS)
# or %APPDATA%/Claude/claude_desktop_config.json (Windows)
```

Add to your Claude config:

```json
{
  "mcpServers": {
    "pm-data": {
      "command": "pm-data-server",
      "args": []
    },
    "pm-validate": {
      "command": "pm-validate-server",
      "args": []
    },
    "pm-analyse": {
      "command": "pm-analyse-server",
      "args": []
    }
  }
}
```

Now Claude can:
- Parse PM files: "Read my schedule.mpp file and summarize the critical path"
- Validate data: "Check this project for NISTA compliance"
- Analyze projects: "What are the schedule risks in this project?"

## Common Use Cases

### Use Case 1: Multi-Format Data Migration

Migrate from one PM tool to another:

```python
from pm_data_tools import parse_project
from pm_data_tools.exporters import export_project

# Read from MS Project
project = parse_project("legacy_schedule.mpp")

# Export to Primavera P6
export_project(project, "new_schedule.xml", format="p6_xml")

# Validate the migration
from pm_data_tools.validators import StructureValidator
validator = StructureValidator()
validation = validator.validate(project)

if validation.is_valid:
    print("Migration successful!")
else:
    print("Issues found:", validation.errors)
```

### Use Case 2: NISTA Compliance Reporting

Generate compliance reports for governance:

```python
from pm_data_tools import parse_project
from pm_data_tools.validators import NISTAValidator
from pm_data_tools.reporters import ComplianceReporter

# Parse project
project = parse_project("schedule.mpp")

# Validate
validator = NISTAValidator()
result = validator.validate(project)

# Generate report
reporter = ComplianceReporter()
report = reporter.generate(result, format="html")

# Save report
with open("compliance_report.html", "w") as f:
    f.write(report)
```

### Use Case 3: Batch Processing Multiple Projects

Process multiple PM files programmatically:

```python
from pathlib import Path
from pm_data_tools import parse_project
from pm_data_tools.validators import NISTAValidator

# Find all .mpp files
project_files = Path("projects/").glob("*.mpp")

# Process each
validator = NISTAValidator()
results = []

for file in project_files:
    project = parse_project(file)
    validation = validator.validate(project)

    results.append({
        "file": file.name,
        "compliance": validation.compliance_score,
        "status": validation.status
    })

# Summary
for result in results:
    print(f"{result['file']}: {result['compliance']}% ({result['status']})")
```

### Use Case 4: AI-Powered Risk Analysis

Use AI to analyze project risks:

```python
from pm_data_tools import parse_project
from agent_planning import create_agent
from agent_planning.providers import AnthropicProvider

# Parse project
project = parse_project("schedule.mpp")

# Set up AI agent
provider = AnthropicProvider(api_key="your-key")
agent = create_agent(provider)

# Analyze risks
prompt = f"""
Analyze this project schedule for risks:
- {len(project.tasks)} tasks
- Duration: {project.duration} days
- Critical path length: {len(project.critical_path)} tasks

Identify top 5 schedule risks and mitigation strategies.
"""

analysis = await agent.execute(prompt, context={"project": project})
print(analysis.result)
```

## Troubleshooting

### Issue: Import Error for pm-data-tools

**Problem:**
```
ImportError: No module named 'pm_data_tools'
```

**Solution:**
```bash
pip install pm-data-tools
# or for development
pip install -e "packages/pm-data-tools[dev]"
```

### Issue: LXML Installation Fails

**Problem:**
```
error: Microsoft Visual C++ 14.0 or greater is required
```

**Solution (Windows):**
1. Install Microsoft C++ Build Tools
2. Or use pre-built wheels:
   ```bash
   pip install --only-binary :all: lxml
   ```

**Solution (macOS):**
```bash
brew install libxml2 libxslt
pip install lxml
```

### Issue: MCP Server Not Appearing in Claude

**Problem:** MCP servers don't show up in Claude Desktop

**Solution:**
1. Verify installation: `which pm-data-server`
2. Check config file location (see paths above)
3. Restart Claude Desktop completely
4. Check Claude logs: `~/Library/Logs/Claude/` (macOS)

### Issue: NISTA Validation Fails

**Problem:** All projects fail NISTA validation

**Solution:**
```python
# Check what's missing
result = validator.validate(project)

for issue in result.issues:
    if issue.severity == "error":
        print(f"Required: {issue.field}")
        print(f"Issue: {issue.message}")
        print(f"Fix: {issue.suggestion}")
```

### Issue: Parse Error with .mpp Files

**Problem:**
```
ParseError: Unable to read MSPDI format
```

**Solution:**
1. Ensure file is MS Project 2007+ format (MSPDI XML)
2. For binary .mpp files, export as XML from MS Project first
3. Or use Project Server API for direct access

### Issue: Memory Error with Large Projects

**Problem:** Large projects (10,000+ tasks) cause memory issues

**Solution:**
```python
# Use streaming parser for large files
from pm_data_tools.parsers import StreamingParser

parser = StreamingParser()
for task in parser.parse_tasks("large_project.xml"):
    # Process task by task
    process_task(task)
```

## Next Steps

- **Architecture Overview**: See [architecture-overview.md](./architecture-overview.md) for system design
- **Barrier Mapping**: See [barrier-mapping.md](./barrier-mapping.md) for how this addresses AI barriers
- **Examples**: Check the `examples/` directory for more use cases
- **Specifications**: Review `specs/` for canonical model and MCP server specs
- **API Reference**: Full API docs coming soon

## Getting Help

- **Issues**: https://github.com/antnewman/pda-platform/issues
- **Discussions**: https://github.com/antnewman/pda-platform/discussions
- **Email**: Contact repository maintainer

## Contributing

See [CONTRIBUTING.md](../.github/CONTRIBUTING.md) for development workflow and guidelines.

---

**Built to support the NISTA trial and improve UK project delivery.**
