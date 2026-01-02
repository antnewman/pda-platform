# Sample Queries for PM MCP Servers

Example queries you can ask Claude when using PM MCP Servers.

## Loading Projects

```
Load the Microsoft Project file at /projects/website-redesign.mpp

Load project.xml as a Primavera P6 XER file

Parse the Monday.com board from monday_export.json

Load the GMPP data from government_projects.csv

Import the NISTA submission file nista_2026_q1.json
```

## Project Summaries

```
Give me a high-level summary of this project

What's the overall project status?

How many tasks are on the critical path?

When is this project scheduled to finish?

What percentage of the project is complete?
```

## Task Queries

```
Show me all milestone tasks

List all tasks that are behind schedule

What tasks are assigned to John Smith?

Show me critical path tasks with less than 50% progress

Find all tasks starting in March 2026

Which tasks have zero float?
```

## Critical Path Analysis

```
What's the critical path for this project?

Show me tasks that are near-critical (within 5 days float)

How long is the critical path in days?

What happens if "Foundation Pour" is delayed by 2 weeks?

Which critical tasks are behind schedule?
```

## Dependency Analysis

```
What tasks depend on "Design Approval"?

Show me all predecessors for "Testing Phase"

What's the dependency chain from start to finish?

Find circular dependencies in this project

Which tasks have the most successors?
```

## Resource Analysis

```
Who is assigned to critical path tasks?

What resources are over-allocated?

Show me John's task assignments

Which tasks have no resources assigned?

What's the resource loading for March 2026?
```

## Format Conversion

```
Convert this project to NISTA JSON format

Export this as an MS Project XML file

Create a NISTA CSV for government reporting

Convert P6 data to Monday.com format

Generate a GMPP-compliant export
```

## Comparison & Analysis

```
Compare the baseline schedule to the current schedule

What's changed since the last update?

Show me variance between planned and actual dates

Which tasks have slipped more than 10 days?

Compare resource allocation across phases
```

## Risk Identification

```
What are the biggest schedule risks?

Identify tasks with high float consumption

Which milestones are at risk?

Show me tasks with many dependencies

Find tasks on multiple critical paths
```

## Filtering & Sorting

```
Show me the 10 longest tasks

List tasks by percent complete (ascending)

Find tasks with duration > 30 days

Show only in-progress tasks

Filter tasks by department or category
```

## Multi-Project Queries

```
Load all projects in /projects/ folder

Compare critical paths across projects

Which project has the most schedule risk?

Aggregate task counts across all projects

Show resource utilization across portfolio
```

## Validation Queries (pm-validate server)

```
Validate this project against NISTA standards

Check for structural integrity issues

Verify all tasks have valid dates

Ensure dependencies are logically correct

Validate GMPP compliance
```

## Analysis Queries (pm-analyse server)

```
Forecast the project completion date

Identify anomalies in the schedule

Assess overall schedule health

Generate alternative scenarios for delay recovery

Predict which tasks will miss their deadlines
```

## Complex Workflows

### Workflow 1: Critical Path Deep Dive
```
1. Load project.mpp
2. Show me the critical path
3. For each critical task, show dependencies
4. Identify which critical tasks are behind schedule
5. Generate a recovery plan
```

### Workflow 2: NISTA Compliance
```
1. Load gmpp_data.csv
2. Validate NISTA compliance
3. Identify missing required fields
4. Convert to NISTA JSON format
5. Verify the export validates successfully
```

### Workflow 3: Schedule Risk Assessment
```
1. Load construction_project.xml
2. Get critical path with near-critical tasks
3. Show tasks with high dependency counts
4. Identify float consumption patterns
5. Recommend risk mitigation actions
```

### Workflow 4: Format Migration
```
1. Load legacy_project.mpp (MS Project)
2. Validate data integrity
3. Convert to modern NISTA format
4. Verify all data preserved
5. Export for government submission
```

## Natural Language Variations

Claude understands variations:

**Instead of:** "Show me critical path tasks"

**Try:**
- "What's on the critical path?"
- "Which tasks are critical?"
- "Show me tasks with zero float"
- "What determines the project end date?"

**Instead of:** "Load /path/to/file.mpp"

**Try:**
- "Import the project at /path/to/file.mpp"
- "Parse this MS Project file: /path/to/file.mpp"
- "Open /path/to/file.mpp and analyze it"

## Tips for Effective Queries

1. **Be Specific:** "Show me critical tasks in Phase 2" vs "Show me tasks"
2. **Use Context:** "For the project we just loaded..." (Claude remembers)
3. **Chain Operations:** "Load X, then analyze Y, then export as Z"
4. **Ask for Explanations:** "Why is this task critical?"
5. **Request Formats:** "Show as a table" or "Give me JSON output"

## Error Recovery

If a query fails:

```
You: Load /wrong/path.mpp
Claude: Error: File not found

You: Load /correct/path.mpp
Claude: ✓ Project loaded successfully
```

## Session Management

Projects persist in session:

```
You: Load project_a.mpp
Claude: ✓ Loaded as project_123

You: Load project_b.mpp
Claude: ✓ Loaded as project_456

You: Compare project_123 and project_456 critical paths
Claude: [Compares both projects still in memory]
```

## Next Steps

Try these queries with your own project data and see what insights Claude can provide!
