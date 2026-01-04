# OutlierDetector Model Card

## Model Details

| Attribute | Value |
|-----------|-------|
| Model Name | OutlierDetector |
| Version | 0.3.0 |
| Model Type | Statistical anomaly detection |
| Developer | PDA Task Force |
| License | MIT |
| Last Updated | 2026-01-04 |

## Intended Use

The OutlierDetector model is designed to:

- **Identify anomalous values** in project management data that deviate significantly from established patterns
- **Support data quality analysis** by flagging potentially erroneous or suspicious data entries
- **Enable informed decision-making** by highlighting data points that warrant human review and verification
- **Assist in risk identification** by surfacing unusual patterns that may indicate underlying project issues

### Primary Users
- Project managers conducting data quality reviews
- Portfolio managers assessing project health
- Quality assurance teams validating project data
- Governance and compliance functions

### Appropriate Use Cases
- Validating project status reports for unusual entries
- Identifying data entry errors in project management systems
- Detecting potentially fraudulent or fabricated project metrics
- Flagging unusual project performance indicators for further investigation

### Inappropriate Use Cases
- Automated decision-making without human oversight
- Excluding team members based on outlier detection results
- Making personnel decisions based solely on outlier flags
- Determining resource allocation without human review

## Methodology

The OutlierDetector employs multiple statistical and heuristic analysis methods:

### 1. Z-Score Analysis
- Calculates Z-scores for numerical values to identify statistical outliers
- Measures how many standard deviations a value is from the mean
- Sensitive to changes in variance and absolute values

### 2. Progress Comparison
- Analyzes project progress patterns over time
- Identifies non-linear or inconsistent progress trajectories
- Flags sudden jumps or drops in reported progress

### 3. Float Analysis
- Examines floating-point values for unrealistic precision
- Identifies values that may indicate data entry errors
- Flags values outside reasonable ranges for specific metrics

### 4. Date Validation
- Validates date fields for logical consistency
- Ensures dates fall within expected project timeframes
- Identifies date anomalies (e.g., end dates before start dates)

### 5. Baseline Variance Analysis
- Compares current values against established baselines
- Identifies significant deviations from planned or historical values
- Measures variance relative to previous reporting periods

## Configurable Thresholds

The OutlierDetector uses the following configurable parameters:

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| Z-Score Threshold | 2.5 | 1.0 - 5.0 | Standard deviations from mean to flag as outlier |
| Duration Max | 120 | 30 - 365 | Maximum project duration in days |
| Progress Max | 100 | 80 - 100 | Maximum allowed progress percentage |
| Variance Multiplier | 1.5 | 1.0 - 3.0 | Acceptable variance relative to baseline |
| Confidence Level | 0.95 | 0.80 - 0.99 | Statistical confidence for flagging outliers |

## Severity Classification

Detected outliers are classified into severity levels:

### Critical
- Values that are clearly impossible (negative durations, >100% progress)
- Date inconsistencies that break logical project sequencing
- Data that appears fabricated or fraudulently entered
- Z-scores > 4.0 for key metrics

### High
- Values 3.0 - 4.0 standard deviations from mean
- Significant unexplained changes from previous reports
- Progress reported beyond planned project end date
- Variance >2x baseline variance

### Medium
- Values 2.5 - 3.0 standard deviations from mean
- Moderate variance from baseline (1.5x - 2.0x)
- Unusual but plausible data patterns
- Progress jumps >20% in single reporting period

### Low
- Values 2.0 - 2.5 standard deviations from mean
- Minor variance from baseline (1.2x - 1.5x)
- Plausible but noteworthy data patterns
- Slight inconsistencies in reporting

## Outputs

The OutlierDetector produces structured outlier objects with:

```json
{
  "outlier_id": "unique_identifier",
  "field_name": "name_of_analyzed_field",
  "value": 150,
  "severity": "High",
  "type": "z_score | progress | float | date | variance",
  "evidence": {
    "mean": 45.5,
    "std_dev": 12.3,
    "z_score": 3.2,
    "baseline": 50,
    "variance_multiplier": 2.1
  },
  "description": "Human-readable explanation of the anomaly",
  "recommended_action": "Review data entry | Verify project status | Contact team",
  "timestamp": "2026-01-04T10:30:00Z"
}
```

## Limitations

- **Statistical limitations:** Works best with datasets containing 10+ historical data points; less reliable with limited historical data
- **Rule-based approach:** Does not learn from data patterns; detection rules are static and predefined
- **Context-insensitive:** Cannot account for legitimate business reasons for unusual values (e.g., scope changes, force majeure events)
- **False positives:** May flag legitimate outliers that warrant human explanation
- **Domain knowledge:** Does not encode project management domain expertise; relies on statistical patterns
- **Assumption of normality:** Z-score analysis assumes approximately normal distributions; less effective with bimodal or skewed distributions

## Ethical Considerations

### Fairness
- The model applies consistent statistical rules across all projects and teams
- Outlier detection is based on data patterns, not subjective judgment
- Organizations must ensure outlier flags do not result in unfair treatment of teams or individuals
- Use in governance processes should include human review to ensure fairness

### Transparency
- All detection methods are transparent and explainable
- Users can understand why specific data points are flagged
- Model thresholds and parameters should be documented and communicated
- Organizations should document how outlier findings inform decisions

### Appropriate Use
- Results should be treated as data quality flags, not definitive proof of errors or misconduct
- All flagged outliers require human investigation before action
- Should not be used for automated personnel decisions or punitive actions
- Organizations should establish clear policies on how outlier findings are used

### Bias and Fairness
- Results may be biased by historical data quality issues
- Different projects with different reporting cultures may see different flagging rates
- Organizations should monitor flagging patterns across teams for potential disparate impact
- Thresholds should be reviewed periodically to ensure fair application

## Contact

For questions, issues, or feedback about the OutlierDetector model:

**Email:** hello@pdataskforce.com
**Project:** PDA Platform
**License:** MIT

---

**Disclaimer:** This model provides statistical analysis only and does not constitute advice. Organizations using this model remain responsible for all decisions based on its outputs and must ensure compliance with relevant policies, procedures, and regulations.
