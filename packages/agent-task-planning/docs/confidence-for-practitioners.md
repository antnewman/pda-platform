# Confidence Extraction for Project Professionals

A practical guide to using confidence extraction for project management decisions.

## Why This Matters

When you ask an AI to analyse project risks, estimate effort, or recommend actions, how do you know if the answer is reliable?

A single AI response might be:
- Spot on
- Reasonable but incomplete
- Confidently wrong

Confidence extraction helps you know the difference by asking the AI the same question multiple times and measuring how consistent its answers are.

**High agreement = higher confidence that the answer is reliable**

**Low agreement = flag for human review**

## When to Use It

Use confidence extraction for high-stakes project decisions:

✅ **Good candidates:**
- Risk assessments going to steering committee
- Effort estimates for business cases
- Recommendations that will influence resource allocation
- Analysis that will be cited in formal reports

❌ **Probably overkill for:**
- Quick informal queries
- Exploratory analysis
- Low-stakes internal notes

## Understanding the Output

### Confidence Score (0-100%)

| Score | Interpretation |
|-------|----------------|
| 80%+ | High confidence - samples strongly agree |
| 60-80% | Good confidence - minor variations |
| 40-60% | Moderate - some disagreement, review recommended |
| Below 40% | Low confidence - significant disagreement |

### Review Levels

The system recommends appropriate review based on confidence:

- **None**: High confidence, safe to use as-is
- **Spot check**: Quick glance recommended
- **Detailed review**: Careful examination needed
- **Expert required**: Significant uncertainty, get specialist input

### Outliers

When one response differs significantly from others, it's flagged as an outlier. This might indicate:
- A valid alternative perspective worth considering
- An error in that particular response
- Ambiguity in the source material

Always review outliers - they often surface important edge cases.

## Practical Example

**Scenario:** Extracting risks from a project initiation document for a steering committee briefing.

```
Query: "What are the top 5 risks for this project?"

Result:
- Confidence: 72%
- Review level: Spot check
- 5 risks extracted
- 1 outlier flagged (probability score)

Field confidence:
- Risk descriptions: 85% (strong agreement)
- Categories: 90% (very consistent)
- Probability scores: 55% (some variation)
- Impact scores: 78% (good agreement)
```

**Interpretation:** The risk descriptions and categories are reliable. The probability scores show more variation - worth a quick review to ensure they make sense for your context.

## Integration with Sign-off Processes

Confidence extraction supports formal sign-off regimes:

1. **Define verification levels** for different decision types
2. **Use review recommendations** to guide verification effort
3. **Document the confidence scores** in your evidence pack
4. **Flag outliers** for explicit consideration

Example policy alignment:
- Steering committee papers: require 70%+ confidence or documented review
- Business cases: all estimates must include confidence scores
- Risk registers: outliers must be explicitly addressed

## Cost Considerations

Confidence extraction uses 5 samples by default. This means ~5x the API cost of a single query.

**When it's worth it:**
- Decisions with significant financial/schedule/reputation impact
- Analysis that will be formally cited
- Situations where getting it wrong is expensive

**Cost optimisation:**
- Early stopping reduces costs by ~40% when samples agree quickly
- Use single queries for exploratory work, confidence extraction for final analysis

## Common Questions

**Q: Does higher confidence mean the answer is correct?**

A: Higher confidence means the AI is consistent. Consistency doesn't guarantee correctness, but inconsistency is a strong signal to verify.

**Q: What if I get low confidence?**

A: Low confidence is valuable information. It tells you this is an area of uncertainty that needs human judgement.

**Q: Can I use this for all my PM work?**

A: Use it selectively for high-stakes analysis. For routine queries, standard single responses are fine.

## Getting Started

1. Identify a high-stakes analysis task (e.g., risk assessment for upcoming gate review)
2. Run confidence extraction on your source document
3. Review the confidence scores and outliers
4. Use the review level recommendation to guide your verification effort
5. Document the confidence scores in your deliverable

## Example Workflow

### Project Risk Assessment

```python
from agent_planning import ConfidenceExtractor, SchemaType
from agent_planning.providers import AnthropicProvider

# Setup
provider = AnthropicProvider(api_key="your-key")
extractor = ConfidenceExtractor(provider)

# Extract risks from project document
result = await extractor.extract(
    query="Identify the top 5 project risks",
    context=project_document,
    schema=SchemaType.RISK,
)

# Review results
print(f"Confidence: {result.confidence:.0%}")
print(f"Review needed: {result.review_level.value}")

if result.outliers:
    print(f"⚠️ {len(result.outliers)} outliers detected - review required")

# Export for steering committee paper
risks_for_report = result.consensus
```

## Best Practices

1. **Use appropriate schemas** - Choose the schema that matches your extraction task
2. **Provide good context** - More context = better extraction quality
3. **Review outliers first** - They often highlight important edge cases
4. **Document confidence scores** - Include them in your deliverables for transparency
5. **Calibrate thresholds** - Adjust review thresholds based on your organisation's risk appetite

## Support

For technical documentation, see [confidence-extraction.md](confidence-extraction.md).

This capability was developed by Members of the PDA Task Force for the PDA Task Force as part of the agent-task-planning toolkit.

## Acknowledgement

This feature was shaped by suggestions from [Lawrence Rowland](https://github.com/lawrencerowland).
