"""Custom schema definition example."""

import asyncio
import os
from dataclasses import dataclass
from agent_planning.confidence import (
    ConfidenceExtractor,
    CustomSchema,
)
from agent_planning.providers import AnthropicProvider


# Define a custom data class (optional, for type hints)
@dataclass
class CompetitorItem:
    """Competitor information."""
    name: str
    strengths: list[str]
    weaknesses: list[str]
    threat_level: str  # High, Medium, Low
    market_share: float


# Define custom schema
COMPETITOR_SCHEMA = CustomSchema(
    name="Competitor Analysis",
    extraction_prompt="""Extract competitor information with these fields:
- name: Competitor company name
- strengths: List of key strengths
- weaknesses: List of key weaknesses
- threat_level: High, Medium, or Low
- market_share: Estimated market share as decimal (e.g., 0.15 for 15%)

Return as a JSON array of competitor objects.""",
    aggregation_fields={
        "categorical": ["threat_level"],
        "numeric": ["market_share"],
        "text": ["name"],
        "list": ["strengths", "weaknesses"],
    },
    output_class=CompetitorItem,  # Optional
)


async def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Please set ANTHROPIC_API_KEY environment variable")
        return

    provider = AnthropicProvider(api_key=api_key)
    extractor = ConfidenceExtractor(provider)

    result = await extractor.extract(
        query="Who are the main competitors in the UK cloud infrastructure market?",
        schema=COMPETITOR_SCHEMA,
    )

    print(f"Confidence: {result.confidence:.2%}")
    print(f"Competitors found: {len(result.consensus.get('items', []))}")

    print("\nField confidence:")
    for field, conf in result.field_confidence.items():
        print(f"  {field}: {conf:.2%}")

    print("\nConsensus data:")
    for key, value in result.consensus.items():
        if isinstance(value, list) and value:
            print(f"\n{key}:")
            for item in value[:3]:  # Show first 3 items
                print(f"  {item}")
        else:
            print(f"{key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
