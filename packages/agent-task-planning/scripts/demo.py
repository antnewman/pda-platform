#!/usr/bin/env python3
"""
Command-line demo for agent-task-planning.

Usage:
    python scripts/demo.py "Your task here"
    python scripts/demo.py --provider openai "Your task here"
    python scripts/demo.py --provider ollama --model llama3.1:8b "Your task here"
"""

import argparse
import asyncio
import os
import sys

# Add src to path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agent_planning import TodoListPlanner, GuardrailConfig


def get_provider(provider_name: str, model: str | None = None):
    """Create a provider instance."""
    if provider_name == "anthropic":
        from agent_planning.providers import AnthropicProvider
        return AnthropicProvider(
            model=model or "claude-3-5-haiku-20241022"
        )
    elif provider_name == "openai":
        from agent_planning.providers import OpenAIProvider
        return OpenAIProvider(
            model=model or "gpt-4o-mini"
        )
    elif provider_name == "google":
        from agent_planning.providers import GoogleProvider
        return GoogleProvider(
            model=model or "gemini-1.5-flash"
        )
    elif provider_name == "ollama":
        from agent_planning.providers import OllamaProvider
        return OllamaProvider(
            model=model or "llama3.1:8b"
        )
    else:
        raise ValueError(f"Unknown provider: {provider_name}")


async def main():
    parser = argparse.ArgumentParser(description="Agent Task Planning Demo")
    parser.add_argument("objective", help="The task to accomplish")
    parser.add_argument(
        "--provider",
        choices=["anthropic", "openai", "google", "ollama"],
        default="anthropic",
        help="LLM provider to use",
    )
    parser.add_argument("--model", help="Specific model to use")
    parser.add_argument(
        "--max-cost",
        type=float,
        default=0.25,
        help="Maximum cost in USD",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Timeout in seconds",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Setup logging if verbose
    if args.verbose:
        import structlog
        import logging
        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
        )

    print(f"Provider: {args.provider}")
    print(f"Objective: {args.objective}")
    print(f"Max cost: ${args.max_cost}")
    print("-" * 50)

    try:
        provider = get_provider(args.provider, args.model)
    except ImportError as e:
        print(f"Error: {e}")
        print(f"Install with: pip install agent-task-planning[{args.provider}]")
        sys.exit(1)

    planner = TodoListPlanner(
        provider=provider,
        guardrails=GuardrailConfig(
            max_cost_usd=args.max_cost,
            timeout_seconds=args.timeout,
        ),
    )

    print("Executing...\n")
    result = await planner.execute(args.objective)

    print("=" * 50)
    print("RESULT")
    print("=" * 50)
    print(result.summary())

    print("\n" + "=" * 50)
    print("TASKS")
    print("=" * 50)
    for task in result.tasks:
        print(task.to_display())

    if result.final_output:
        print("\n" + "=" * 50)
        print("OUTPUT")
        print("=" * 50)
        print(result.final_output)

    if result.error:
        print("\n" + "=" * 50)
        print("ERROR")
        print("=" * 50)
        print(result.error)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
