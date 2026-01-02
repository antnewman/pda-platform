"""Basic confidence extraction example."""

import asyncio
import os
from agent_planning import ConfidenceExtractor, SchemaType
from agent_planning.providers import AnthropicProvider
from agent_planning.guardrails import GuardrailConfig


async def main():
    # Setup
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Please set ANTHROPIC_API_KEY environment variable")
        return

    provider = AnthropicProvider(api_key=api_key)
    guardrails = GuardrailConfig(
        confidence_samples=5,
        confidence_temperature=0.7,
    )

    extractor = ConfidenceExtractor(provider, guardrails)

    # Simple risk extraction
    result = await extractor.extract(
        query="What are the main risks for a software migration project?",
        schema=SchemaType.RISK,
    )

    # Display results
    print(f"Confidence: {result.confidence:.2%}")
    print(f"Review level: {result.review_level.value}")
    print(f"Samples used: {result.samples_used}/{result.samples_requested}")
    print(f"Early stopped: {result.early_stopped}")
    print(f"Cost: ${result.cost_usd:.4f} (saved ${result.cost_saved_usd:.4f})")

    print("\nConsensus:")
    for key, value in result.consensus.items():
        print(f"  {key}: {value}")

    if result.outliers:
        print("\nOutliers detected:")
        for outlier in result.outliers:
            print(f"  {outlier.field}: {outlier.reason}")

    print("\nField confidence:")
    for field, conf in result.field_confidence.items():
        print(f"  {field}: {conf:.2%}")


if __name__ == "__main__":
    asyncio.run(main())
