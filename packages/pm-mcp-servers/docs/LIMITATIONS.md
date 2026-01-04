# Limitations and Appropriate Use

## Purpose

This document describes the known limitations of pda-platform and guidance on appropriate use. Understanding these limitations is essential for responsible deployment.

## Intended Use

pda-platform is designed as **decision-support infrastructure** for project management professionals. It provides:

- Data parsing and conversion across formats
- Compliance validation against NISTA standards
- AI-assisted risk identification
- Forecasting with uncertainty quantification
- Anomaly detection in project data

### Appropriate Uses

✅ Augmenting human project analysis
✅ Identifying potential risks for human review
✅ Validating data quality before submission
✅ Converting between project management formats
✅ Generating forecasts for planning discussions
✅ Compliance checking against NISTA standards

### Inappropriate Uses

❌ Fully automated decision-making without human review
❌ Life-safety critical applications
❌ Legal or contractual determinations
❌ Processing personal or sensitive data
❌ Real-time control systems
❌ Applications requiring guaranteed accuracy

## Technical Limitations

### Data Quality Dependency

**Limitation**: Output quality depends entirely on input quality.

- "Garbage in, garbage out" applies
- Missing data reduces confidence scores
- Inconsistent data may produce misleading results

**Mitigation**: 
- Use pm-validate to check data quality first
- Review confidence scores
- Cross-check results with source data

### Format-Specific Constraints

**Limitation**: Parser capabilities vary by format.

| Format | Completeness | Notes |
|--------|-------------|--------|
| MSPDI | 95% | Full Microsoft Project support |
| P6 XER | 90% | Most Primavera features |
| NISTA | 100% | Complete standard coverage |
| Jira | 80% | API-dependent fields |
| Monday | 75% | Limited schedule data |
| Asana | 75% | Limited project management features |
| Smartsheet | 80% | Varies by sheet structure |
| GMPP | 85% | UK government focus |

**Mitigation**: Test with your specific format; report parsing issues

### Processing Scale

**Limitation**: Performance degrades with very large projects.

| Project Size | Performance |
|--------------|-------------|
| <1,000 tasks | Excellent (<5s) |
| 1,000-5,000 tasks | Good (<30s) |
| 5,000-10,000 tasks | Acceptable (<2min) |
| >10,000 tasks | May be slow (>2min) |

**Mitigation**: Consider breaking very large projects into phases

### No Historical Learning

**Limitation**: The platform does not learn from past analyses.

- Each analysis is independent
- No organizational memory
- No improvement from usage

**Mitigation**: Maintain your own lessons learned database

## AI-Specific Limitations

### Confidence Scores Are Estimates

**Limitation**: Confidence scores (0.0-1.0) indicate quality, not certainty.

| Range | Interpretation | Recommended Action |
|-------|---------------|-------------------|
| 0.0-0.3 | Low | Treat as exploratory only |
| 0.3-0.5 | Questionable | Review evidence carefully; seek corroboration |
| 0.5-0.7 | Moderate | Reasonable basis for further investigation |
| 0.7-0.85 | Good | Can inform decisions with normal review |
| 0.85-1.0 | High | Strong basis; verify for critical decisions |

**Important**: Even high-confidence outputs should be reviewed for critical decisions.

### Risk Identification Not Exhaustive

**Limitation**: Cannot identify all possible risks.

- Rule-based detection has blind spots
- Novel or complex risks may be missed
- Assumes standard project structures

**Mitigation**: Use as one input to comprehensive risk management

### Forecasting Uncertainty

**Limitation**: All forecasts have inherent uncertainty.

- Point estimates are best-effort predictions
- Confidence intervals show range of possibilities
- External factors cannot be predicted

**Mitigation**: 
- Use confidence intervals, not just point estimates
- Review multiple scenario forecasts
- Update forecasts regularly

### No Domain Expertise

**Limitation**: The platform has no sector-specific knowledge.

- Cannot assess technical feasibility
- No knowledge of regulatory requirements
- No understanding of organizational context

**Mitigation**: Combine with domain expert review

## Known Edge Cases

### Schedule Analysis
- Very short schedules (<10 tasks): Limited statistical significance
- Very long schedules (>10,000 tasks): Performance may degrade
- Schedules without baseline: Many metrics unavailable
- Schedules with circular dependencies: Will be flagged but may affect analysis

### Cost Analysis
- Missing budget data: Cost analysis unavailable
- Multiple currencies: Not automatically converted
- Cost loaded tasks without resource rates: Estimates may be inaccurate

### Resource Analysis
- Resources without assignments: Cannot analyse utilisation
- Shared resources across projects: Single-project view only
- Non-labour resources: Limited analysis available

## Regulatory Limitations

### Not a Compliance Certificate

pda-platform validates against NISTA standards but:
- Validation is advisory, not certification
- Does not guarantee regulatory compliance
- Cannot substitute for official compliance review
- Rules may not reflect latest guidance

**Mitigation**: Treat as first-pass check; seek official review for submissions

### Data Protection

**Limitation**: Platform is not designed for personal data processing.

- No GDPR compliance features
- No data subject rights handling
- No privacy impact assessment

**Mitigation**: Do not process personal data

## Operational Limitations

### No Real-Time Updates

**Limitation**: Analysis is point-in-time only.

- Does not monitor projects continuously
- Does not alert to changes
- Does not integrate with live systems

**Mitigation**: Re-run analysis regularly

### No Multi-Project Portfolio View

**Limitation**: Analyses one project at a time.

- No portfolio-level insights
- No cross-project dependencies
- No resource conflicts across projects

**Mitigation**: Use external portfolio tools

### No Collaboration Features

**Limitation**: Single-user analysis tool.

- No multi-user access
- No commenting or workflows
- No approval processes

**Mitigation**: Export results to collaboration tools

## Responsible Use Guidance

### Human Review Required

All outputs must be reviewed by qualified professionals:
- Project managers for schedule analysis
- Cost controllers for budget forecasts
- Risk managers for risk identification
- Senior decision-makers for critical choices

### Verification Steps

Before acting on platform outputs:
1. Review confidence scores
2. Check evidence trails
3. Cross-reference with source data
4. Consult domain experts
5. Consider organizational context
6. Document your review

### When to Seek Additional Input

Escalate for expert review when:
- Confidence scores are low (<0.5)
- Results conflict with expectations
- Decisions have significant impact
- Regulatory compliance is involved
- Safety is a consideration

## Updates and Improvements

We continuously work to address limitations:
- Bug fixes in patch releases (0.3.x)
- New features in minor releases (0.x.0)
- Major improvements in major releases (x.0.0)

See our [roadmap](../IMPLEMENTATION_ROADMAP.md) for planned improvements.

## Reporting Limitations

If you encounter a limitation not documented here:
- Open a GitHub issue
- Email: hello@pdataskforce.com
- Include examples and context

We appreciate feedback to improve this documentation.

---

**Last updated**: January 2026  
**Version**: 0.3.0
