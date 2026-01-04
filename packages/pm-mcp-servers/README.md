# PM MCP Servers

MCP servers for AI-enabled project management. Enables Claude to interact with PM data.

Part of the [PDA Platform](https://github.com/PDA-Task-Force/pda-platform).

<!-- mcp-name: io.github.antnewman/pm-data -->
<!-- mcp-name: io.github.antnewman/pm-validate -->
<!-- mcp-name: io.github.antnewman/pm-analyse -->

## Overview

PM MCP Servers provides Model Context Protocol (MCP) servers that enable Claude Desktop and other MCP clients to interact with project management data. Built to support the NISTA Programme and Project Data Standard trial.

## Features

- **pm-data-server**: Load, query, and manipulate PM data
- **pm-validate-server**: Validate PM data against standards
- **pm-analyse-server**: Analyze PM data for insights
- **pm-benchmark-server**: Benchmark PM AI capabilities

## Installation

```bash
pip install pm-mcp-servers
```

## Quick Start

### Configure Claude Desktop

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "pm-data": {
      "command": "pm-data-server",
      "args": []
    }
  }
}
```

### Example Queries

Once configured, you can ask Claude:

- "Load /projects/building.mpp and show the critical path"
- "What tasks are at risk of slipping?"
- "Convert this project to NISTA format"
- "Validate this project against NISTA requirements"

## Available Servers

### pm-data-server

Core server for PM data interaction.

**Tools:**
- `load_project`: Load a project file
- `query_tasks`: Query tasks by criteria
- `get_critical_path`: Find critical path
- `export_project`: Export to different formats

### pm-validate-server

Validation server for PM data quality.

**Tools:**
- `validate_nista`: Validate NISTA compliance
- `validate_structure`: Check structural integrity
- `check_dependencies`: Validate task dependencies

### pm-analyse-server

Analysis server for PM insights.

**Tools:**
- `analyze_risks`: Identify project risks
- `forecast_completion`: Predict completion dates
- `resource_utilization`: Analyze resource usage

### pm-benchmark-server

Benchmarking server for PM AI evaluation.

**Tools:**
- `run_benchmark`: Execute benchmark tasks
- `compare_results`: Compare AI performance

## Development

```bash
# Clone repository
git clone https://github.com/PDA-Task-Force/pda-platform.git
cd pda-platform/packages/pm-mcp-servers

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## Acknowledgments

Developed by members of the PDA Task Force.

This work was made possible by:
- The **PDA Task Force White Paper** identifying AI implementation barriers in UK project delivery
- The **NISTA Programme and Project Data Standard** and its 12-month trial period

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- [PDA Platform](https://github.com/PDA-Task-Force/pda-platform)
- [Documentation](https://github.com/PDA-Task-Force/pda-platform/tree/main/packages/pm-mcp-servers)
- [Issues](https://github.com/PDA-Task-Force/pda-platform/issues)
- [Model Context Protocol](https://modelcontextprotocol.io)
