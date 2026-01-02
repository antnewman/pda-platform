# NISTA Integration - Programme and Project Data Standard

**Status:** Phase 2 Complete - Reference Implementation
**Version:** 0.2.0
**Standard:** UK Government Programme and Project Data Standard (December 2025)

## Overview

This module provides the **reference implementation** for the UK Government's NISTA (National Infrastructure and Service Transformation Authority) Programme and Project Data Standard. It enables parsing, validation, export, and migration assistance for NISTA-compliant project data.

## Quick Start

### Parse NISTA Data

```python
from pm_data_tools.schemas.nista import NISTAParser

# Parse JSON (native NISTA format)
parser = NISTAParser()
project = parser.parse_file("nista_submission.json")

# Parse CSV (GMPP legacy format)
projects = parser.parse_file("gmpp_data.csv")

# Parse Excel
projects = parser.parse_file("gmpp_data.xlsx")
```

### Validate Compliance

```python
from pm_data_tools.schemas.nista import NISTAValidator, StrictnessLevel

# Standard validation
validator = NISTAValidator(version="1.0", strictness=StrictnessLevel.STANDARD)
result = validator.validate_project(project)

print(f"Compliant: {result.compliant}")
print(f"Score: {result.compliance_score}%")
print(f"Missing: {result.missing_required_fields}")

# Three strictness levels
lenient = NISTAValidator(strictness=StrictnessLevel.LENIENT)    # GMPP compatible
standard = NISTAValidator(strictness=StrictnessLevel.STANDARD)  # Default
strict = NISTAValidator(strictness=StrictnessLevel.STRICT)      # Full compliance
```

### Export to NISTA Format

```python
from pm_data_tools.schemas.nista import NISTAExporter

exporter = NISTAExporter(version="1.0")

# Export to JSON
exporter.to_file(project, "output.json")

# Export to CSV (GMPP format)
exporter.to_csv([project1, project2], "output.csv")

# Export to Excel
exporter.to_excel(projects, "output.xlsx")
```

### Migration Assessment

```python
from pm_data_tools.migration import NISTAMigrationAssistant

assistant = NISTAMigrationAssistant()
report = assistant.assess(project)

print(f"Current Compliance: {report.current_compliance_score}%")
print(f"Gaps: {report.required_gaps_count} required, {report.recommended_gaps_count} recommended")
print(f"Effort: {report.estimated_effort.value}")

# Get specific recommendations
for gap in report.gaps:
    print(f"- {gap.field_name}: {gap.mapping_suggestion}")
```

## NISTA Standard Fields

### Required Fields (Lenient)
- `project_id` - Unique identifier
- `project_name` - Project name
- `department` - Owning department
- `category` - Infrastructure / Transformation / Military / ICT
- `delivery_confidence_assessment_ipa` - Green / Amber / Red / Exempt
- `start_date_baseline` - Planned start (ISO 8601)
- `end_date_baseline` - Planned end (ISO 8601)
- `whole_life_cost_baseline` - Total cost (£ millions)

### Required Fields (Standard)
All lenient fields plus:
- `delivery_confidence_assessment_sro` - SRO's DCA
- `senior_responsible_owner` - SRO details
- `benefits_baseline` - Monetised benefits (£ millions)

### Recommended Fields
- `description` - Project description and aims
- `milestones` - Key project milestones
- `risks_summary` - Top risks and counts
- `issues_summary` - Top issues and counts

### Optional Fields
- `start_date_forecast` - Forecast start
- `end_date_forecast` - Forecast end
- `whole_life_cost_forecast` - Forecast cost
- `benefits_non_monetised` - Non-financial benefits
- `custom_fields` - Department-specific extensions

## Compliance Levels

### Lenient (GMPP Compatible)
Minimum viable for legacy GMPP data. Requires only core identification and financial fields.

**Use when:** Migrating from existing GMPP CSV exports.

### Standard (Default)
Full NISTA compliance for government reporting. Includes governance and benefits tracking.

**Use when:** Submitting data for NISTA/IPA reporting.

### Strict (Gold Standard)
Comprehensive compliance including milestones, risks, and issues.

**Use when:** Internal governance requires full transparency.

## Data Formats

### JSON (Native)
```json
{
  "project_id": "DFT_0048_2021-Q3",
  "project_name": "Example Project",
  "department": "DFT",
  "category": "Infrastructure and Construction",
  "delivery_confidence_assessment_ipa": "Amber",
  "start_date_baseline": "2024-04-01",
  "end_date_baseline": "2027-03-31",
  "whole_life_cost_baseline": 1959,
  "benefits_baseline": 24475,
  "milestones": [
    {
      "name": "Gate 1 - Business Case",
      "baseline_date": "2024-06-30",
      "status": "Completed"
    }
  ]
}
```

### CSV (GMPP Legacy)
Standard GMPP column format with 19 columns. Automatically mapped to NISTA fields.

### Excel (.xlsx)
Same structure as CSV, compatible with existing GMPP templates.

## Migration Guide

See [migration-guide.md](migration-guide.md) for detailed migration instructions from:
- Monday.com
- Asana
- Smartsheet
- Jira
- Microsoft Project
- Primavera P6

## Schema Mapping

See [schema-mapping.md](schema-mapping.md) for complete field mappings between NISTA and the canonical model.

## API Reference

### NISTAParser
- `parse_file(path)` - Auto-detect format and parse
- `parse_json(data)` - Parse JSON dict
- `parse_csv(rows)` - Parse CSV rows
- `parse_excel_file(path)` - Parse Excel file

### NISTAValidator
- `validate(data)` - Validate NISTA dict
- `validate_project(project)` - Validate canonical Project
- `validate_file(path)` - Validate JSON file

### NISTAExporter
- `export(project)` - Export to NISTA dict
- `to_file(project, path)` - Export to JSON
- `to_csv(projects, path)` - Export to CSV
- `to_excel(projects, path)` - Export to Excel

### NISTAMigrationAssistant
- `assess(project)` - Assess compliance and gaps
- Returns `MigrationReport` with:
  - `current_compliance_score`
  - `gaps` - List of missing fields
  - `mapping_suggestions` - Field mapping hints
  - `estimated_effort` - LOW / MEDIUM / HIGH

## Contributing

This is the reference implementation for the NISTA standard. Contributions should maintain:
1. JSON Schema Draft 7 compliance
2. Backward compatibility with GMPP
3. Three-level strictness support
4. Comprehensive test coverage

## License

MIT License - See LICENSE file

## References

- [NISTA Programme and Project Data Standard](https://projectdelivery.gov.uk/)
- [GMPP Annual Report 2024-25](https://www.gov.uk/government/publications/nista-annual-report-2024-2025)
- [pm-data-tools Repository](https://github.com/PDA-Task-Force/pm-data-tools)

---

**Timestamp:** 2026-01-01
**Authors:** PDA Task Force
**Status:** Reference Implementation
