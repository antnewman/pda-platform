"""Tests for confidence extractor."""

import pytest
from agent_planning.confidence import (
    ConfidenceExtractor,
    SchemaType,
    ReviewLevel,
)
from agent_planning.guardrails import GuardrailConfig


@pytest.mark.asyncio
async def test_unanimous_extraction_high_confidence(mock_provider_unanimous):
    """Test that unanimous responses produce high confidence."""
    extractor = ConfidenceExtractor(mock_provider_unanimous)

    result = await extractor.extract(
        query="What are the risks?",
        schema=SchemaType.RISK,
    )

    assert result.confidence >= 0.8
    assert result.review_level == ReviewLevel.NONE
    assert len(result.outliers) == 0
    assert result.samples_used <= 5


@pytest.mark.asyncio
async def test_early_stopping(mock_provider_unanimous):
    """Test that early stopping triggers on agreement."""
    guardrails = GuardrailConfig(
        confidence_samples=5,
        confidence_early_stop_threshold=0.6,
    )
    extractor = ConfidenceExtractor(mock_provider_unanimous, guardrails)

    result = await extractor.extract(
        query="What are the risks?",
        schema=SchemaType.RISK,
        early_stop=True,
    )

    # Should stop early since all responses are identical
    assert result.early_stopped
    assert result.samples_used < result.samples_requested
    assert result.cost_saved_usd > 0


@pytest.mark.asyncio
async def test_outlier_detection(mock_provider_outlier):
    """Test that outliers are detected."""
    extractor = ConfidenceExtractor(mock_provider_outlier)

    result = await extractor.extract(
        query="How long will this take?",
        schema=SchemaType.ESTIMATE,
        early_stop=False,  # Run all samples
    )

    assert len(result.outliers) > 0
    assert result.review_level in [ReviewLevel.EXPERT_REQUIRED, ReviewLevel.DETAILED_REVIEW]

    # Check that the outlier value (100) was flagged
    outlier_values = [o.outlier_value for o in result.outliers]
    assert 100 in outlier_values or 100.0 in outlier_values


@pytest.mark.asyncio
async def test_low_agreement_triggers_review(mock_provider_disagreement):
    """Test that disagreement triggers expert review."""
    extractor = ConfidenceExtractor(mock_provider_disagreement)

    result = await extractor.extract(
        query="What category is this risk?",
        schema=SchemaType.RISK,
        early_stop=False,
    )

    assert result.confidence < 0.5
    assert result.review_level == ReviewLevel.EXPERT_REQUIRED
    assert result.review_reason is not None


@pytest.mark.asyncio
async def test_varied_responses_moderate_confidence(mock_provider_varied):
    """Test that varied responses produce moderate confidence."""
    extractor = ConfidenceExtractor(mock_provider_varied)

    result = await extractor.extract(
        query="What are the risks?",
        schema=SchemaType.RISK,
        early_stop=False,
    )

    # Should have moderate confidence due to some variation
    assert 0.4 <= result.confidence <= 0.9


@pytest.mark.asyncio
async def test_batch_extraction(mock_provider_unanimous):
    """Test batch extraction."""
    extractor = ConfidenceExtractor(mock_provider_unanimous)

    result = await extractor.extract_batch(
        queries=["Risk 1?", "Risk 2?", "Risk 3?"],
        schemas=[SchemaType.RISK, SchemaType.RISK, SchemaType.RISK],
        max_concurrent=2,
    )

    assert result.queries_succeeded == 3
    assert result.queries_failed == 0
    assert len(result.results) == 3
    assert result.total_cost_usd > 0


@pytest.mark.asyncio
async def test_whitepaper_context_extraction(mock_provider_unanimous, whitepaper_context):
    """Test extraction with realistic whitepaper context."""
    extractor = ConfidenceExtractor(mock_provider_unanimous)

    result = await extractor.extract(
        query="What barriers are identified?",
        context=whitepaper_context,
        schema=SchemaType.BARRIER,
    )

    assert result.samples_used > 0
    assert result.consensus is not None


@pytest.mark.asyncio
async def test_cost_tracking(mock_provider_unanimous):
    """Test that costs are tracked correctly."""
    extractor = ConfidenceExtractor(mock_provider_unanimous)

    result = await extractor.extract(
        query="Test query",
        schema=SchemaType.RISK,
        early_stop=False,
    )

    # 5 samples * 0.001 per sample = 0.005
    assert result.cost_usd == pytest.approx(0.005, rel=0.1)
    assert result.tokens_used == 500  # 5 * 100
