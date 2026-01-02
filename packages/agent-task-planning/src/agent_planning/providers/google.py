"""Google (Gemini) provider implementation."""

from typing import Optional

try:
    import google.generativeai as genai
except ImportError:
    raise ImportError(
        "google-generativeai package not installed. "
        "Install with: pip install agent-task-planning[google]"
    )

from agent_planning.providers.base import BaseProvider, ProviderResponse


# Pricing per 1M tokens (as of Dec 2024)
PRICING = {
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-2.0-flash-exp": {"input": 0.10, "output": 0.40},
}


class GoogleProvider(BaseProvider):
    """
    Provider for Google's Gemini models.

    Example:
        provider = GoogleProvider(api_key="...")
        response = await provider.complete(
            messages=[{"role": "user", "content": "Hello"}]
        )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-1.5-pro",
        max_tokens: int = 4096,
    ):
        """
        Initialise the Google provider.

        Args:
            api_key: Google API key (uses GOOGLE_API_KEY env var if not provided)
            model: Model to use
            max_tokens: Maximum tokens in response
        """
        if api_key:
            genai.configure(api_key=api_key)
        self.model_name = model
        self.model = genai.GenerativeModel(model)
        self.max_tokens = max_tokens

    @property
    def name(self) -> str:
        return f"google/{self.model_name}"

    async def complete(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        **kwargs,
    ) -> ProviderResponse:
        """Generate a completion using Gemini."""
        # Convert messages to Gemini format
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [msg["content"]]})

        # Add system instruction if provided
        generation_config = genai.GenerationConfig(
            max_output_tokens=kwargs.get("max_tokens", self.max_tokens),
        )

        if system:
            model = genai.GenerativeModel(
                self.model_name,
                system_instruction=system,
            )
        else:
            model = self.model

        response = await model.generate_content_async(
            contents,
            generation_config=generation_config,
        )

        # Estimate tokens (Gemini doesn't always provide this)
        input_tokens = sum(len(c["parts"][0]) // 4 for c in contents)
        output_tokens = len(response.text) // 4

        pricing = PRICING.get(self.model_name, {"input": 1.25, "output": 5.00})
        cost = (
            (input_tokens * pricing["input"] / 1_000_000) +
            (output_tokens * pricing["output"] / 1_000_000)
        )

        return ProviderResponse(
            content=response.text,
            tokens_used=input_tokens + output_tokens,
            cost_usd=cost,
            model=self.model_name,
        )
