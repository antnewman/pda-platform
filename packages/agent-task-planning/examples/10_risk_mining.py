"""Mining for non-obvious risks."""

import asyncio
import os
from agent_planning.mining import OutlierMiner, MiningConfig
from agent_planning.confidence import SchemaType
from agent_planning.providers import AnthropicProvider


PROJECT_CONTEXT = """
Project: Cloud Migration Programme
Budget: £5.2M
Timeline: 18 months
Scope: Migrate 47 applications from on-premise data centres to AWS

Current status: Planning complete, entering execution phase.
Team: 12 internal staff + external implementation partner (Acme Cloud Services)
Key stakeholders: CTO (sponsor), Finance Director, Operations Director

Technical approach:
- Lift-and-shift for 30 applications
- Re-platform for 12 applications
- Re-architect for 5 business-critical applications
"""


async def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Please set ANTHROPIC_API_KEY environment variable")
        return

    provider = AnthropicProvider(api_key=api_key)

    config = MiningConfig(
        samples=30,
        novelty_weight=0.6,  # Prioritise finding unusual risks
        coherence_weight=0.25,
        coverage_weight=0.15,
        characterise_clusters=True,
        extract_assumptions=True,
    )

    miner = OutlierMiner(provider, config)

    result = await miner.mine(
        query="What risks might affect this programme that are not immediately obvious?",
        context=PROJECT_CONTEXT,
        schema=SchemaType.RISK,
    )

    print(f"Generated {result.samples_generated} samples")
    print(f"Quality pass rate: {result.quality_pass_rate:.1%}")
    print(f"Found {result.num_clusters} distinct risk perspectives")
    print(f"Silhouette score: {result.silhouette_score:.2f}")

    # High novelty risks
    novel = [c for c in result.candidates if c.novelty_score > 0.7]
    print(f"\n{len(novel)} highly novel risks found:")

    for candidate in novel:
        print(f"\n• {candidate.approach_summary}")
        print(f"  Novelty: {candidate.novelty_score:.2f}")
        print(f"  Coherence: {candidate.coherence_score:.2f}")

    # Cluster overview
    print("\n\nCluster summaries:")
    for cluster in result.clusters:
        print(f"  [{cluster.cluster_id}] ({cluster.size} samples): {cluster.summary}")

    # Potential hallucinations
    if result.potential_hallucinations:
        print(f"\n⚠️  {len(result.potential_hallucinations)} candidates flagged for high entropy (review carefully)")


if __name__ == "__main__":
    asyncio.run(main())
