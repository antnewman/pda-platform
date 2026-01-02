# Outlier Mining

Outlier mining discovers diverse approaches and novel insights by treating outliers as signal rather than noise.

## Consensus vs Mining

| Mode | Question | Outliers Are | Use When |
|------|----------|--------------|----------|
| **Consensus** | "What's the stable answer?" | Noise to filter | Need reliable answer |
| **Mining** | "What's the novel answer?" | Signal to mine | Need creative options |

## Overview

Traditional confidence extraction (consensus mode) filters out outliers to find the most reliable answer. Outlier mining does the opposite: it generates many diverse responses and mines them for breakthrough insights.

This is based on research showing that for hard problems with low success probability, generating many solutions (n=32) and mining for the best outperforms single-shot generation.

## Quick Start

```python
from agent_planning.mining import OutlierMiner, MiningConfig
from agent_planning.confidence import SchemaType
from agent_planning.providers import AnthropicProvider

# Setup
provider = AnthropicProvider(api_key="your-key")
config = MiningConfig(
    samples=32,              # Generate 32 diverse responses
    novelty_weight=0.6,      # Prioritise novel approaches
)

miner = OutlierMiner(provider, config)

# Mine for diverse approaches
result = await miner.mine(
    query="What non-obvious risks might affect this project?",
    context=project_document,
    schema=SchemaType.RISK,
)

# Review diverse candidates
for candidate in result.candidates:
    print(f"Novelty: {candidate.novelty_score:.2f}")
    print(f"Summary: {candidate.approach_summary}")
```

## How It Works

1. **Diverse Generation**: Generate many responses (default 32) using:
   - Temperature variation (0.7 → 1.0)
   - Role injection (cautious analyst, creative thinker, etc.)
   - Instruction variation

2. **Quality Filtering**: Remove low-quality responses while keeping valid outliers

3. **Clustering**: Group similar approaches using UMAP + HDBSCAN
   - Each cluster represents a distinct approach
   - Singleton clusters are true outliers

4. **Novelty Scoring**: Score each candidate on:
   - **Novelty** (0-1): How different from other candidates
   - **Coherence** (0-1): Internal consistency
   - **Coverage** (0-1): Addresses the query

5. **Ranking**: Return top candidates by composite score

## Configuration

```python
config = MiningConfig(
    # Sampling
    samples=32,                    # How many responses to generate
    temperature_start=0.7,         # Starting temperature
    temperature_end=1.0,           # Ending temperature

    # Quality
    quality_threshold=0.6,         # Minimum quality to include

    # Clustering
    hdbscan_min_cluster_size=2,    # Min samples per cluster
    allow_singleton_clusters=True,  # Include true outliers

    # Scoring weights
    novelty_weight=0.4,            # Weight for novelty
    coherence_weight=0.3,          # Weight for coherence
    coverage_weight=0.3,           # Weight for coverage
)
```

## When to Use Mining

**Use outlier mining when:**
- Need creative solutions to hard problems
- Want to discover non-obvious risks or opportunities
- Exploring alternative approaches
- Brainstorming or ideation
- Low cost of including a false positive

**Use consensus mode when:**
- Need reliable, stable answer
- High cost of being wrong
- Formal sign-off required
- Standard PM deliverables (risk register, estimates)

## Results Interpretation

### Diversity Score
- **High (>0.6)**: Found genuinely diverse approaches
- **Medium (0.3-0.6)**: Some variation
- **Low (<0.3)**: Responses converged (consider using consensus mode)

### Novelty Score (per candidate)
- **>0.7**: Highly novel - different from all others
- **0.4-0.7**: Moderately novel
- **<0.4**: Similar to other candidates

### Clusters
- **Many clusters**: Problem has multiple valid approaches
- **Few clusters**: Responses converged on common themes
- **Singleton clusters**: True outliers worth reviewing

## Dependencies

**Basic** (numpy + sentence-transformers):
```bash
pip install agent-task-planning[mining]
```

**Full** (adds UMAP + HDBSCAN for better clustering):
```bash
pip install agent-task-planning[mining-full]
```

Without UMAP/HDBSCAN, the system falls back to SVD + AgglomerativeClustering.

## Examples

See:
- `examples/09_basic_mining.py` - Simple mining example
- `examples/10_risk_mining.py` - Mining for non-obvious risks

## API Reference

### OutlierMiner

Main class for outlier mining operations.

**Methods:**
- `mine(query, context, schema)` - Mine for diverse approaches
- `mine_batch(queries, context, schemas, max_concurrent)` - Batch mining

### MiningResult

Result object containing:
- `candidates` - List of MiningCandidate objects (sorted by score)
- `num_clusters` - Number of distinct approaches found
- `diversity_score` - Overall diversity (0-1)
- `quality_pass_rate` - Fraction passing quality filter
- `silhouette_score` - Clustering quality metric

### MiningCandidate

Individual candidate with:
- `content` - Extracted structured content
- `novelty_score` - How different from others (0-1)
- `coherence_score` - Internal consistency (0-1)
- `coverage_score` - Coverage of query (0-1)
- `composite_score` - Weighted combination
- `cluster_id` - Which cluster this belongs to

## Research Background

Based on insights from:
- Codex n=32: For hard problems, generate many solutions and select best
- Self-consistency: Agreement across samples indicates reliability
- Min-p sampling: Better than top-p for diverse generation
- UMAP + HDBSCAN: State-of-art density-based clustering

## Limitations

- Requires ~32x more API calls than single generation
- Quality depends on prompt clarity and context
- Novelty ≠ correctness (review high-novelty candidates)
- Best for exploratory work, not formal deliverables

## Cost Management

Typical costs for 32 samples:
- With Claude Sonnet: ~$0.05-0.15 per query
- With GPT-4: ~$0.20-0.40 per query
- Reduce samples to 16-20 for lower cost

Use mining selectively for high-value exploratory analysis.

## Acknowledgement

This feature was shaped by suggestions from [Lawrence Rowland](https://github.com/lawrencerowland), including the outlier mining approach for hard problems (referencing the Codex n=32 pattern).
