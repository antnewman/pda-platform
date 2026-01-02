# NISTA Programme and Project Data Standard - Research Notes

**Research Date:** 2026-01-01
**Researcher:** antnewman
**Purpose:** Define NISTA schema for pm-data-tools v0.2.0

## Executive Summary

The UK Government launched the **Programme and Project Data Standard** in December 2025 as part of the Government Project Delivery framework overseen by NISTA (National Infrastructure and Service Transformation Authority). This standard mandates a common way of defining, formatting, and updating programme and project data across all government departments and arm's length bodies.

## Key Findings

### 1. Standard Overview

**Publication Date:** December 11, 2025
**Authority:** Government Project Delivery / NISTA
**Scope:** All UK government departments and arm's length bodies
**Purpose:** Improve data quality/standardization to enable reliable AI insights

**Governance Structure:**
- **Accounting officers:** Accountable for information/data management
- **Chief data officers:** Responsible for data management expectations and compliance
- **Senior officer for project delivery:** Ensures compliance with the standard
- **Portfolio directors / SROs:** Ensure data is created/managed per standard

### 2. GMPP Data Structure (Current State)

The Government Major Projects Portfolio (GMPP) provides the baseline structure. Analysis of actual GMPP data (DfT March 2024) reveals the following fields:

#### Core Identification Fields
- `GMPP ID Number` - Unique project identifier (format: DEPT_NNNN_YYYY-QN)
- `Project Name` - Full project name
- `Department` - Owning department (e.g., DFT, MOD, DHSC)
- `Annual Report Category` - Project type classification

#### Project Classification
Four categories identified in NISTA Annual Report 2024-25:
1. **Infrastructure & Construction** - 68 projects, £433B
2. **Transformation & Service Delivery** - 76 projects, £200B
3. **Military Capability** - 45 projects, £327B
4. **ICT** - 24 projects, £36B

#### Description Fields
- `Description / Aims` - Free text project description
- `Departmental commentary on actions planned or taken on the IPA RAG rating`
- `Departmental narrative on schedule, including any deviation from planned schedule (if necessary)`
- `Departmental narrative on budget/forecast variance for 2023/24 (if variance is more than 5%)`
- `Departmental Narrative on Budgeted Whole Life Costs`
- `Departmental Narrative on Budgeted Benefits`

#### Delivery Confidence Assessment (DCA)
- `IPA Delivery Confidence Assessment` - Three-point scale: Red/Amber/Green
  - **Green (14%):** 30 projects - On track
  - **Amber (63%):** 135 projects - Feasible but requires management attention
  - **Red (15%):** 31 projects - In doubt; £198B in costs
  - **Exempt (8%):** 17 projects - Not assessed
- `SRO Delivery Confidence Assessment` - Same scale, SRO's own assessment

#### Schedule Fields
- `Project - Start Date (Latest Approved Start Date)` - Format: YYYY-MM-DD
- `Project - End Date (Latest Approved End Date)` - Format: YYYY-MM-DD

#### Financial Fields (all in £m)
- `Financial Year Baseline (£m) (including Non-Government Costs)` - Annual budget
- `Financial Year Forecast (£m) (including Non-Government Costs)` - Annual forecast
- `Financial Year Variance (%)` - Percentage variance
- `TOTAL Baseline Whole Life Costs (£m) (including Non-Government Costs)` - Whole Life Cost (WLC)
- `TOTAL Baseline Benefits (£m)` - Monetised benefits

#### Senior Responsible Owner
- SRO mentioned in governance requirements (not a separate field in current GMPP data)

### 3. GMPP Portfolio Statistics (March 2025)

**Total Projects:** 213
**Total Whole Life Costs:** £996 billion
**Total Monetised Benefits:** £742 billion
**Departments:** 20

**10-Year Infrastructure Commitment:** £725 billion

### 4. Data Governance Requirements

From the Programme and Project Data Standard:

**Compliance Path:**
- Organizations must develop implementation plans if immediate compliance is impossible
- Compliance path varies based on IT systems, data management practices, and data maturity
- Standard applies to portfolios, programmes, and projects

**Accountability:**
- Accounting officers accountable for data management
- CDOs responsible for compliance
- SROs ensure programme/project data complies with standard

