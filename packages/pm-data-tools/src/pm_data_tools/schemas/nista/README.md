# NISTA Support - Placeholder

## Overview

**NISTA** (National Infrastructure and Strategic Transport Agency) is the UK government standard for infrastructure and strategic transport project data, launched in December 2025.

## Current Status

This module is currently a **placeholder** awaiting the publication of the official NISTA schema specification. The NISTA standard is expected to build upon and extend the Government Major Projects Portfolio (GMPP) format.

## Roadmap

Once the official NISTA schema is published, this module will provide:

### 1. Parser (`nista/parser.py`)
- Parse NISTA data files (expected format: JSON or XML)
- Map NISTA fields to canonical Project model
- Handle NISTA-specific infrastructure and transport metadata

### 2. Writer (`nista/writer.py`)
- Export canonical Projects to NISTA format
- Ensure compliance with NISTA validation rules
- Support NISTA-specific extensions

### 3. Validator (`nista/validator.py`)
- Validate NISTA data against official schema
- Check infrastructure-specific constraints
- Verify transport project requirements

## Interim Approach

Until the NISTA schema is available, we recommend:

1. **Use GMPP Parser**: The GMPP parser supports UK government project data including:
   - Delivery Confidence Assessment (DCA)
   - Whole Life Cost
   - Senior Responsible Owner (SRO)
   - Department classification

2. **Extend for Infrastructure**: For infrastructure-specific fields, use the `custom_fields` extension on the Project model:

```python
from pm_data_tools.models import Project, CustomField
from pm_data_tools.schemas.gmpp import GMPPParser

parser = GMPPParser()
projects = parser.parse_file("data.csv")

# Add infrastructure-specific fields
for project in projects:
    project.custom_fields.append(
        CustomField(
            key="infrastructure_type",
            value="Transport",
            category="NISTA"
        )
    )
```

## Expected NISTA Extensions

Based on GMPP and infrastructure project requirements, NISTA is likely to include:

### Infrastructure Classification
- Project type (rail, road, airport, port, etc.)
- Geographic scope
- Strategic importance rating

### Transport-Specific Metrics
- Capacity improvements
- Journey time reductions
- Carbon impact
- Accessibility benefits

### Enhanced Governance
- Stakeholder management
- Environmental assessments
- Planning permissions status

## How to Contribute

Once the NISTA schema is published:

1. Contact the project maintainers with the official specification
2. We will implement parser, writer, and validator
3. Test cases will be created against official NISTA examples
4. Documentation will be updated

## Related Standards

- **GMPP**: Government Major Projects Portfolio (current implementation available)
- **IPA**: Infrastructure and Projects Authority reporting
- **HMT Green Book**: Business case appraisal guidance

## Contact

For questions or to share information about the NISTA schema:
- GitHub Issues: https://github.com/PDA-Task-Force/pm-data-tools/issues
- Email: For sensitive schema documents, contact maintainers directly

## References

- [Infrastructure and Projects Authority](https://www.gov.uk/government/organisations/infrastructure-and-projects-authority)
- [Major Projects Portfolio Data](https://www.gov.uk/government/collections/major-projects-data)

---

**Last Updated**: January 2025
**Status**: Awaiting NISTA schema publication
