"""Provider configuration — typed settings (CLAUDE.md §4).

Provider selection is the only place that knows which LLM is behind the roles.
The domain and application layers never see a model string.

Override via environment variables (prefix VESPA_) or a .env file:
  VESPA_MODEL_PROVIDER=anthropic   (default; swap to "openai" for local models)
  VESPA_MODEL_NAME=claude-opus-4-8
  VESPA_BASE_URL=http://localhost:11434/v1   (for Ollama / vLLM)
"""

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class VespaSettings(BaseSettings):
    """Runtime configuration for VESPA."""

    model_config = SettingsConfigDict(env_prefix="VESPA_", env_file=".env", extra="ignore")

    model_provider: str = "anthropic"
    """LLM provider understood by Pydantic AI (e.g. `"anthropic"`, `"openai"`)."""

    model_name: str = "claude-opus-4-8"
    """Model identifier within the provider (e.g. `"claude-opus-4-8"`)."""

    base_url: str | None = None
    """Optional base URL override, used for local models via an OpenAI-compatible
    endpoint (Ollama, vLLM). Ignored when `model_provider` is `"anthropic"`."""

    @computed_field
    @property
    def pydantic_ai_model(self) -> str:
        """The model string passed to Pydantic AI agents, e.g. `"anthropic:claude-opus-4-8"`."""
        return f"{self.model_provider}:{self.model_name}"
