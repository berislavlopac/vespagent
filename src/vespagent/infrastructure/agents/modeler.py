"""Modeler role adapter — Pydantic AI implementation (CLAUDE.md §4, §7).

Satisfies the `ModelerRole` protocol structurally; the domain never imports
from here. Prompt lives in `prompts/modeler.md`.

Context is intentionally narrow: the Modeler receives only the already-known
artifacts and the expert's latest response — not the full transcript. Giving it
more context would dilute the extraction signal (CLAUDE.md §11).
"""

from importlib import resources

from pydantic_ai import Agent

from vespagent.domain.roles import ModelerOutput
from vespagent.domain.session import Session

_PROMPT = resources.files("vespagent.prompts").joinpath("modeler.md").read_text()


def _build_context(session: Session) -> str:
    """Serialise the session into a user-turn string for the Modeler.

    The Modeler receives: what is already in the model (to avoid duplicates)
    and the expert's latest response. The full transcript is deliberately
    withheld — the Modeler's job is extraction, not comprehension of history.
    """
    events = ", ".join(session.domain_model.events) or "none yet"
    commands = ", ".join(session.domain_model.commands) or "none yet"

    expert_turns = [t for t in session.transcript if t.speaker == "expert"]
    latest = expert_turns[-1].content if expert_turns else "(no expert response yet)"

    return (
        f"Domain: {session.domain_model.subject}\n\n"
        f"Already in the model:\n"
        f"  Events: {events}\n"
        f"  Commands: {commands}\n\n"
        f'Expert\'s latest response:\n"{latest}"'
    )


class ModelerAgent:
    """Pydantic AI adapter implementing `ModelerRole`.

    Wraps a single `Agent[None, ModelerOutput]`. The `_agent` attribute is
    intentionally accessible (single-underscore) for Layer-2 tests.
    """

    def __init__(self, model: str) -> None:
        self._agent: Agent[None, ModelerOutput] = Agent(
            model,
            output_type=ModelerOutput,
            system_prompt=_PROMPT,
            defer_model_check=True,
        )

    async def extract(self, session: Session) -> ModelerOutput:
        """Extract newly-discovered artifacts from the session.

        Args:
            session: The current interview session; focuses on the latest
                expert turn and the existing model state.

        Returns:
            A `ModelerOutput` with any new events and commands found.
        """
        result = await self._agent.run(_build_context(session))
        return result.output
