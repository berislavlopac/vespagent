"""Session aggregate — one interview run (CLAUDE.md §4).

A `Session` ties together the expert's transcript and the `DomainModel` being built.
It is the primary durable unit: resuming a session means loading this aggregate.
"""

from enum import StrEnum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import Field

from vespagent.domain.base import Entity, ValueObject
from vespagent.domain.model import DomainModel


class Turn(ValueObject):
    """A single utterance recorded in the interview transcript."""

    speaker: Literal["expert", "facilitator"]
    """Who spoke: the domain expert or the Facilitator role."""

    content: str
    """The verbatim text of the utterance."""


class SessionState(StrEnum):
    """Lifecycle state of a `Session`."""

    ACTIVE = "active"
    """Interview is ongoing; the expert can still respond."""

    COMPLETED = "completed"
    """Interview has concluded; the domain model is a finished draft."""


class Session(Entity):
    """Aggregate root for one interview session.

    Holds the growing transcript and the `DomainModel` being built from it.
    The application layer drives the session forward via `Orchestrator.turn`;
    this aggregate records what happened and what the model looks like right now.

    Identity is `id`; two `Session` instances with the same `id` are the same session.
    """

    id: UUID = Field(default_factory=uuid4)
    """Stable identity, generated on creation and never changed."""

    domain_model: DomainModel
    """The evolving domain model being built during this session."""

    transcript: list[Turn] = Field(default_factory=list)
    """Every turn in the interview, in order, including both speakers."""

    state: SessionState = SessionState.ACTIVE
    """Current lifecycle state."""

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Session):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def record_expert_turn(self, content: str) -> Turn:
        """Append an expert utterance to the transcript.

        Args:
            content: The expert's verbatim response.

        Returns:
            The recorded `Turn`.
        """
        turn = Turn(speaker="expert", content=content)
        self.transcript.append(turn)
        return turn

    def record_facilitator_turn(self, content: str) -> Turn:
        """Append a Facilitator utterance to the transcript.

        Args:
            content: The question or reflection the Facilitator produced.

        Returns:
            The recorded `Turn`.
        """
        turn = Turn(speaker="facilitator", content=content)
        self.transcript.append(turn)
        return turn

    @property
    def turn_count(self) -> int:
        """Total number of turns recorded so far."""
        return len(self.transcript)
