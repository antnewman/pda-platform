# NISTA Migration Guide

Quick guide for migrating existing project data to NISTA compliance.

## Step 1: Assess Current State

```python
from pm_data_tools.schemas.monday import MondayParser
from pm_data_tools.migration import NISTAMigrationAssistant

# Parse your current data
parser = MondayParser()
project = parser.parse_file("monday_board.json")

# Assess NISTA compliance
assistant = NISTAMigrationAssistant()
report = assistant.assess(project)

print(report)
# Shows: compliance score, gaps, effort estimate
```

## Step 2: Address Required Gaps

Focus on required fields first:

```python
for gap in report.gaps:
    if gap.required:
        print(f"{gap.field_name}: {gap.mapping_suggestion}")
```

### Common Required Field Mappings

| NISTA Field | Monday.com | Asana | Smartsheet | Jira |
|-------------|------------|-------|------------|------|
| project_id | board.id | project.gid | sheet.id | project.key |
| project_name | board.name | project.name | sheet.name | project.name |
| department | custom "Department" | custom_field | column "Dept" | component |
| category | custom "Type" | custom_field | column "Category" | project_type |
| start_date | earliest item date | start_on | min date column | start_date |
| end_date | latest item date | due_on | max date column | due_date |
| whole_life_cost | sum of budget column | custom cost field | sum cost column | custom field |

## Step 3: Enrich Missing Data

For fields without source mappings:

### Delivery Confidence Assessment (DCA)
```python
# Manual assessment required
# Review project status and apply DCA criteria:
# - Green: On track, no significant issues
# - Amber: Feasible but requires attention
# - Red: Delivery in doubt

project_with_dca = Project(
    **project.__dict__,
    delivery_confidence=DeliveryConfidence.AMBER
)
```

### Senior Responsible Owner
```python
# Extract from project manager or assign
sro_name = project.project_manager or "John Smith"
```

### Category
```python
# Classify based on project type
category_map = {
    "IT": "ICT",
    "Construction": "Infrastructure and Construction",
    "Digital": "Government Transformation and Service Delivery",
    "Defence": "Military Capability"
}
category = category_map.get(project.category, "Government Transformation and Service Delivery")
```

## Step 4: Validate and Export

```python
from pm_data_tools.schemas.nista import NISTAValidator, NISTAExporter

# Validate
validator = NISTAValidator()
result = validator.validate_project(enriched_project)

if result.compliant:
    # Export to NISTA format
    exporter = NISTAExporter()
    exporter.to_file(enriched_project, "nista_submission.json")
    print("✓ NISTA-compliant export created")
else:
    print(f"Remaining issues: {result.error_count}")
```

## Common Scenarios

### Migrating from GMPP CSV
Already compatible! Just parse and validate:
```python
from pm_data_tools.schemas.nista import NISTAParser

parser = NISTAParser()
projects = parser.parse_file("gmpp_data.csv")  # Works directly
```

### Migrating from Monday.com
1. Export board to JSON
2. Parse with MondayParser
3. Add: department, category, DCA, SRO
4. Export with NISTAExporter

### Migrating from Asana
1. Export project via API
2. Parse with AsanaParser
3. Map custom fields to NISTA fields
4. Validate and export

### Migrating from Smartsheet
1. Export sheet to JSON
2. Parse with SmartsheetParser
3. Map columns to NISTA fields
4. Add governance fields (SRO, DCA)
5. Export

## Effort Estimates

| Scenario | Typical Effort | Notes |
|----------|---------------|-------|
| GMPP CSV → NISTA | < 1 hour | Already compliant, just format conversion |
| Monday/Asana/Smartsheet → NISTA | 1-3 days | Requires field mapping + data enrichment |
| Microsoft Project → NISTA | 2-5 days | Complex scheduling data, needs DCA/benefits |
| Jira → NISTA | 3-5 days | Agile → Waterfall mapping, add financials |

## Automation Tips

1. **Batch Processing**: Use CSV export for multiple projects
2. **Template Mapping**: Save custom field mappings in config
3. **Scheduled Exports**: Automate monthly NISTA submissions
4. **Validation CI**: Run NISTA validation in build pipeline

## Support

For migration assistance:
- Review field mappings: [schema-mapping.md](schema-mapping.md)
- Check examples: `tests/fixtures/nista/`
- Raise issues: GitHub Issues
