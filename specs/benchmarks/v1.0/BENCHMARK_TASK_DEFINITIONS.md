# Benchmark Task Definitions v1.0

Evaluation tasks for assessing AI capabilities in project management.

## Overview

This specification defines five benchmark tasks for evaluating AI systems working with project management data. Developed by members of the PDA Task Force to support the NISTA Programme and Project Data Standard trial.

## Tasks

### 1. Task Extraction

**Goal:** Extract structured tasks from natural language project descriptions.

**Input:** Free-form text describing project scope and activities

**Output:** List of tasks with:
- Task name
- Description
- Estimated duration
- Dependencies (if mentioned)

**Evaluation Metrics:**
- Precision: Percentage of extracted tasks that are valid
- Recall: Percentage of actual tasks successfully extracted
- F1 Score: Harmonic mean of precision and recall

**Example:**
```
Input: "We need to design the foundation, get permits, then excavate and pour concrete."
Output:
- Task 1: Design foundation
- Task 2: Obtain permits (depends on Task 1)
- Task 3: Excavate site (depends on Task 2)
- Task 4: Pour concrete (depends on Task 3)
```

### 2. Dependency Inference

**Goal:** Infer logical task dependencies from context.

**Input:** List of tasks with descriptions

**Output:** Dependency graph with relationship types (FS, SS, FF, SF)

**Evaluation Metrics:**
- Dependency accuracy: Percentage of correct dependencies
- Over-linking: Percentage of unnecessary dependencies
- Under-linking: Percentage of missing dependencies

**Example:**
```
Input:
- Design system architecture
- Write code
- Write tests
- Deploy to production

Output:
- Write code depends on Design system architecture (FS)
- Write tests depends on Write code (FS)
- Deploy to production depends on Write tests (FS)
```

### 3. Risk Identification

**Goal:** Identify project risks from schedule and resource data.

**Input:** Project data (tasks, resources, schedule)

**Output:** List of risks with:
- Risk description
- Probability (0-1)
- Impact (0-1)
- Affected tasks

**Evaluation Metrics:**
- Risk detection rate: Percentage of known risks identified
- False positive rate: Percentage of flagged non-risks
- Risk ranking accuracy: Correlation with expert rankings

**Example Risks:**
- Resource over-allocation
- Missing dependencies
- Unrealistic durations
- Critical path bottlenecks

### 4. Schedule Optimization

**Goal:** Optimize project schedule to minimize duration or cost.

**Input:** Project with tasks, dependencies, resources, and constraints

**Output:** Optimized schedule with:
- Task start/finish dates
- Resource assignments
- Critical path
- Schedule rationale

**Evaluation Metrics:**
- Schedule duration reduction
- Resource utilization improvement
- Constraint satisfaction
- Solution feasibility

**Constraints:**
- Resource availability
- Task dependencies
- Calendar exceptions
- Budget limits

### 5. NISTA Compliance Validation

**Goal:** Validate project data against NISTA requirements.

**Input:** Project data in any format

**Output:** Compliance report with:
- Compliance status (pass/fail)
- Missing required fields
- Invalid values
- Recommendations

**Evaluation Metrics:**
- Validation accuracy: Percentage of issues correctly identified
- False negative rate: Percentage of issues missed
- Report clarity: Usefulness of recommendations

**NISTA Requirements:**
- Required fields present
- Date formats correct
- WBS structure valid
- Dependency graph acyclic

## Dataset

Benchmark datasets include:
- 10 synthetic projects (small, medium, large)
- 5 real-world anonymized projects
- Ground truth annotations from domain experts

## Usage

```python
from pm_mcp_servers.benchmark import run_benchmark

# Run all tasks
results = run_benchmark(
    tasks=["task_extraction", "dependency_inference", "risk_identification",
           "schedule_optimization", "nista_compliance"],
    model="claude-3-opus"
)

# View results
print(f"Average F1: {results.average_f1}")
print(f"Task scores: {results.task_scores}")
```

## Authors

Members of the PDA Task Force

## Acknowledgments

These benchmarks support the NISTA Programme and Project Data Standard trial and address AI implementation barriers identified in the PDA Task Force White Paper.

## Version History

- **1.0.0** (2026-01-02) - Initial task definitions