### 5. Gap Analysis: GMPP vs NISTA Standard Requirements

**Fields Present in GMPP:**
- Project identification (name, code, department)
- Delivery Confidence Assessment (DCA) - Red/Amber/Green
- Whole Life Cost (WLC)
- Start/end dates (baseline)
- Benefits (monetised)
- Project category
- Annual budget and forecast

**Likely NISTA Additions (based on standard requirements):**
- **Senior Responsible Owner (SRO)** - Name/contact (mentioned in governance)
- **Forecast dates** - In addition to baseline dates
- **Risk and issues summary** - Structured data (currently narrative only)
- **Non-monetised benefits** - Structured field
- **Milestones and key dates** - Structured milestone data
- **Machine-readable format** - JSON schema (currently CSV/Excel)
- **Custom fields** - Department-specific extensions

### 6. Data Format Observations

**Current GMPP Format:**
- Primary: CSV and Excel (.xlsx)
- Date format: ISO 8601 (YYYY-MM-DD)
- Currency: £ millions (m)
- Text fields: Allow multiline with _x000D_ line breaks
- IDs: Structured as DEPT_NUMBER_YEAR-QUARTER

**Proposed NISTA Format:**
- JSON Schema for validation
- Support for JSON, CSV, and Excel input/output
- Maintain backward compatibility with existing GMPP structure
- Add required fields for NISTA compliance

### 7. Implementation Strategy

**Phase 1: Schema Definition**
1. Create JSON Schema v1.0 based on GMPP + NISTA requirements
2. Define three strictness levels:
   - **Lenient:** Critical GMPP fields only (backward compatible)
   - **Standard:** All required NISTA fields, warn on recommended
   - **Strict:** Treat recommended as required

**Phase 2: Parser**
- Support CSV, Excel, and JSON input
- Handle GMPP legacy format
- Map to canonical model

**Phase 3: Validator**
- JSON Schema validation
- Three strictness levels
- Detailed compliance reporting (0-100 score)

**Phase 4: Exporter**
- Output to JSON, CSV, Excel
- NISTA-compliant formatting
- Optional: Include only fields required for submission

**Phase 5: Migration Assistant**
- Assess current compliance score
- Identify gaps
- Suggest field mappings
- Estimate migration effort

### 8. Required Field Definitions (Draft)

Based on research, the following fields are required for NISTA compliance:

**Level 1 - Critical (from GMPP):**
- project_id
- project_name
- department
- category (Infrastructure/Transformation/Military/ICT)
- delivery_confidence_assessment (IPA)
- delivery_confidence_assessment_sro
- start_date_baseline
- end_date_baseline
- whole_life_cost_baseline
- benefits_baseline

**Level 2 - Standard (NISTA additions):**
- senior_responsible_owner (name, contact)
- start_date_forecast
- end_date_forecast
- whole_life_cost_forecast
- benefits_non_monetised
- milestones (structured array)
- risks_summary
- issues_summary

**Level 3 - Recommended:**
- annual_budget
- annual_forecast
- variance_percentage
- narratives (various)
- custom_fields

## Next Steps

1. Define JSON Schema incorporating:
   - All GMPP fields (backward compatibility)
   - NISTA required fields
   - Extensibility for future requirements

2. Create test fixtures from real GMPP data

3. Implement parser, validator, exporter, and migration assistant

4. Document schema mapping: NISTA ↔ Canonical Model

5. Write comprehensive tests (target: 100+ tests)

## Sources

- [Government launches new standard for programme and project data](https://projectdelivery.gov.uk/2025/12/11/government-launches-new-standard-for-programme-and-project-data/)
- [NISTA Annual Report 2024-25](https://www.gov.uk/government/publications/nista-annual-report-2024-2025/nista-annual-report-2024-25)
- [Major projects data - GOV.UK](https://www.gov.uk/government/collections/major-projects-data)
- [DfT GMPP Data March 2024](https://www.gov.uk/government/publications/dft-government-major-projects-portfolio-data-2024)

## IP Protection Note

**This research establishes prior art for the NISTA schema implementation.**
Timestamped: 2026-01-01
License: MIT (as per pm-data-tools repository)
