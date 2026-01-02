#!/usr/bin/env python3
"""
Basic usage example for agent-task-planning.

This example demonstrates the simplest way to use the library
with the Anthropic provider.
"""

import asyncio
import os

from agent_planning import TodoListPlanner
from agent_planning.providers import AnthropicProvider


async def main():
    # Initialise provider (uses ANTHROPIC_API_KEY env var)
    provider = AnthropicProvider(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        model="claude-3-5-sonnet-20241022",
    )

    # Create planner
    planner = TodoListPlanner(provider=provider)

    # Execute a complex task
    result = await planner.execute(
        "Research the top 3 AI frameworks for building agents, "
        "compare their features, and recommend one for a startup"
    )

    # Print results
    print("\n" + "=" * 50)
    print("EXECUTION SUMMARY")
    print("=" * 50)
    print(result.summary())

    print("\n" + "=" * 50)
    print("TASK LIST")
    print("=" * 50)
    for task in result.tasks:
        print(task.to_display())

    if result.final_output:
        print("\n" + "=" * 50)
        print("FINAL OUTPUT")
        print("=" * 50)
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
