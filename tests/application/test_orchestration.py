"""Layer-1 tests for the Orchestrator (CLAUDE.md §5 L1).

Role protocols are stubbed — no LLM, no infrastructure. Tests verify that the turn
loop advances session state correctly, applies Modeler output to the domain model,
and routes through the Facilitator for every question.
"""

import asyncio

from vespagent.application.orchestration import Orchestrator
from vespagent.domain.model import CommandName, EventName
from vespagent.domain.roles import FacilitatorOutput, ModelerOutput
from vespagent.domain.session import Session


class StubFacilitator:
    """Returns a canned question and records every session it was called with."""

    def __init__(self, question: str = "What happens next?") -> None:
        self.question = question
        self.calls: list[Session] = []

    async def ask(self, session: Session) -> FacilitatorOutput:
        self.calls.append(session)
        return FacilitatorOutput(question=self.question)


class StubModeler:
    """Returns a canned output and records every session it was called with."""

    def __init__(self, output: ModelerOutput | None = None) -> None:
        self.output = output or ModelerOutput()
        self.calls: list[Session] = []

    async def extract(self, session: Session) -> ModelerOutput:
        self.calls.append(session)
        return self.output


def _run(coro):  # noqa: F841
    return asyncio.run(coro)


def _orchestrator(
    question: str = "What happens next?",
    modeler_output: ModelerOutput | None = None,
) -> tuple[Orchestrator, StubFacilitator, StubModeler]:
    facilitator = StubFacilitator(question=question)
    modeler = StubModeler(output=modeler_output)
    return Orchestrator(facilitator=facilitator, modeler=modeler), facilitator, modeler


class TestStart:
    def test_returns_the_facilitator_question(self):
        orch, _, _ = _orchestrator(question="Tell me about your domain.")
        question, _ = _run(orch.start("order fulfilment"))
        assert question == "Tell me about your domain."

    def test_returns_a_new_active_session(self):
        from vespagent.domain.session import SessionState

        orch, _, _ = _orchestrator()
        _, session = _run(orch.start("order fulfilment"))
        assert session.state == SessionState.ACTIVE

    def test_session_domain_model_has_correct_subject(self):
        orch, _, _ = _orchestrator()
        _, session = _run(orch.start("returns processing"))
        assert session.domain_model.subject == "returns processing"

    def test_opening_question_is_recorded_in_transcript(self):
        orch, _, _ = _orchestrator(question="Where shall we begin?")
        _, session = _run(orch.start("order fulfilment"))
        assert session.turn_count == 1
        assert session.transcript[0].speaker == "facilitator"
        assert session.transcript[0].content == "Where shall we begin?"

    def test_calls_facilitator_once(self):
        orch, facilitator, _ = _orchestrator()
        _run(orch.start("order fulfilment"))
        assert len(facilitator.calls) == 1

    def test_does_not_call_modeler(self):
        orch, _, modeler = _orchestrator()
        _run(orch.start("order fulfilment"))
        assert len(modeler.calls) == 0


class TestTurn:
    def test_returns_the_facilitator_question(self):
        orch, _, _ = _orchestrator(question="And then what?")
        _, session = _run(orch.start("order fulfilment"))
        question = _run(orch.turn("The order was placed.", session))
        assert question == "And then what?"

    def test_expert_input_recorded_in_transcript(self):
        orch, _, _ = _orchestrator()
        _, session = _run(orch.start("order fulfilment"))
        _run(orch.turn("Something happened.", session))
        expert_turns = [t for t in session.transcript if t.speaker == "expert"]
        assert len(expert_turns) == 1
        assert expert_turns[0].content == "Something happened."

    def test_facilitator_question_appended_to_transcript(self):
        orch, _, _ = _orchestrator(question="Next?")
        _, session = _run(orch.start("order fulfilment"))
        _run(orch.turn("Answer.", session))
        facilitator_turns = [t for t in session.transcript if t.speaker == "facilitator"]
        assert facilitator_turns[-1].content == "Next?"

    def test_calls_modeler_with_session(self):
        orch, _, modeler = _orchestrator()
        _, session = _run(orch.start("order fulfilment"))
        _run(orch.turn("Answer.", session))
        assert len(modeler.calls) == 1
        assert modeler.calls[0] is session

    def test_new_events_from_modeler_added_to_domain_model(self):
        events = [EventName(value="OrderPlaced"), EventName(value="PaymentReceived")]
        orch, _, _ = _orchestrator(modeler_output=ModelerOutput(new_events=events))
        _, session = _run(orch.start("order fulfilment"))
        _run(orch.turn("The order was placed and payment received.", session))
        assert session.domain_model.event_count == 2

    def test_new_commands_from_modeler_added_to_domain_model(self):
        commands = [CommandName(value="PlaceOrder")]
        orch, _, _ = _orchestrator(modeler_output=ModelerOutput(new_commands=commands))
        _, session = _run(orch.start("order fulfilment"))
        _run(orch.turn("The customer places an order.", session))
        assert session.domain_model.command_count == 1

    def test_duplicate_events_from_modeler_are_silently_ignored(self):
        name = EventName(value="OrderPlaced")
        orch, _, _ = _orchestrator(modeler_output=ModelerOutput(new_events=[name]))
        _, session = _run(orch.start("order fulfilment"))
        _run(orch.turn("First mention.", session))
        _run(orch.turn("Repeated mention.", session))
        assert session.domain_model.event_count == 1

    def test_duplicate_commands_from_modeler_are_silently_ignored(self):
        name = CommandName(value="PlaceOrder")
        orch, _, _ = _orchestrator(modeler_output=ModelerOutput(new_commands=[name]))
        _, session = _run(orch.start("order fulfilment"))
        _run(orch.turn("First mention.", session))
        _run(orch.turn("Repeated mention.", session))
        assert session.domain_model.command_count == 1

    def test_transcript_grows_correctly_over_multiple_turns(self):
        orch, _, _ = _orchestrator()
        _, session = _run(orch.start("order fulfilment"))
        _run(orch.turn("Answer one.", session))
        _run(orch.turn("Answer two.", session))
        # start: 1 facilitator; turn 1: 1 expert + 1 facilitator; turn 2: same
        assert session.turn_count == 5
