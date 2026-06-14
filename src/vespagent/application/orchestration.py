"""Orchestrator — the adaptive turn loop (CLAUDE.md §2, §4, §9 step 1).

Coordinates the role calls for one interview turn. Control flow is driven by the
accumulated session state, not by a fixed script (§2). Fully testable with stubbed role
protocols — no LLM needed at this layer (§5 L1).
"""

from vespagent.domain.model import DomainModel
from vespagent.domain.model.exceptions import DuplicateCommandError, DuplicateEventError
from vespagent.domain.roles import FacilitatorRole, ModelerOutput, ModelerRole
from vespagent.domain.session import Session


class Orchestrator:
    """Drives one VESPA interview turn end-to-end.

    On each turn: records the expert's input, lets the Modeler extract artifacts,
    applies them to the domain model, then asks the Facilitator for the next question.
    Holds no state of its own — all state lives in `Session`.
    """

    def __init__(self, facilitator: FacilitatorRole, modeler: ModelerRole) -> None:
        self._facilitator = facilitator
        self._modeler = modeler

    async def start(self, subject: str) -> tuple[str, Session]:
        """Open a new session and return the Facilitator's opening question.

        Args:
            subject: The domain area to explore, e.g. `'order fulfilment'`.

        Returns:
            A tuple of `(opening_question, session)`. The session is ACTIVE and its
            transcript already contains the Facilitator's opening turn.
        """
        session = Session(domain_model=DomainModel(subject=subject))
        output = await self._facilitator.ask(session)
        session.record_facilitator_turn(output.question)
        return output.question, session

    async def turn(self, user_input: str, session: Session) -> str:
        """Process one expert response and return the Facilitator's next question.

        Records the expert's input, runs the Modeler to extract new artifacts, applies
        them to the domain model, then runs the Facilitator to get the next question.

        Args:
            user_input: The expert's verbatim response.
            session: The current session; mutated in place.

        Returns:
            The Facilitator's next question.
        """
        session.record_expert_turn(user_input)
        modeler_output = await self._modeler.extract(session)
        self._apply_modeler_output(session, modeler_output)
        facilitator_output = await self._facilitator.ask(session)
        session.record_facilitator_turn(facilitator_output.question)
        return facilitator_output.question

    def _apply_modeler_output(self, session: Session, output: ModelerOutput) -> None:
        # Silently drop duplicates: the Modeler sees the current model but may still
        # re-surface names already present (e.g. the expert restates a prior event).
        for name in output.new_events:
            try:
                session.domain_model.add_event(name)
            except DuplicateEventError:
                pass
        for name in output.new_commands:
            try:
                session.domain_model.add_command(name)
            except DuplicateCommandError:
                pass
