"""Role protocols and their I/O contracts (CLAUDE.md §3, §4, §7).

Each role is a distinct, separately-framed model call behind a `Protocol` so the
orchestrator depends on abstractions, not on Pydantic AI. The role suffix is intentional
(CLAUDE.md §10 2026-06-14): `FacilitatorRole`, `ModelerRole`, etc.

Only the roles needed for the current build step are defined; others follow in §9 steps
5 and 9. Role context is deliberately scoped: each protocol receives only what that role
needs — don't widen a role's context 'helpfully' (CLAUDE.md §11).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from pydantic import Field

from vespagent.domain.base import ValueObject
from vespagent.domain.model import CommandName, EventName

if TYPE_CHECKING:
    from vespagent.domain.session import Session


class FacilitatorOutput(ValueObject):
    """What the Facilitator role produces: the single next question to ask the expert."""

    question: str
    """The next question to put to the domain expert.

    Must be exactly one question — the Facilitator never fires multiple questions at once
    (CLAUDE.md §3). The question must depend on what the expert just said, not on a
    fixed script (CLAUDE.md §2).
    """


class ModelerOutput(ValueObject):
    """What the Modeler role extracts from the expert's most recent response."""

    new_events: list[EventName] = Field(default_factory=list)
    """Domain events newly mentioned or implied in the expert's last turn."""

    new_commands: list[CommandName] = Field(default_factory=list)
    """Commands newly mentioned or implied in the expert's last turn."""


class FacilitatorRole(Protocol):
    """Drives the conversation: decides the next move and asks the single next question.

    Receives the full session (transcript + current model state) so its choice of next
    question is adaptive, not scripted (CLAUDE.md §2). Only the Facilitator speaks to
    the human (CLAUDE.md §3).
    """

    async def ask(self, session: Session) -> FacilitatorOutput:
        """Produce the next question to ask the domain expert.

        Args:
            session: The current session, including full transcript and domain model.

        Returns:
            A `FacilitatorOutput` containing exactly one question.
        """
        ...


class ModelerRole(Protocol):
    """Extracts and structures domain artifacts from the conversation so far.

    Works behind the scenes; its output is applied to the `DomainModel` by the
    orchestrator before the Facilitator decides the next move. Never speaks to the
    human directly (CLAUDE.md §3).
    """

    async def extract(self, session: Session) -> ModelerOutput:
        """Extract newly-discovered artifacts from the session.

        Args:
            session: The current session; the Modeler should focus on the latest
                expert turn but may use prior context.

        Returns:
            A `ModelerOutput` containing any new events and commands found.
        """
        ...
