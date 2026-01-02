"""Fixtures for mining tests."""

import pytest


class MockProvider:
    """Mock provider for testing."""

    def __init__(self, responses: list[str]):
        self.responses = responses
        self.call_count = 0
        self._name = "mock"

    async def complete(self, **kwargs) -> dict:
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return {
            "content": response,
            "tokens_used": 100,
            "cost_usd": 0.001,
        }

    @property
    def name(self) -> str:
        return self._name


@pytest.fixture
def mock_provider_diverse():
    """Provider returning diverse responses."""
    responses = [
        '[{"description": "Timeline risk from supplier dependency", "category": "Schedule", "probability": 3, "impact": 4}]',
        '[{"description": "Budget overrun from scope creep", "category": "Commercial", "probability": 4, "impact": 3}]',
        '[{"description": "Technical debt from legacy integration", "category": "Technical", "probability": 3, "impact": 3}]',
        '[{"description": "Resource availability during holidays", "category": "Resource", "probability": 2, "impact": 3}]',
        '[{"description": "Regulatory compliance gap", "category": "External", "probability": 2, "impact": 5}]',
    ] * 10  # Repeat for multiple samples
    return MockProvider(responses)


@pytest.fixture
def mock_provider_convergent():
    """Provider returning similar responses (low diversity)."""
    response = '[{"description": "Timeline risk", "category": "Schedule", "probability": 3, "impact": 4}]'
    return MockProvider([response] * 50)


@pytest.fixture
def project_context():
    """Sample project context for testing."""
    return """
    Project: System Upgrade
    Budget: £1M
    Timeline: 6 months

    Key risks identified in planning:
    - Resource availability
    - Technical complexity
    - Stakeholder alignment
    """
