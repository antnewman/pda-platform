# NISTA Compliance Example

Validate project data against the NISTA Programme and Project Data Standard.

## Overview

This example demonstrates how to use pm-data-tools to validate project management data against NISTA requirements.

## Usage

```python
from pm_data_tools import parse_project
from pm_data_tools.validators import NISTAValidator

# Load project from any format
project = parse_project("my_project.mpp")

# Validate NISTA compliance
validator = NISTAValidator(strictness="standard")
result = validator.validate(project)

print(f"Compliant: {result.compliant}")
print(f"Score: {result.compliance_score}%")
print(f"Missing fields: {result.missing_required_fields}")

# Get detailed report
for issue in result.issues:
    print(f"{issue.severity}: {issue.message}")
```

## Strictness Levels

- **lenient**: Warnings for missing optional fields
- **standard**: Errors for missing required fields
- **strict**: Errors for any non-compliant data

## Required Fields

NISTA requires:
- Project name and unique ID
- WBS structure
- Task start and finish dates
- Resource assignments
- Dependency relationships

## Converting to NISTA Format

```python
from pm_data_tools.converters import convert_to_nista

# Convert any format to NISTA
nista_data = convert_to_nista(project)

# Export
nista_data.save("project_nista.json")
```

## Authors

Members of the PDA Task Force

This example supports the NISTA Programme and Project Data Standard trial.
