"""Anthropic (Claude) provider implementation."""

from typing import Optional

try:
    import anthropic
except ImportError:
    raise ImportError(
        "anthropic package not installed. "
        "Install with: pip install agent-task-planning[anthropic]"
    )

from agent_planning.providers.base import BaseProvider, ProviderResponse


# Pricing per 1M tokens (as of Dec 2024)
PRICING = {
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},
    "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
}


class AnthropicProvider(BaseProvider):
    """
    Provider for Anthropic's Claude models.

    Example:
        provider = AnthropicProvider(api_key="sk-...")
        response = await provider.complete(
            messages=[{"role": "user", "content": "Hello"}],
            system="You are helpful."
        )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
    ):
        """
        Initialise the Anthropic provider.

        Args:
            api_key: Anthropic API key (uses ANTHROPIC_API_KEY env var if not provided)
            model: Model to use
            max_tokens: Maximum tokens in response
        """
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens

    @property
    def name(self) -> str:
        return f"anthropic/{self.model}"

    async def complete(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        **kwargs,
    ) -> ProviderResponse:
        """Generate a completion using Claude."""
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            system=system or "",
            messages=messages,
        )

        # Calculate cost
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        pricing = PRICING.get(self.model, {"input": 3.00, "output": 15.00})
        cost = (
            (input_tokens * pricing["input"] / 1_000_000) +
            (output_tokens * pricing["output"] / 1_000_000)
        )

        return ProviderResponse(
            content=response.content[0].text,
            tokens_used=input_tokens + output_tokens,
            cost_usd=cost,
            model=self.model,
            raw_response=response.model_dump(),
        )
