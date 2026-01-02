"""Full PM extraction example with multiple schema types."""

import asyncio
import os
from agent_planning.confidence import (
    ConfidenceExtractor,
    SchemaType,
    ReviewLevel,
)
from agent_planning.providers import AnthropicProvider


PROJECT_CONTEXT = """
Project: Legacy System Migration
Duration: 18 months
Budget: £2.4M

The project involves migrating a 15-year-old ERP system to a modern cloud-based
platform. Key challenges include data migration from proprietary formats,
training 200+ users, and maintaining business continuity during transition.

Current status: Planning phase complete, entering execution.

Stakeholders: Finance department (primary users), IT operations, external
implementation partner, executive sponsor.

Known concerns:
- Data quality issues identified in source system
- Key SME retiring in 6 months
- Competing priority with regulatory compliance project
"""


async def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Please set ANTHROPIC_API_KEY environment variable")
        return

    provider = AnthropicProvider(api_key=api_key)
    extractor = ConfidenceExtractor(provider)

    # Extract risks
    print("=" * 60)
    print("RISK EXTRACTION")
    print("=" * 60)

    risk_result = await extractor.extract(
        query="Identify the top 5 risks for this project",
        context=PROJECT_CONTEXT,
        schema=SchemaType.RISK,
    )

    print(f"Confidence: {risk_result.confidence:.2%}")
    print(f"Review: {risk_result.review_level.value}")
    if risk_result.review_reason:
        print(f"Reason: {risk_result.review_reason}")
    print(f"\nExtracted {len(risk_result.consensus.get('items', []))} risks")

    # Extract estimates
    print("\n" + "=" * 60)
    print("ESTIMATE EXTRACTION")
    print("=" * 60)

    estimate_result = await extractor.extract(
        query="What are the effort estimates for key workstreams?",
        context=PROJECT_CONTEXT,
        schema=SchemaType.ESTIMATE,
    )

    print(f"Confidence: {estimate_result.confidence:.2%}")
    if estimate_result.outliers:
        print(f"Warning: {len(estimate_result.outliers)} outlier estimates detected")

    # Extract recommendations
    print("\n" + "=" * 60)
    print("RECOMMENDATION EXTRACTION")
    print("=" * 60)

    rec_result = await extractor.extract(
        query="What actions should the project manager prioritise?",
        context=PROJECT_CONTEXT,
        schema=SchemaType.RECOMMENDATION,
    )

    print(f"Confidence: {rec_result.confidence:.2%}")

    # Summary
    print("\n" + "=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)

    total_cost = risk_result.cost_usd + estimate_result.cost_usd + rec_result.cost_usd
    total_saved = risk_result.cost_saved_usd + estimate_result.cost_saved_usd + rec_result.cost_saved_usd

    print(f"Total cost: ${total_cost:.4f}")
    print(f"Cost saved via early stopping: ${total_saved:.4f}")

    # Review recommendations
    for name, result in [("Risks", risk_result), ("Estimates", estimate_result), ("Recommendations", rec_result)]:
        if result.review_level != ReviewLevel.NONE:
            print(f"\n⚠️  {name} require {result.review_level.value}: {result.review_reason}")


if __name__ == "__main__":
    asyncio.run(main())
