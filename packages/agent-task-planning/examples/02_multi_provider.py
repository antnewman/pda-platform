#!/usr/bin/env python3
"""
Multi-provider example demonstrating provider switching.

Shows how to use the same planner logic with different LLM providers.
"""

import asyncio
import os
from typing import Optional

from agent_planning import TodoListPlanner, GuardrailConfig
from agent_planning.providers.base import BaseProvider


def get_provider(name: str) -> Optional[BaseProvider]:
    """Get a provider by name."""
    if name == "anthropic":
        from agent_planning.providers import AnthropicProvider
        return AnthropicProvider(api_key=os.getenv("ANTHROPIC_API_KEY"))

    elif name == "openai":
        from agent_planning.providers import OpenAIProvider
        return OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"))

    elif name == "google":
        from agent_planning.providers import GoogleProvider
        return GoogleProvider(api_key=os.getenv("GOOGLE_API_KEY"))

    elif name == "ollama":
        from agent_planning.providers import OllamaProvider
        return OllamaProvider(model="llama3.1:8b")

    return None


async def run_with_provider(provider_name: str, objective: str):
    """Run a task with the specified provider."""
    provider = get_provider(provider_name)
    if provider is None:
        print(f"Unknown provider: {provider_name}")
        return

    print(f"\n{'=' * 50}")
    print(f"Running with {provider.name}")
    print("=" * 50)

    planner = TodoListPlanner(
        provider=provider,
        guardrails=GuardrailConfig(
            max_cost_usd=0.50,  # Limit spend per provider
            timeout_seconds=120,
        ),
    )

    result = await planner.execute(objective)

    print(f"\nResult: {'Success' if result.success else 'Failed'}")
    print(f"Tasks: {result.progress[0]}/{result.progress[1]} completed")
    print(f"Cost: ${result.total_cost_usd:.4f}")
    print(f"Tokens: {result.total_tokens:,}")


async def main():
    objective = "List 3 benefits of exercise and explain each briefly"

    # Run with each available provider
    for provider_name in ["anthropic", "openai", "ollama"]:
        try:
            await run_with_provider(provider_name, objective)
        except ImportError as e:
            print(f"Skipping {provider_name}: {e}")
        except Exception as e:
            print(f"Error with {provider_name}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
