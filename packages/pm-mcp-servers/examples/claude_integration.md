# Claude Desktop Integration Guide

Step-by-step guide to integrating PM MCP Servers with Claude Desktop.

## Prerequisites

- Claude Desktop app installed
- Python 3.10+ with pm-mcp-servers installed
- Project files to analyze

## Step 1: Install pm-mcp-servers

```bash
pip install pm-mcp-servers
```

Verify installation:
```bash
pm-data-server --version
```

## Step 2: Configure Claude Desktop

### Location of config file:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

### Add pm-data server:

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

### Add multiple servers:

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

## Step 3: Restart Claude Desktop

After updating the config file, restart Claude Desktop for changes to take effect.

## Step 4: Verify Connection

In Claude Desktop, you should see the MCP servers listed in the tools panel.

Ask Claude:
```
What MCP servers are available?
```

Claude should list pm-data (and others if configured).

## Step 5: Test Basic Operations

### Load a Project

**You:** "Load the Microsoft Project file at C:/Projects/Construction.mpp"

**Claude:** *Uses load_project tool*

"I've loaded the project 'Construction Project'. It contains 247 tasks, 18 resources, and 342 dependencies. The project runs from January 15, 2026 to December 31, 2027. Would you like me to analyze the critical path?"

### Query Tasks

**You:** "Show me all critical path tasks"

**Claude:** *Uses get_critical_path tool*

"The critical path contains 42 tasks totaling 456 days. Here are the key tasks:
1. Foundation Excavation (Jan 15 - Feb 2, 2026)
2. Structural Steel Erection (Feb 3 - Apr 15, 2026)
..."

### Analyze Dependencies

**You:** "What tasks depend on 'Foundation Excavation'?"

**Claude:** *Uses get_dependencies tool*

"Foundation Excavation has 5 successor tasks:
1. Foundation Formwork (FS link, 0 day lag)
2. Steel Delivery (FS link, 2 day lag)
..."

## Common Workflows

### 1. Project Health Check

```
You: Load project.mpp and give me a health summary
Claude: Uses load_project + get_project_summary
```

### 2. Risk Identification

```
You: Identify schedule risks in this project
Claude: Uses query_tasks + get_critical_path + get_dependencies
```

### 3. Format Conversion

```
You: Convert this P6 project to NISTA format
Claude: Uses load_project + convert_format
```

### 4. Critical Path Analysis

```
You: Show me the critical path and near-critical tasks
Claude: Uses get_critical_path with include_near_critical=true
```

## Troubleshooting

### Server not appearing in Claude

1. Check config file syntax (valid JSON)
2. Verify pm-data-server is in PATH
3. Restart Claude Desktop
4. Check Claude Desktop logs

### Tool calls failing

1. Ensure project file paths are absolute
2. Check file format compatibility
3. Verify Python dependencies installed

### Performance issues

- Large projects (>1000 tasks) may take longer to load
- Consider filtering queries with limit parameter
- Cache loaded projects in session

## Advanced Configuration

### Custom Python Environment

```json
{
  "mcpServers": {
    "pm-data": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "pm_mcp_servers.pm_data.server"]
    }
  }
}
```

### Debug Logging

Set environment variable:
```bash
export MCP_LOG_LEVEL=DEBUG
```

## Best Practices

1. **Load Once, Query Many:** Load the project once per session, then run multiple queries
2. **Use Filters:** Narrow results with filters to improve performance
3. **Session Persistence:** Projects remain loaded for the Claude session
4. **Error Handling:** Check for errors in responses before proceeding

## Example Conversation

```
You: Load C:/Projects/DataCenter.mpp

Claude: ✓ Loaded "Data Center Build" project
- 512 tasks
- 34 resources
- Critical path: 287 days

You: What are the top 5 longest tasks on the critical path?

Claude: [Uses query_tasks + sorting]
1. Electrical Installation (45 days)
2. HVAC System Install (38 days)
3. Server Rack Assembly (32 days)
...

You: Show me dependencies for "HVAC System Install"

Claude: [Uses get_dependencies]
Predecessors (3):
- Electrical Rough-In (FS, 0 days)
- Mechanical Ductwork (FS, 0 days)
...

You: Convert this to NISTA format for government reporting

Claude: [Uses convert_format]
✓ Converted to NISTA JSON format
✓ Includes DCA rating, WLC, benefits
Ready for submission
```

## Next Steps

- Try pm-validate server for compliance checking
- Use pm-analyse server for AI-powered insights
- Explore pm-benchmark for model evaluation

## Support

- GitHub Issues: [pm-mcp-servers/issues](https://github.com/PDA-Task-Force/pm-mcp-servers/issues)
- Documentation: [README.md](../README.md)
