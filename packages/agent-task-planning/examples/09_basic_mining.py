"""Basic outlier mining example."""

import asyncio
import os
from agent_planning.mining import OutlierMiner, MiningConfig
from agent_planning.confidence import SchemaType
from agent_planning.providers import AnthropicProvider


async def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Please set ANTHROPIC_API_KEY environment variable")
        return

    provider = AnthropicProvider(api_key=api_key)

    config = MiningConfig(
        samples=20,
        novelty_weight=0.5,
        coherence_weight=0.3,
        coverage_weight=0.2,
    )

    miner = OutlierMiner(provider, config)

    result = await miner.mine(
        query="What are approaches to reduce this project's timeline by 25%?",
        schema=SchemaType.RECOMMENDATION,
    )

    print(f"Found {len(result.candidates)} distinct approaches")
    print(f"Diversity score: {result.diversity_score:.2f}")
    print(f"Quality pass rate: {result.quality_pass_rate:.1%}")

    print("\nTop candidates:")
    for i, candidate in enumerate(result.candidates[:3], 1):
        print(f"\n{i}. {candidate.approach_summary}")
        print(f"   Novelty: {candidate.novelty_score:.2f}")
        print(f"   Coherence: {candidate.coherence_score:.2f}")
        print(f"   Coverage: {candidate.coverage_score:.2f}")
        print(f"   Composite: {candidate.composite_score:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
