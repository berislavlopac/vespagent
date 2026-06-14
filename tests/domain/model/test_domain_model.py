"""Layer-1 tests for DomainModel creation, identity, domain-event buffer, and exceptions."""

from uuid import uuid4

from vespagent.domain.exceptions import ModelNotFoundError
from vespagent.domain.model import (
    DomainModel,
    EventAdded,
    EventDescribed,
    EventName,
)


def _name(value: str = "OrderPlaced") -> EventName:
    return EventName(value=value)


def _model() -> DomainModel:
    return DomainModel(subject="order fulfilment")


class TestDomainModelCreation:
    def test_assigns_a_uuid_id(self):
        assert _model().id is not None

    def test_each_model_gets_a_unique_id(self):
        assert _model().id != _model().id

    def test_stores_subject(self):
        assert DomainModel(subject="returns processing").subject == "returns processing"

    def test_starts_with_no_events(self):
        assert _model().event_count == 0

    def test_starts_with_no_commands(self):
        assert _model().command_count == 0

    def test_starts_with_empty_domain_event_buffer(self):
        assert _model().collect_events() == []


class TestDomainEventBuffer:
    def test_collect_events_drains_the_buffer(self):
        model = _model()
        model.add_event(_name("A"))
        model.add_event(_name("B"))
        assert len(model.collect_events()) == 2
        assert model.collect_events() == []

    def test_domain_events_peek_does_not_drain(self):
        model = _model()
        model.add_event(_name())
        _ = model.domain_events
        assert len(model.collect_events()) == 1

    def test_events_accumulate_across_operations(self):
        model = _model()
        name = _name()
        model.add_event(name)
        model.describe_event(name, "desc")
        recorded = model.collect_events()
        assert len(recorded) == 2
        assert isinstance(recorded[0], EventAdded)
        assert isinstance(recorded[1], EventDescribed)


class TestIdentity:
    def test_same_id_means_equal(self):
        model = _model()
        same = DomainModel(id=model.id, subject="different subject")
        assert model == same

    def test_different_ids_means_not_equal(self):
        assert _model() != _model()

    def test_hashable_and_usable_in_a_set(self):
        model = _model()
        assert model in {model}

    def test_not_equal_to_non_domain_model(self):
        assert _model() != "not a model"


class TestDomainExceptions:
    def test_model_not_found_error_stores_id(self):
        model_id = uuid4()
        assert ModelNotFoundError(model_id).model_id == model_id

    def test_model_not_found_error_message_contains_id(self):
        model_id = uuid4()
        assert str(model_id) in str(ModelNotFoundError(model_id))
