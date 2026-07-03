"""Layer-1 tests for provider configuration and the composition root (CLAUDE.md §5 L1).

No LLM calls: agents defer model checks, so wiring can be asserted on the model
strings alone. Settings are constructed with `_env_file=None` so a developer's
real `.env` never leaks into the tests.
"""

from vespagent.wiring.config import VespaSettings
from vespagent.wiring.factories import create_orchestrator


def _settings(**kwargs: str) -> VespaSettings:
    return VespaSettings(_env_file=None, **kwargs)


class TestDefaults:
    def test_default_model(self):
        assert _settings().default_model == "anthropic:claude-opus-4-8"

    def test_role_overrides_default_to_none(self):
        settings = _settings()
        assert settings.facilitator_model is None
        assert settings.modeler_model is None


class TestRoleResolution:
    def test_facilitator_falls_back_to_default(self):
        assert _settings(default_model="test").facilitator == "test"

    def test_modeler_falls_back_to_default(self):
        assert _settings(default_model="test").modeler == "test"

    def test_facilitator_override_wins(self):
        settings = _settings(facilitator_model="google:gemini-2.5-pro")
        assert settings.facilitator == "google:gemini-2.5-pro"

    def test_modeler_override_wins(self):
        settings = _settings(modeler_model="ollama:qwen3:14b")
        assert settings.modeler == "ollama:qwen3:14b"

    def test_override_does_not_affect_other_role(self):
        settings = _settings(modeler_model="ollama:qwen3:14b")
        assert settings.facilitator == "anthropic:claude-opus-4-8"


class TestEnvironment:
    def test_reads_prefixed_variables(self, monkeypatch):
        monkeypatch.setenv("VESPA_DEFAULT_MODEL", "google:gemini-2.5-flash")
        monkeypatch.setenv("VESPA_MODELER_MODEL", "ollama:qwen3:14b")
        settings = _settings()
        assert settings.facilitator == "google:gemini-2.5-flash"
        assert settings.modeler == "ollama:qwen3:14b"


class TestCreateOrchestrator:
    def test_wires_role_specific_models(self):
        settings = _settings(
            facilitator_model="google:gemini-2.5-pro",
            modeler_model="ollama:qwen3:14b",
        )
        orchestrator = create_orchestrator(settings)
        assert orchestrator._facilitator._agent.model == "google:gemini-2.5-pro"
        assert orchestrator._modeler._agent.model == "ollama:qwen3:14b"

    def test_single_model_reaches_both_roles(self):
        orchestrator = create_orchestrator(_settings(default_model="test"))
        assert orchestrator._facilitator._agent.model == "test"
        assert orchestrator._modeler._agent.model == "test"
