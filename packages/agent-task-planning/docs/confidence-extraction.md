# Confidence Extraction

Confidence extraction provides reliable, uncertainty-aware data extraction from LLM responses using self-consistency techniques.

## Overview

When asking an LLM to extract structured data (risks, estimates, recommendations), a single response may be:
- Correct and confident
- Correct but lucky
- A hallucination that sounds confident
- An outlier that a different query wouldn't produce

Confidence extraction addresses this by:
1. Querying the same model multiple times (default: 5 samples)
2. Extracting structured data from each response
3. Aggregating results statistically (median for numbers, mode for categories)
4. Detecting outliers using IQR
5. Computing a confidence score based on agreement
6. Recommending appropriate human review levels

## Quick Start

```python
from agent_planning import ConfidenceExtractor, SchemaType
from agent_planning.providers import AnthropicProvider

provider = AnthropicProvider(api_key="your-key")
extractor = ConfidenceExtractor(provider)

result = await extractor.extract(
    query="What are the top 3 risks for this project?",
    context=project_document,
    schema=SchemaType.RISK,
)

print(f"Confidence: {result.confidence:.2%}")
print(f"Review recommended: {result.review_level.value}")
```

## Configuration

Confidence settings are part of `GuardrailConfig`:

```python
from agent_planning.guardrails import GuardrailConfig

guardrails = GuardrailConfig(
    confidence_samples=5,              # Number of samples to take
    confidence_temperature=0.7,        # Sampling temperature
    confidence_early_stop_threshold=0.6,  # Stop if 60% agree
)

extractor = ConfidenceExtractor(provider, guardrails)
```

## Built-in Schemas

| Schema | Use Case |
|--------|----------|
| `SchemaType.RISK` | Risk identification and assessment |
| `SchemaType.ESTIMATE` | Effort, cost, duration estimates |
| `SchemaType.RECOMMENDATION` | Recommended actions |
| `SchemaType.MILESTONE` | Project milestones |
| `SchemaType.BARRIER` | Barriers and blockers |
| `SchemaType.OUTCOME_MEASURE` | KPIs and success metrics |
| `SchemaType.STAKEHOLDER_IMPACT` | Stakeholder analysis |

## Review Levels

Based on confidence and outliers, the system recommends review levels:

| Level | Confidence | Meaning |
|-------|------------|---------|
| `NONE` | >= 80% | High confidence, no review needed |
| `SPOT_CHECK` | 60-80% | Quick verification recommended |
| `DETAILED_REVIEW` | 40-60% | Careful review needed |
| `EXPERT_REQUIRED` | < 40% or outliers | Expert review required |

## Custom Schemas

```python
from agent_planning.confidence import CustomSchema

my_schema = CustomSchema(
    name="Competitor Analysis",
    extraction_prompt="Extract competitors with: name, threat_level (High/Medium/Low), market_share (decimal)",
    aggregation_fields={
        "categorical": ["threat_level"],
        "numeric": ["market_share"],
        "text": ["name"],
    }
)

result = await extractor.extract(query, schema=my_schema)
```

## Batch Processing

```python
result = await extractor.extract_batch(
    queries=["Risk analysis", "Effort estimate", "Recommendations"],
    schemas=[SchemaType.RISK, SchemaType.ESTIMATE, SchemaType.RECOMMENDATION],
    max_concurrent=3,
)

print(f"Total cost: ${result.total_cost_usd:.4f}")
```

## Cost Optimisation

Early stopping reduces costs by ~40% when samples agree:

```python
result = await extractor.extract(query, early_stop=True)

print(f"Samples used: {result.samples_used}/{result.samples_requested}")
print(f"Cost saved: ${result.cost_saved_usd:.4f}")
```

## API Reference

### ConfidenceExtractor

Main extraction class that coordinates the confidence extraction process.

**Methods:**
- `extract(query, context, schema, samples, temperature, early_stop)` - Extract with confidence scoring
- `extract_batch(queries, context, schemas, max_concurrent, progress_callback)` - Batch extraction

### ConfidenceResult

Result object containing:
- `consensus` - Aggregated structured output
- `confidence` - Overall confidence score (0.0-1.0)
- `field_confidence` - Per-field confidence scores
- `outliers` - List of detected outliers
- `review_level` - Recommended review level
- `cost_usd` - Total API cost
- `samples_used` - Number of samples collected

### SchemaType

Enumeration of built-in schema types for common PM extractions.

### CustomSchema

Define custom extraction schemas with your own prompts and aggregation rules.

## Research Background

This implementation is based on academic research showing:
- Self-consistency with a single strong model outperforms multi-model ensembles
- +3-23% accuracy improvements on reasoning tasks via majority voting
- 40% cost reduction via confidence-informed early stopping
- Verbalized confidence is unreliable; use agreement rate instead

## Examples

See the `examples/` directory for complete working examples:
- `05_basic_confidence.py` - Simple risk extraction
- `06_pm_extraction.py` - Multiple schema types
- `07_batch_confidence.py` - Batch processing
- `08_custom_schema.py` - Custom schema definition

## Testing

Run the test suite:

```bash
pytest tests/test_confidence/
```

## Limitations

- Assumes structured extraction is possible (not suitable for all tasks)
- Requires 5x the API calls of single extraction (mitigated by early stopping)
- Confidence measures agreement, not correctness
- Best suited for tasks with objective answers

## Acknowledgement

This feature was shaped by suggestions from [Lawrence Rowland](https://github.com/lawrencerowland), including multi-sample queries with median answer identification, outlier detection, and sign-off regimes with verification levels.
