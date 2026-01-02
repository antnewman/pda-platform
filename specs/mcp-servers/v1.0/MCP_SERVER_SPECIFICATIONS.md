# MCP Server Specifications v1.0

Model Context Protocol servers for AI-enabled project management.

## Overview

This specification defines four MCP servers that enable AI assistants like Claude to interact with project management data. Developed by members of the PDA Task Force to support the NISTA Programme and Project Data Standard trial.

## Servers

### 1. pm-data-server

Core server for PM data interaction.

**Tools:**
- `load_project(path: str)` - Load a project file
- `list_tasks(filter: Optional[Dict])` - List tasks with optional filtering
- `get_task(task_id: str)` - Get task details
- `update_task(task_id: str, updates: Dict)` - Update task fields
- `get_critical_path()` - Calculate critical path
- `export_project(format: str, path: str)` - Export to different format

**Resources:**
- `project://current` - Currently loaded project
- `task://{task_id}` - Individual task data

### 2. pm-validate-server

Validation server for PM data quality.

**Tools:**
- `validate_nista(strictness: str)` - Validate NISTA compliance
- `validate_structure()` - Check structural integrity
- `check_dependencies()` - Validate dependency graph
- `verify_resources()` - Check resource allocation
- `audit_data_quality()` - Comprehensive quality report

**Resources:**
- `validation://report` - Latest validation results

### 3. pm-analyse-server

Analysis server for PM insights.

**Tools:**
- `analyze_schedule()` - Schedule analysis and metrics
- `identify_risks()` - Risk detection from data patterns
- `forecast_completion(method: str)` - Predict completion dates
- `resource_utilization()` - Resource usage analysis
- `cost_analysis()` - Budget and cost metrics
- `compare_to_baseline()` - Variance analysis

**Resources:**
- `analysis://schedule` - Schedule analysis results
- `analysis://risks` - Identified risks

### 4. pm-benchmark-server

Benchmarking server for PM AI evaluation.

**Tools:**
- `run_task_extraction()` - Extract tasks from natural language
- `run_dependency_inference()` - Infer task relationships
- `run_risk_identification()` - Identify project risks
- `run_schedule_optimization()` - Optimize schedule
- `run_nista_compliance()` - Test NISTA compliance validation

**Resources:**
- `benchmark://results` - Benchmark execution results

## Data Format

All servers use the Canonical Model (see `../canonical-model/v1.0/`) for representing PM data.

## Integration

### Claude Desktop

Add to `claude_desktop_config.json`:

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
    },
    "pm-benchmark": {
      "command": "pm-benchmark-server",
      "args": []
    }
  }
}
```

## Error Handling

All tools follow standard MCP error responses:

- `INVALID_REQUEST` - Malformed request
- `FILE_NOT_FOUND` - Project file not found
- `VALIDATION_ERROR` - Data validation failure
- `PROCESSING_ERROR` - Server-side processing error

## Security

- Servers operate with user-level file permissions
- No network access required
- All data processing is local

## Authors

Members of the PDA Task Force

## Acknowledgments

This specification supports the NISTA Programme and Project Data Standard trial and addresses AI implementation barriers identified in the PDA Task Force White Paper.

## Version History

- **1.0.0** (2026-01-02) - Initial specification
