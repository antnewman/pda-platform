"""Ollama (local models) provider implementation."""

from typing import Optional

try:
    import ollama
except ImportError:
    raise ImportError(
        "ollama package not installed. "
        "Install with: pip install agent-task-planning[ollama]"
    )

from agent_planning.providers.base import BaseProvider, ProviderResponse


class OllamaProvider(BaseProvider):
    """
    Provider for local models via Ollama.

    Example:
        provider = OllamaProvider(model="llama3.1:70b")
        response = await provider.complete(
            messages=[{"role": "user", "content": "Hello"}]
        )
    """

    def __init__(
        self,
        model: str = "llama3.1:8b",
        base_url: str = "http://localhost:11434",
    ):
        """
        Initialise the Ollama provider.

        Args:
            model: Model name (must be pulled first)
            base_url: Ollama server URL
        """
        self.model = model
        self.client = ollama.AsyncClient(host=base_url)

    @property
    def name(self) -> str:
        return f"ollama/{self.model}"

    async def complete(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        **kwargs,
    ) -> ProviderResponse:
        """Generate a completion using Ollama."""
        # Prepend system message if provided
        all_messages = messages.copy()
        if system:
            all_messages.insert(0, {"role": "system", "content": system})

        response = await self.client.chat(
            model=self.model,
            messages=all_messages,
        )

        # Ollama provides token counts
        tokens = response.get("eval_count", 0) + response.get("prompt_eval_count", 0)

        return ProviderResponse(
            content=response["message"]["content"],
            tokens_used=tokens,
            cost_usd=0.0,  # Local models are free
            model=self.model,
            raw_response=response,
        )
