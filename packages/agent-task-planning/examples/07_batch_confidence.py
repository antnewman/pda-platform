"""Batch extraction example."""

import asyncio
import os
from agent_planning.confidence import (
    ConfidenceExtractor,
    SchemaType,
    confidence_extract_batch,
)
from agent_planning.providers import AnthropicProvider


CONTEXT = """
Project: Digital Transformation Initiative
Budget: £5M over 2 years
Team: 15 FTE across 3 workstreams

The initiative aims to modernise legacy systems, improve customer experience,
and enable data-driven decision making. Key workstreams include:

1. Customer Portal Redesign - New self-service capabilities
2. Data Platform Migration - Move to cloud-based analytics
3. Process Automation - RPA for routine tasks

Current challenges:
- Stakeholder alignment on priorities
- Skills gaps in cloud technologies
- Integration complexity with existing systems
- Change management across 500+ staff
"""

QUERIES = [
    "What are the key risks?",
    "What are the effort estimates for each phase?",
    "What recommendations do you have for the steering committee?",
    "What are the key milestones?",
    "What barriers might prevent success?",
]

SCHEMAS = [
    SchemaType.RISK,
    SchemaType.ESTIMATE,
    SchemaType.RECOMMENDATION,
    SchemaType.MILESTONE,
    SchemaType.BARRIER,
]


async def progress(completed: int, total: int):
    """Progress callback for batch extraction."""
    print(f"Progress: {completed}/{total} queries complete")


async def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Please set ANTHROPIC_API_KEY environment variable")
        return

    provider = AnthropicProvider(api_key=api_key)

    print("Starting batch extraction...")

    result = await confidence_extract_batch(
        queries=QUERIES,
        provider=provider,
        context=CONTEXT,
        schemas=SCHEMAS,
        max_concurrent=2,
        progress_callback=progress,
    )

    print(f"\nBatch complete!")
    print(f"Succeeded: {result.queries_succeeded}")
    print(f"Failed: {result.queries_failed}")
    print(f"Total cost: ${result.total_cost_usd:.4f}")
    print(f"Total tokens: {result.total_tokens:,}")

    print("\nResults by query:")
    for i, r in enumerate(result.results):
        print(f"\n{i+1}. {r.query[:50]}...")
        print(f"   Confidence: {r.confidence:.2%}")
        print(f"   Review: {r.review_level.value}")


if __name__ == "__main__":
    asyncio.run(main())
