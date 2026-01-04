# HealthAssessor Model Card

## Model Details

| Attribute | Value |
|-----------|-------|
| Model Name | HealthAssessor |
| Version | 0.3.0 |
| Model Type | Multi-dimensional scoring system |
| Developer | PDA Task Force |
| License | MIT |
| Last Updated | 2026-01-04 |

## Intended Use

The HealthAssessor model is designed to:

- **Calculate comprehensive project health scores** across five key dimensions
- **Provide portfolio visibility** into overall project status and risk profiles
- **Support governance decision-making** by aggregating multiple health indicators
- **Enable proactive management** by identifying projects requiring attention
- **Facilitate consistent evaluation** of project health across portfolios

### Primary Users
- Project managers assessing project viability and status
- Portfolio managers monitoring portfolio health
- Senior leadership evaluating overall project performance
- Governance bodies making portfolio-level decisions
- Risk and compliance functions

### Appropriate Use Cases
- Monthly or periodic project health reviews
- Portfolio health dashboards and reporting
- Identifying projects that require escalation or intervention
- Resource allocation and prioritization decisions
- Trend analysis and historical health comparison
- Governance reporting and board-level summaries

### Inappropriate Use Cases
- Automated project termination decisions without human review
- Personnel evaluations or performance ratings
- Determining individual team member competence
- Making staffing or reorganization decisions
- Excluding teams or individuals from opportunities based on score alone
- Bypassing established project governance and approval processes

## Methodology

The HealthAssessor employs a multi-dimensional scoring approach that evaluates project health across five key dimensions:

### Five Dimensions with Weights

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Schedule | 30% | Project timeline adherence and forecast accuracy |
| Cost | 25% | Budget management and financial performance |
| Scope | 15% | Scope management and change control |
| Resources | 15% | Resource availability and team capacity |
| Risk | 15% | Overall risk profile and mitigation status |

### Scoring Algorithm

The HealthAssessor uses the following scoring methodology:

1. **Baseline Score:** Begins with a perfect score of 100 points
2. **Dimension Assessment:** Evaluates each dimension against defined criteria
3. **Deduction Calculation:** Deducts points based on identified issues
4. **Weighted Aggregation:** Applies dimension weights to calculate final score
5. **Dimension Breakdown:** Provides individual scores for each dimension

## Status Classification

Health assessment results are classified into status categories:

### Healthy (Score >= 75)
- Project is on track and performing well
- Minor issues that are being managed effectively
- Low risk of project failure or significant deviation
- Routine management and standard oversight sufficient

### At Risk (Score 50-74)
- Project has notable challenges requiring attention
- Multiple minor issues or one or more significant issues present
- Moderate risk of further deterioration or schedule/cost impact
- Enhanced oversight and corrective action planning required

### Critical (Score < 50)
- Project has serious problems requiring immediate intervention
- Major issues across multiple dimensions or one critical issue
- High risk of project failure, significant delays, or cost overrun
- Escalation and intensive management required

## Outputs

The HealthAssessor produces structured HealthAssessment objects with detailed dimension breakdown, individual issue identification, and recommended corrective actions.

## Limitations

- **Simplified representation:** A single score cannot capture all aspects of project health
- **Historical data dependent:** Accuracy depends on availability and quality of historical project data
- **Context-insensitive:** Does not account for external factors
- **Threshold-based:** Status classifications use fixed thresholds that may not apply to all project types
- **Lag effect:** Reflects current data; may not capture emerging issues before next assessment cycle
- **Domain assumptions:** Built on assumptions about project management best practices
- **Input data quality:** Results are only as good as the underlying data provided

## Ethical Considerations

### Fairness
- The model applies consistent rules across all projects
- Organizations should monitor for disparate impact on specific projects or teams
- Use results transparently and explain assessment results to project teams

### Transparency
- Model methodology and weightings should be clearly documented
- Project teams should understand what factors contribute to their health score
- Assessment results should include detailed breakdown and specific issues identified

### Appropriate Use
- Use as input to decision-making, not as sole decision criterion
- All decisions based on health assessments should include human review
- Should not be used for automated project termination or team removal

### Bias and Equity
- Results may reflect organizational bias in reporting and data collection
- Organizations should monitor for disparate impact on specific projects or teams
- Ensure assessment process is consistent and fair across all projects

## Contact

For questions, issues, or feedback about the HealthAssessor model:

**Email:** hello@pdataskforce.com
**Project:** PDA Platform
**License:** MIT

---

**Disclaimer:** This model provides assessment and analysis only and does not constitute advice. Organizations using this model remain responsible for all decisions based on its outputs and must ensure compliance with relevant policies, procedures, and regulations.
