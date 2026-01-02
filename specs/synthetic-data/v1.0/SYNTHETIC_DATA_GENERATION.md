# Synthetic Data Generation v1.0

Privacy-preserving project data generation for testing and development.

## Overview

This specification defines methods for generating realistic synthetic project management data. Developed by members of the PDA Task Force to enable AI development without exposing sensitive project information.

## Motivation

Real project data often contains:
- Commercially sensitive information
- Personal data (resource names, rates)
- Confidential schedules and budgets

Synthetic data enables:
- Safe model training and testing
- Public benchmarking
- Tool development without data access restrictions

## Generation Methods

### 1. Template-Based Generation

Generate projects from predefined templates.

**Templates:**
- Software development projects
- Construction projects
- Infrastructure projects
- Event planning projects

**Parameters:**
- Project size (small/medium/large)
- Complexity (simple/medium/complex)
- Duration (weeks/months/years)

**Example:**
```python
from pm_data_tools.synthetic import generate_from_template

project = generate_from_template(
    template="software",
    size="medium",
    complexity="complex",
    duration_weeks=24
)
```

### 2. Statistical Generation

Generate based on statistical properties of real data.

**Distributions:**
- Task duration: Log-normal distribution
- Resource costs: Normal distribution
- Dependency density: Poisson distribution
- WBS depth: Geometric distribution

**Constraints:**
- Valid dependency graphs (acyclic)
- Resource allocation within bounds
- Schedule feasibility

**Example:**
```python
from pm_data_tools.synthetic import generate_statistical

project = generate_statistical(
    num_tasks=50,
    avg_duration=5.0,
    dependency_density=0.3,
    num_resources=10
)
```

### 3. LLM-Assisted Generation

Use large language models to generate realistic project narratives.

**Process:**
1. Generate project description from prompt
2. Extract tasks and structure
3. Infer dependencies
4. Populate with realistic data

**Example:**
```python
from pm_data_tools.synthetic import generate_llm

project = generate_llm(
    prompt="A 6-month website redesign project for a government agency",
    model="claude-3-opus"
)
```

### 4. Real Data Anonymization

Transform real data while preserving structure.

**Transformations:**
- Replace names with fictional names
- Scale dates relative to fixed start
- Perturb costs by random factor
- Generalize location data

**Privacy Guarantees:**
- k-anonymity for resources
- Differential privacy for costs
- No re-identification possible

**Example:**
```python
from pm_data_tools.synthetic import anonymize_project

anon_project = anonymize_project(
    real_project,
    k=5,
    epsilon=0.1
)
```

## Data Quality

Generated data must satisfy:

### Structural Validity
- WBS codes are hierarchical
- Dependency graph is acyclic
- Assignments reference valid tasks and resources
- Dates respect dependencies

### Semantic Realism
- Task durations are plausible
- Resource rates are market-appropriate
- Project timelines are realistic
- Risk probabilities are reasonable

### Statistical Fidelity
- Distributions match real-world patterns
- Correlations preserved (e.g., cost-duration)
- Outliers occur at realistic rates

## Validation

All synthetic data passes:
1. Schema validation (canonical model)
2. Structural validation (dependencies, WBS)
3. Realism checks (duration ranges, cost ranges)
4. NISTA compliance (if applicable)

## Usage Example

```python
from pm_data_tools.synthetic import SyntheticGenerator

# Create generator
gen = SyntheticGenerator(seed=42)

# Generate 100 projects
projects = gen.generate_batch(
    count=100,
    method="template",
    templates=["software", "construction"],
    size_distribution={"small": 0.3, "medium": 0.5, "large": 0.2}
)

# Export for benchmarking
gen.export(projects, format="nista", path="synthetic_dataset/")
```

## Dataset Releases

The PDA Platform includes:
- **dev-set**: 10 small projects for quick testing
- **test-set**: 100 diverse projects for evaluation
- **benchmark-set**: 500 projects with ground truth annotations

All datasets are MIT-licensed and freely available.

## Authors

Members of the PDA Task Force

## Acknowledgments

This specification supports the NISTA Programme and Project Data Standard trial and enables safe AI development without exposing sensitive project data.

## Version History

- **1.0.0** (2026-01-02) - Initial specification
