"""OpenAI provider implementation."""

from typing import Optional

try:
    import openai
except ImportError:
    raise ImportError(
        "openai package not installed. "
        "Install with: pip install agent-task-planning[openai]"
    )

from agent_planning.providers.base import BaseProvider, ProviderResponse


# Pricing per 1M tokens (as of Dec 2024)
PRICING = {
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
}


class OpenAIProvider(BaseProvider):
    """
    Provider for OpenAI models.

    Example:
        provider = OpenAIProvider(api_key="sk-...")
        response = await provider.complete(
            messages=[{"role": "user", "content": "Hello"}]
        )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        max_tokens: int = 4096,
    ):
        """
        Initialise the OpenAI provider.

        Args:
            api_key: OpenAI API key (uses OPENAI_API_KEY env var if not provided)
            model: Model to use
            max_tokens: Maximum tokens in response
        """
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens

    @property
    def name(self) -> str:
        return f"openai/{self.model}"

    async def complete(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        **kwargs,
    ) -> ProviderResponse:
        """Generate a completion using OpenAI."""
        # Prepend system message if provided
        all_messages = messages.copy()
        if system:
            all_messages.insert(0, {"role": "system", "content": system})

        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            messages=all_messages,
        )

        # Calculate cost
        input_tokens = response.usage.prompt_tokens if response.usage else 0
        output_tokens = response.usage.completion_tokens if response.usage else 0
        pricing = PRICING.get(self.model, {"input": 2.50, "output": 10.00})
        cost = (
            (input_tokens * pricing["input"] / 1_000_000) +
            (output_tokens * pricing["output"] / 1_000_000)
        )

        return ProviderResponse(
            content=response.choices[0].message.content or "",
            tokens_used=input_tokens + output_tokens,
            cost_usd=cost,
            model=self.model,
            raw_response=response.model_dump(),
        )
