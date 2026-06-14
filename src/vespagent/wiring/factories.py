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

    Args:
        settings: Runtime config. Reads from environment / .env if not supplied.

    Returns:
        An `Orchestrator` backed by the configured LLM provider.
    """
    if settings is None:
        settings = VespaSettings()
    model = settings.pydantic_ai_model
    return Orchestrator(
        facilitator=FacilitatorAgent(model),
        modeler=ModelerAgent(model),
    )
