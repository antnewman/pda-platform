# Claude Integration Example

Use Claude Desktop with PM data through MCP.

## Overview

This example shows how to configure Claude Desktop to work with project management data using the pm-mcp-servers package.

## Setup

1. Install the server:
   ```bash
   pip install pm-mcp-servers
   ```

2. Add to Claude Desktop config (`claude_desktop_config.json`):
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

3. Restart Claude Desktop

## Example Queries

Once configured, you can ask Claude:

### Data Loading
- "Load the project from /projects/building.mpp"
- "Show me all tasks in the project"
- "What's on the critical path?"

### Validation
- "Validate this project against NISTA requirements"
- "Check for dependency cycles"
- "Are there any over-allocated resources?"

### Analysis
- "What are the highest-risk tasks?"
- "Predict the project completion date"
- "Show resource utilization by week"

### Conversion
- "Convert this project to NISTA format"
- "Export to Primavera P6"
- "Generate a Gantt chart"

## Advanced Usage

### Custom Analysis

```
"Analyze the schedule and identify:
1. Tasks likely to slip
2. Resource bottlenecks
3. Budget variances
4. Recommended mitigations"
```

### Batch Processing

```
"Load all projects from /projects/ and:
1. Validate each against NISTA
2. Generate compliance reports
3. Identify common issues"
```

## Configuration

The servers respect these environment variables:
- `PM_DATA_PATH`: Default project directory
- `PM_VALIDATE_STRICT`: Validation strictness (lenient/standard/strict)
- `PM_ANALYSE_CACHE`: Enable analysis result caching

## Troubleshooting

### Server not found
Ensure pm-mcp-servers is installed in your Python environment:
```bash
which pm-data-server
```

### Permission denied
Check file permissions on project files:
```bash
ls -la /path/to/project.mpp
```

### Validation errors
Review NISTA requirements:
```python
from pm_data_tools.validators import NISTAValidator
print(NISTAValidator.get_requirements())
```

## Authors

Members of the PDA Task Force

This integration supports the NISTA Programme and Project Data Standard trial.
