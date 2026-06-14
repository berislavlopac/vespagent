"""Facilitator role adapter — Pydantic AI implementation (CLAUDE.md §4, §7).

The only place in this module that knows about Pydantic AI. Satisfies the
`FacilitatorRole` protocol structurally; the domain never imports from here.
Prompt lives in `prompts/facilitator.md` and is loaded once at module import.
"""

from importlib import resources

from pydantic_ai import Agent

from vespagent.domain.roles import FacilitatorOutput
from vespagent.domain.session import Session

_PROMPT = resources.files("vespagent.prompts").joinpath("facilitator.md").read_text()


def _build_context(session: Session) -> str:
    """Serialise the session into a user-turn string for the Facilitator.

    The Facilitator receives: the domain subject, what has been discovered so
    far, and the full transcript. Context is intentionally broad here (§9 step 2
    — 'everything in context') and will be tightened once quality is judged.
    """
    events = ", ".join(session.domain_model.events) or "none yet"
    commands = ", ".join(session.domain_model.commands) or "none yet"

    if session.transcript:
        transcript_lines = [f"[{turn.speaker}]: {turn.content}" for turn in session.transcript]
        transcript = "\n".join(transcript_lines)
    else:
        transcript = "(session just started — no turns yet)"

    return (
        f"Domain being explored: {session.domain_model.subject}\n\n"
        f"Events discovered so far: {events}\n"
        f"Commands discovered so far: {commands}\n\n"
        f"Transcript:\n{transcript}"
    )


class FacilitatorAgent:
    """Pydantic AI adapter implementing `FacilitatorRole`.

    Wraps a single `Agent[None, FacilitatorOutput]`. The `_agent` attribute is
    intentionally accessible (single-underscore) so Layer-2 tests can call
    `self._agent.override(model=TestModel())` without modifying production code.
    """

    def __init__(self, model: str) -> None:
        self._agent: Agent[None, FacilitatorOutput] = Agent(
            model,
            output_type=FacilitatorOutput,
            system_prompt=_PROMPT,
            defer_model_check=True,
        )

    async def ask(self, session: Session) -> FacilitatorOutput:
        """Ask the single next question given the current session state.

        Args:
            session: The current interview session (transcript + domain model).

        Returns:
            A `FacilitatorOutput` containing exactly one question.
        """
        result = await self._agent.run(_build_context(session))
        return result.output
