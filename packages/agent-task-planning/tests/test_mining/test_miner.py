"""Tests for OutlierMiner."""

import pytest
from agent_planning.mining import OutlierMiner, MiningConfig
from agent_planning.confidence import SchemaType


@pytest.mark.asyncio
async def test_basic_mining(mock_provider_diverse):
    """Test basic mining operation."""
    config = MiningConfig(samples=10)
    miner = OutlierMiner(mock_provider_diverse, config)

    result = await miner.mine(
        query="What are the project risks?",
        schema=SchemaType.RISK,
    )

    assert result.samples_generated > 0
    assert len(result.candidates) >= 0
    assert result.diversity_score >= 0


@pytest.mark.asyncio
async def test_mining_finds_diversity(mock_provider_diverse):
    """Test that mining finds diverse approaches."""
    config = MiningConfig(samples=20)
    miner = OutlierMiner(mock_provider_diverse, config)

    result = await miner.mine(
        query="What risks might affect this project?",
        schema=SchemaType.RISK,
    )

    # Should find multiple distinct approaches
    assert result.num_clusters >= 2
    assert result.diversity_score > 0.2


@pytest.mark.asyncio
async def test_convergent_responses_low_diversity(mock_provider_convergent):
    """Test that convergent responses show low diversity."""
    config = MiningConfig(samples=15)
    miner = OutlierMiner(mock_provider_convergent, config)

    result = await miner.mine(
        query="What are the risks?",
        schema=SchemaType.RISK,
    )

    # Should show low diversity
    assert result.num_clusters <= 2


@pytest.mark.asyncio
async def test_quality_filtering(mock_provider_diverse):
    """Test that quality filtering works."""
    config = MiningConfig(
        samples=10,
        quality_threshold=0.5,
    )
    miner = OutlierMiner(mock_provider_diverse, config)

    result = await miner.mine(
        query="What are the risks?",
        schema=SchemaType.RISK,
    )

    assert result.samples_passed_quality <= result.samples_generated
    assert result.quality_pass_rate >= 0


@pytest.mark.asyncio
async def test_candidates_have_scores(mock_provider_diverse):
    """Test that candidates have novelty/coherence/coverage scores."""
    config = MiningConfig(samples=15)
    miner = OutlierMiner(mock_provider_diverse, config)

    result = await miner.mine(
        query="What are the risks?",
        schema=SchemaType.RISK,
    )

    for candidate in result.candidates:
        assert 0 <= candidate.novelty_score <= 1
        assert 0 <= candidate.coherence_score <= 1
        assert 0 <= candidate.coverage_score <= 1
        assert 0 <= candidate.composite_score <= 1


@pytest.mark.asyncio
async def test_cost_tracking(mock_provider_diverse):
    """Test that costs are tracked."""
    config = MiningConfig(samples=10)
    miner = OutlierMiner(mock_provider_diverse, config)

    result = await miner.mine(
        query="Test query",
        schema=SchemaType.RISK,
    )

    assert result.cost_usd > 0
    assert result.tokens_used > 0
