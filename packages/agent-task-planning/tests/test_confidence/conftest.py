"""Fixtures for confidence extraction tests."""

import pytest
from dataclasses import dataclass
from typing import Any, Optional, List, Dict


@dataclass
class MockResponse:
    """Mock provider response."""
    content: str
    tokens_used: int = 100
    cost_usd: float = 0.001
    model: str = "mock-model"
    raw_response: Optional[dict] = None


class MockProvider:
    """Mock provider for testing."""

    def __init__(self, responses: list[str]):
        self.responses = responses
        self.call_count = 0
        self._name = "mock"

    async def complete(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> MockResponse:
        """Return mock response."""
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return MockResponse(
            content=response,
            tokens_used=100,
            cost_usd=0.001,
        )

    @property
    def name(self) -> str:
        """Provider name for logging."""
        return self._name


@pytest.fixture
def mock_provider_unanimous():
    """Provider that returns identical responses."""
    response = '''[
        {"description": "Data quality risk", "category": "Technical", "probability": 3, "impact": 4, "mitigation": "Data audit"}
    ]'''
    return MockProvider([response] * 5)


@pytest.fixture
def mock_provider_varied():
    """Provider that returns varied responses."""
    responses = [
        '[{"description": "Data risk", "category": "Technical", "probability": 3, "impact": 4, "mitigation": "Audit"}]',
        '[{"description": "Data risk", "category": "Technical", "probability": 3, "impact": 4, "mitigation": "Audit"}]',
        '[{"description": "Data risk", "category": "Technical", "probability": 3, "impact": 4, "mitigation": "Audit"}]',
        '[{"description": "Data risk", "category": "Technical", "probability": 4, "impact": 4, "mitigation": "Audit"}]',
        '[{"description": "Data risk", "category": "Technical", "probability": 5, "impact": 5, "mitigation": "Audit"}]',
    ]
    return MockProvider(responses)


@pytest.fixture
def mock_provider_outlier():
    """Provider with one clear outlier."""
    responses = [
        '[{"value": 15, "unit": "days"}]',
        '[{"value": 18, "unit": "days"}]',
        '[{"value": 16, "unit": "days"}]',
        '[{"value": 17, "unit": "days"}]',
        '[{"value": 100, "unit": "days"}]',  # Outlier
    ]
    return MockProvider(responses)


@pytest.fixture
def mock_provider_disagreement():
    """Provider with complete disagreement."""
    responses = [
        '[{"category": "Technical", "probability": 1}]',
        '[{"category": "Commercial", "probability": 2}]',
        '[{"category": "Schedule", "probability": 3}]',
        '[{"category": "Resource", "probability": 4}]',
        '[{"category": "External", "probability": 5}]',
    ]
    return MockProvider(responses)


@pytest.fixture
def whitepaper_context():
    """Sample context from PDATF whitepaper for realistic testing."""
    return """
    Project: AI Implementation Programme

    Barriers identified:
    1. Vision without business case - unclear ROI, cultural resistance
    2. Fragmented governance - patchwork of contracts and stakeholders
    3. Risk appetite and trust - forcing AI through conventional ICT gates
    4. Mis-aligned metrics - success not tied to outcome-based KPIs

    Recommended actions:
    - Develop one-page value case for each AI initiative
    - Establish evidence required at each project stage
    - Incorporate outcome measures into regular reviews
    - Consider retiring work that doesn't move agreed outcomes
    """
