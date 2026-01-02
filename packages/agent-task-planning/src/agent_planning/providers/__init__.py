"""LLM Provider implementations."""

from agent_planning.providers.base import BaseProvider, ProviderResponse

__all__ = ["BaseProvider", "ProviderResponse"]

# Lazy imports for optional dependencies
def __getattr__(name: str):
    if name == "AnthropicProvider":
        from agent_planning.providers.anthropic import AnthropicProvider
        return AnthropicProvider
    elif name == "OpenAIProvider":
        from agent_planning.providers.openai import OpenAIProvider
        return OpenAIProvider
    elif name == "GoogleProvider":
        from agent_planning.providers.google import GoogleProvider
        return GoogleProvider
    elif name == "OllamaProvider":
        from agent_planning.providers.ollama import OllamaProvider
        return OllamaProvider
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
