#!/usr/bin/env python3
"""
Production configuration example with comprehensive guardrails.

Demonstrates how to configure the planner for production use
with cost limits, timeouts, content validation, and approval gates.
"""

import asyncio
import os

from agent_planning import TodoListPlanner, GuardrailConfig
from agent_planning.providers import AnthropicProvider


async def main():
    provider = AnthropicProvider(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        model="claude-3-5-haiku-20241022",  # Use cheaper model for demos
    )

    # Production-grade guardrails
    guardrails = GuardrailConfig(
        # Execution limits
        max_tasks=10,
        max_iterations=30,
        max_cost_usd=0.25,
        timeout_seconds=60,
        max_retries_per_task=2,

        # Content safety
        blocked_patterns=[
            r"rm\s+-rf",           # Dangerous shell commands
            r"DROP\s+TABLE",       # SQL injection patterns
            r"api[_-]?key",        # Potential credential exposure
        ],

        # Approval requirements
        require_approval_for=[
            "delete",
            "send",
            "publish",
            "execute",
            "deploy",
        ],

        # Tool restrictions (if using tools)
        allowed_tools=[
            "search",
            "read_file",
            "write_file",
        ],
    )

    planner = TodoListPlanner(
        provider=provider,
        guardrails=guardrails,
    )

    print("Running with production guardrails...")
    print(f"  Max tasks: {guardrails.max_tasks}")
    print(f"  Max cost: ${guardrails.max_cost_usd}")
    print(f"  Timeout: {guardrails.timeout_seconds}s")
    print(f"  Approval required for: {guardrails.require_approval_for}")
    print()

    # This should complete successfully
    result = await planner.execute(
        "List 5 popular programming languages and one strength of each"
    )

    print("\n" + result.summary())

    if result.success:
        print("\nTasks completed:")
        for task in result.tasks:
            print(f"  {task.to_display()}")


if __name__ == "__main__":
    asyncio.run(main())
