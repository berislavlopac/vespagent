"""Composition root — build the application from config (CLAUDE.md §4).

The only place that wires domain, application, and infrastructure together.
Nothing outside this module needs to know which concrete adapters are in use.
"""

from vespagent.application.orchestration import Orchestrator
from vespagent.infrastructure.agents.facilitator import FacilitatorAgent
from vespagent.infrastructure.agents.modeler import ModelerAgent
from vespagent.wiring.config import VespaSettings


def create_orchestrator(settings: VespaSettings | None = None) -> Orchestrator:
    """Build a fully-wired `Orchestrator` from configuration.

    Provider credentials (`ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`,
    `OLLAMA_BASE_URL`, …) must be present in the **process environment** —
    deliberately not read from `.env`, so secrets arrive only through
    controlled channels (shell, direnv, secret managers, CI). Pydantic AI
    fails loudly on first use if the configured provider's key is missing.

    Args:
        settings: Runtime config. Reads from environment / .env if not supplied.

    Returns:
        An `Orchestrator` backed by the configured LLM provider(s).
    """
    if settings is None:
        settings = VespaSettings()
    return Orchestrator(
        facilitator=FacilitatorAgent(settings.facilitator),
        modeler=ModelerAgent(settings.modeler),
    )
