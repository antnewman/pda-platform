# ATRS Guidance: Completing Algorithmic Transparency Records with pda-platform

## Introduction

This guide helps UK government departments and public sector organizations complete ATRS (Algorithmic Transparency Recording Standard) submissions using the pda-platform.

## What is ATRS?

ATRS is the UK government standard for recording information about algorithmic decision-making systems. It requires organizations to document what algorithms are used, how they work, what data they use, and how they are overseen.

## Why This Guidance Exists

Organizations using pda-platform need guidance on:
- Which platform tools produce ATRS-relevant information
- How to interpret platform outputs in ATRS context
- What additional information to gather outside the platform
- How to document governance and oversight processes

## How pda-platform Supports ATRS Compliance

The pda-platform provides:
- Data Analysis Tools (pm-analyse for understanding project data)
- Model Cards (detailed documentation of analytical models)
- Risk Identification (pm-analyse identifies potential issues)
- Data Validation (pm-validate ensures input quality)
- Forecasting (quantified uncertainty for decision-making)
- Documentation (automated generation of analysis reports)

### What pda-platform Does NOT Do
- Certify algorithmic compliance
- Serve as substitute for official ATRS submission
- Replace human judgment in governance
- Guarantee regulatory approval

## Section-by-Section Guidance for ATRS Submissions

### Section 1: Basic Information

Document the system as project analysis infrastructure used to support project management decision-making.

### Section 2: How It Works

Reference the following model cards:
- HealthAssessor: Multi-dimensional project health scoring
- OutlierDetector: Anomaly detection in project data
- RiskEngine: Risk identification and assessment
- ForecastEngine: Schedule and cost forecasting

### Section 3: Training Data

The pda-platform uses rule-based models, not machine learning. No training data is used. All rules are based on project management best practices and documented in model cards.

### Section 4: Human Oversight

Organizations must establish:
- Oversight processes for reviewing platform outputs
- Training for reviewers on system capabilities and limitations
- Escalation procedures for significant decisions
- Quality assurance processes for validating results
- Regular review of system configuration

### Section 5: Impact Assessment

Potential positive impacts:
- Early identification of project risks
- More consistent project health assessments
- Improved decision-making visibility

Potential negative impacts:
- Unfair evaluation if underlying data is biased
- Over-reliance on automated outputs
- Team morale impacts if used punitively

## Best Practices

- Always use platform outputs as one input among many
- Ensure qualified humans review all outputs before decisions
- Document how you have used platform information
- Monitor for unintended consequences
- Review system performance regularly
- Communicate openly about capabilities and limitations

## Contact

For questions about using pda-platform for ATRS compliance:

**Email:** hello@pdataskforce.com
**Project:** PDA Platform
**Version:** 0.3.0

---

**Last Updated:** January 2026
**Version:** 0.3.0
