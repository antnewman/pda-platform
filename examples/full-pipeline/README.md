# Full Pipeline Example

Complete workflow: Load → Validate → Analyze → Convert

## Overview

This example demonstrates a full pipeline for processing project management data using all PDA Platform packages.

## Pipeline Steps

### 1. Load Project Data

```python
from pm_data_tools import parse_project

# Load from any supported format
project = parse_project("my_project.mpp")

print(f"Loaded: {project.name}")
print(f"Tasks: {len(project.tasks)}")
print(f"Resources: {len(project.resources)}")
```

### 2. Validate Against NISTA

```python
from pm_data_tools.validators import NISTAValidator

validator = NISTAValidator(strictness="standard")
result = validator.validate(project)

if not result.compliant:
    print("NISTA Compliance Issues:")
    for issue in result.issues:
        print(f"  - {issue.message}")
```

### 3. Analyze with AI

```python
from agent_planning import AgentPlanner

planner = AgentPlanner(model="claude-3-opus")

# Identify risks
risks = planner.identify_risks(project)
print(f"Identified {len(risks)} risks")

# Generate mitigation plan
for risk in risks:
    print(f"Risk: {risk.description}")
    print(f"  Probability: {risk.probability:.0%}")
    print(f"  Impact: {risk.impact:.0%}")
    print(f"  Mitigation: {risk.mitigation}")
```

### 4. Optimize Schedule

```python
from agent_planning import ScheduleOptimizer

optimizer = ScheduleOptimizer()

# Optimize for minimum duration
optimized = optimizer.optimize(
    project,
    objective="duration",
    constraints=["resource_limits", "dependencies"]
)

print(f"Original duration: {project.duration_days} days")
print(f"Optimized duration: {optimized.duration_days} days")
print(f"Improvement: {optimized.duration_days - project.duration_days} days")
```

### 5. Convert to NISTA Format

```python
from pm_data_tools.converters import convert_to_nista

# Convert optimized project to NISTA
nista_project = convert_to_nista(optimized)

# Export
nista_project.save("optimized_project_nista.json")
```

### 6. Validate Final Output

```python
# Re-validate after optimization
final_result = validator.validate(nista_project)

print(f"Final compliance: {final_result.compliance_score}%")
print(f"Ready for submission: {final_result.compliant}")
```

## Complete Script

```python
#!/usr/bin/env python3
"""
Full PDA Platform pipeline example.

Usage: python pipeline.py input.mpp output_nista.json
"""

import sys
from pm_data_tools import parse_project
from pm_data_tools.validators import NISTAValidator
from pm_data_tools.converters import convert_to_nista
from agent_planning import AgentPlanner, ScheduleOptimizer

def main(input_path: str, output_path: str):
    # Load
    print("Loading project...")
    project = parse_project(input_path)
    
    # Validate
    print("Validating against NISTA...")
    validator = NISTAValidator()
    result = validator.validate(project)
    
    if not result.compliant:
        print(f"Warning: {len(result.issues)} compliance issues")
    
    # Analyze risks
    print("Analyzing risks...")
    planner = AgentPlanner(model="claude-3-opus")
    risks = planner.identify_risks(project)
    print(f"Found {len(risks)} risks")
    
    # Optimize
    print("Optimizing schedule...")
    optimizer = ScheduleOptimizer()
    optimized = optimizer.optimize(project, objective="duration")
    
    # Convert
    print("Converting to NISTA format...")
    nista_project = convert_to_nista(optimized)
    
    # Final validation
    final_result = validator.validate(nista_project)
    
    # Save
    nista_project.save(output_path)
    print(f"Saved to {output_path}")
    print(f"Compliance: {final_result.compliance_score}%")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python pipeline.py input.mpp output.json")
        sys.exit(1)
    
    main(sys.argv[1], sys.argv[2])
```

## Running the Pipeline

```bash
# Install dependencies
pip install pm-data-tools agent-task-planning

# Run pipeline
python pipeline.py my_project.mpp optimized_nista.json
```

## Using with Claude Desktop

You can also run this pipeline interactively through Claude Desktop:

```
"Load /projects/building.mpp, analyze risks, optimize the schedule, 
and export to NISTA format with full compliance validation"
```

Claude will use the MCP servers to execute each step and provide detailed feedback.

## Authors

Members of the PDA Task Force

This pipeline demonstrates the full capabilities of the PDA Platform in support of the NISTA Programme and Project Data Standard trial.
