"""Provider configuration — typed settings (CLAUDE.md §4).

Provider selection is the only place that knows which LLM is behind the roles.
The domain and application layers never see a model string.

Models are Pydantic AI `provider:model` strings; the provider prefix selects the
client (`anthropic`, `google`, `openai`, `ollama`, …). Override via environment
variables (prefix `VESPA_`) or a `.env` file:

  VESPA_DEFAULT_MODEL=anthropic:claude-opus-4-8   (default for every role)
  VESPA_FACILITATOR_MODEL=google:gemini-2.5-pro   (optional per-role override)
  VESPA_MODELER_MODEL=ollama:qwen3:14b            (optional per-role override)

Provider credentials/endpoints use each provider's native variables — e.g.
`ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `OLLAMA_BASE_URL` — which the composition
root loads from `.env` into the process environment (see `factories.py`).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class VespaSettings(BaseSettings):
    """Runtime configuration for VESPA."""

    model_config = SettingsConfigDict(env_prefix="VESPA_", env_file=".env", extra="ignore")

    default_model: str = "anthropic:claude-opus-4-8"
    """Pydantic AI `provider:model` string used by every role without an override."""

    facilitator_model: str | None = None
    """Optional override for the Facilitator role."""

    modeler_model: str | None = None
    """Optional override for the Modeler role."""

    @property
    def facilitator(self) -> str:
        """The model string for the Facilitator role."""
        return self.facilitator_model or self.default_model

    @property
    def modeler(self) -> str:
        """The model string for the Modeler role."""
        return self.modeler_model or self.default_model
