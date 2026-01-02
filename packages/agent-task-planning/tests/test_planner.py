"""Tests for TodoListPlanner."""

import pytest
from unittest.mock import AsyncMock, patch

from agent_planning.planners.todo_list import TodoListPlanner
from agent_planning.guardrails.limits import GuardrailConfig


class TestTodoListPlanner:
    """Tests for TodoListPlanner class."""

    @pytest.mark.asyncio
    async def test_basic_execution(self, mock_provider):
        """Test basic task execution."""
        # Setup mock to return a task list then completion
        mock_provider.responses = [
            '[{"content": "Task 1", "status": "pending"}]',
            "Task 1 completed successfully",
            "Final summary of work done",
        ]

        planner = TodoListPlanner(provider=mock_provider)
        result = await planner.execute("Do something")

        assert result.total_iterations >= 1
        assert mock_provider.call_count >= 1

    @pytest.mark.asyncio
    async def test_guardrail_max_iterations(self, mock_provider):
        """Test that max iterations guardrail is enforced."""
        # Mock that always returns pending tasks
        mock_provider.responses = [
            '[{"content": "Never ending task", "status": "pending"}]',
            "Still working...",
        ]

        planner = TodoListPlanner(
            provider=mock_provider,
            guardrails=GuardrailConfig(max_iterations=3),
        )
        result = await planner.execute("Infinite loop test")

        assert not result.success
        assert "iteration" in result.error.lower()

    @pytest.mark.asyncio
    async def test_guardrail_max_cost(self, mock_provider):
        """Test that cost guardrail is enforced."""
        # Make mock return high cost
        original_complete = mock_provider.complete

        async def high_cost_complete(*args, **kwargs):
            response = await original_complete(*args, **kwargs)
            response.cost_usd = 10.0  # Very high cost
            return response

        mock_provider.complete = high_cost_complete
        mock_provider.responses = [
            '[{"content": "Expensive task", "status": "pending"}]',
        ]

        planner = TodoListPlanner(
            provider=mock_provider,
            guardrails=GuardrailConfig(max_cost_usd=0.01),
        )
        result = await planner.execute("Expensive operation")

        assert not result.success
        assert "cost" in result.error.lower()

    def test_parse_tasks_json(self, mock_provider):
        """Test JSON task parsing."""
        planner = TodoListPlanner(provider=mock_provider)

        content = '[{"content": "Task 1", "status": "pending"}, {"content": "Task 2", "status": "completed"}]'
        tasks = planner._parse_tasks(content)

        assert len(tasks) == 2
        assert tasks[0]["content"] == "Task 1"
        assert tasks[1]["content"] == "Task 2"

    def test_parse_tasks_fallback(self, mock_provider):
        """Test fallback task parsing for non-JSON responses."""
        planner = TodoListPlanner(provider=mock_provider)

        content = """Here are the tasks:
☐ First task to do
☐ Second task to do
✓ Already done task"""

        tasks = planner._parse_tasks(content)
        assert len(tasks) >= 2
