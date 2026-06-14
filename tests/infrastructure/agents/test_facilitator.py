"""Layer-2 tests for the FacilitatorAgent adapter (CLAUDE.md §5 L2).

These tests verify schema-level correctness: that the adapter produces valid,
fully-typed `FacilitatorOutput` without any real LLM call. Content of the
question is irrelevant here — structural validity is what is being checked.
"""

import asyncio

import pydantic_ai
from pydantic_ai.models.test import TestModel
import pytest

from vespagent.domain.model import DomainModel
from vespagent.domain.session import Session
from vespagent.infrastructure.agents.facilitator import FacilitatorAgent

pydantic_ai.ALLOW_MODEL_REQUESTS = False


def _session(subject: str = "order fulfilment") -> Session:
    return Session(domain_model=DomainModel(subject=subject))


def _run(coro):  # noqa: F841
    return asyncio.run(coro)


class TestFacilitatorAgentSchema:
    def test_returns_facilitator_output(self):
        agent = FacilitatorAgent(model="anthropic:claude-opus-4-8")
        test_model = TestModel(custom_output_args={"question": "What happens next?"})
        with agent._agent.override(model=test_model):
            result = _run(agent.ask(_session()))
        from vespagent.domain.roles import FacilitatorOutput

        assert isinstance(result, FacilitatorOutput)

    def test_question_field_is_a_string(self):
        agent = FacilitatorAgent(model="anthropic:claude-opus-4-8")
        test_model = TestModel(custom_output_args={"question": "Tell me more."})
        with agent._agent.override(model=test_model):
            result = _run(agent.ask(_session()))
        assert isinstance(result.question, str)

    def test_custom_question_is_preserved(self):
        agent = FacilitatorAgent(model="anthropic:claude-opus-4-8")
        q = "What does the warehouse do when an order arrives?"
        test_model = TestModel(custom_output_args={"question": q})
        with agent._agent.override(model=test_model):
            result = _run(agent.ask(_session()))
        assert result.question == q

    def test_works_on_empty_session(self):
        """Facilitator must handle a brand-new session with no transcript."""
        agent = FacilitatorAgent(model="anthropic:claude-opus-4-8")
        test_model = TestModel(custom_output_args={"question": "Where shall we begin?"})
        with agent._agent.override(model=test_model):
            result = _run(agent.ask(_session()))
        assert result.question

    def test_works_on_session_with_turns(self):
        agent = FacilitatorAgent(model="anthropic:claude-opus-4-8")
        session = _session()
        session.record_facilitator_turn("What happens first?")
        session.record_expert_turn("The customer places an order.")
        test_model = TestModel(custom_output_args={"question": "Who receives the order?"})
        with agent._agent.override(model=test_model):
            result = _run(agent.ask(session))
        assert result.question

    def test_output_is_frozen(self):
        """FacilitatorOutput is a ValueObject — must be immutable."""
        agent = FacilitatorAgent(model="anthropic:claude-opus-4-8")
        test_model = TestModel(custom_output_args={"question": "Any question."})
        with agent._agent.override(model=test_model):
            result = _run(agent.ask(_session()))
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            result.question = "mutated"  # type: ignore[misc]
