"""Layer-2 tests for the ModelerAgent adapter (CLAUDE.md §5 L2).

Verify schema-level correctness: the adapter produces valid, fully-typed
`ModelerOutput` without any real LLM call. Edge cases: empty output (nothing
new extracted), events only, commands only, both together.
"""

import asyncio

import pydantic_ai
from pydantic_ai.models.test import TestModel
import pytest

from vespagent.domain.model import DomainModel, EventName
from vespagent.domain.session import Session
from vespagent.infrastructure.agents.modeler import ModelerAgent

pydantic_ai.ALLOW_MODEL_REQUESTS = False


def _session(subject: str = "order fulfilment") -> Session:
    return Session(domain_model=DomainModel(subject=subject))


def _run(coro):  # noqa: F841
    return asyncio.run(coro)


class TestModelerAgentSchema:
    def test_returns_modeler_output(self):
        agent = ModelerAgent(model="anthropic:claude-opus-4-8")
        test_model = TestModel(custom_output_args={"new_events": [], "new_commands": []})
        session = _session()
        session.record_expert_turn("Nothing new here.")
        with agent._agent.override(model=test_model):
            result = _run(agent.extract(session))
        from vespagent.domain.roles import ModelerOutput

        assert isinstance(result, ModelerOutput)

    def test_empty_output_is_valid(self):
        agent = ModelerAgent(model="anthropic:claude-opus-4-8")
        test_model = TestModel(custom_output_args={"new_events": [], "new_commands": []})
        session = _session()
        session.record_expert_turn("Yes.")
        with agent._agent.override(model=test_model):
            result = _run(agent.extract(session))
        assert result.new_events == []
        assert result.new_commands == []

    def test_new_events_deserialise_as_event_names(self):
        agent = ModelerAgent(model="anthropic:claude-opus-4-8")
        test_model = TestModel(
            custom_output_args={
                "new_events": [{"value": "OrderPlaced"}, {"value": "PaymentReceived"}],
                "new_commands": [],
            }
        )
        session = _session()
        session.record_expert_turn("The customer places an order and pays.")
        with agent._agent.override(model=test_model):
            result = _run(agent.extract(session))
        from vespagent.domain.model import EventName

        assert len(result.new_events) == 2
        assert all(isinstance(e, EventName) for e in result.new_events)
        assert result.new_events[0].value == "OrderPlaced"
        assert result.new_events[1].value == "PaymentReceived"

    def test_new_commands_deserialise_as_command_names(self):
        agent = ModelerAgent(model="anthropic:claude-opus-4-8")
        test_model = TestModel(
            custom_output_args={
                "new_events": [],
                "new_commands": [{"value": "PlaceOrder"}],
            }
        )
        session = _session()
        session.record_expert_turn("The customer issues the PlaceOrder command.")
        with agent._agent.override(model=test_model):
            result = _run(agent.extract(session))
        from vespagent.domain.model import CommandName

        assert len(result.new_commands) == 1
        assert isinstance(result.new_commands[0], CommandName)
        assert result.new_commands[0].value == "PlaceOrder"

    def test_both_events_and_commands_together(self):
        agent = ModelerAgent(model="anthropic:claude-opus-4-8")
        test_model = TestModel(
            custom_output_args={
                "new_events": [{"value": "OrderPlaced"}],
                "new_commands": [{"value": "PlaceOrder"}],
            }
        )
        session = _session()
        session.record_expert_turn("The customer places an order.")
        with agent._agent.override(model=test_model):
            result = _run(agent.extract(session))
        assert len(result.new_events) == 1
        assert len(result.new_commands) == 1

    def test_event_name_validation_rejects_blank(self):
        """EventName must not be blank — Pydantic AI exhausts retries when validation
        fails on every attempt, surfacing as UnexpectedModelBehavior."""
        agent = ModelerAgent(model="anthropic:claude-opus-4-8")
        test_model = TestModel(
            custom_output_args={
                "new_events": [{"value": "   "}],
                "new_commands": [],
            }
        )
        session = _session()
        session.record_expert_turn("Something.")
        from pydantic_ai.exceptions import UnexpectedModelBehavior

        with agent._agent.override(model=test_model):
            with pytest.raises(UnexpectedModelBehavior):
                _run(agent.extract(session))

    def test_works_on_session_with_existing_model_content(self):
        """Modeler must still run cleanly when the domain model already has events."""
        agent = ModelerAgent(model="anthropic:claude-opus-4-8")
        session = _session()
        session.domain_model.add_event(EventName(value="OrderPlaced"))
        session.record_expert_turn("The shipment is dispatched.")
        test_model = TestModel(
            custom_output_args={
                "new_events": [{"value": "ShipmentDispatched"}],
                "new_commands": [],
            }
        )
        with agent._agent.override(model=test_model):
            result = _run(agent.extract(session))
        assert result.new_events[0].value == "ShipmentDispatched"

    def test_output_is_frozen(self):
        """ModelerOutput is a ValueObject — must be immutable."""
        agent = ModelerAgent(model="anthropic:claude-opus-4-8")
        test_model = TestModel(custom_output_args={"new_events": [], "new_commands": []})
        session = _session()
        session.record_expert_turn("Nothing.")
        with agent._agent.override(model=test_model):
            result = _run(agent.extract(session))
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            result.new_events = []  # type: ignore[misc]
