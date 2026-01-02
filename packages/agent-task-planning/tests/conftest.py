"""Pytest configuration and fixtures."""

import pytest
from unittest.mock import AsyncMock

from agent_planning.core.state import TaskState
from agent_planning.core.task import Task, TaskStatus
from agent_planning.providers.base import BaseProvider, ProviderResponse


class MockProvider(BaseProvider):
    """Mock provider for testing."""

    def __init__(self, responses: list[str] | None = None):
        self.responses = responses or ["Test response"]
        self.call_count = 0
        self.calls: list[dict] = []

    @property
    def name(self) -> str:
        return "mock"

    async def complete(self, messages, system=None, **kwargs):
        self.calls.append({"messages": messages, "system": system, **kwargs})
        response_text = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return ProviderResponse(
            content=response_text,
            tokens_used=100,
            cost_usd=0.001,
            model="mock-model",
        )


@pytest.fixture
def mock_provider():
    """Create a mock provider."""
    return MockProvider()


@pytest.fixture
def sample_state():
    """Create a sample task state."""
    state = TaskState(objective="Test objective")
    state.add_task("First task")
    state.add_task("Second task")
    return state


@pytest.fixture
def completed_state():
    """Create a state with completed tasks."""
    state = TaskState(objective="Completed objective")
    task1 = state.add_task("Done task")
    task1.mark_completed("Result 1")
    task2 = state.add_task("Also done")
    task2.mark_completed("Result 2")
    return state
