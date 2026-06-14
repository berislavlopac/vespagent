"""Layer-1 tests for the DomainModel aggregate root (CLAUDE.md §5 L1).

All role ports are absent — these tests exercise the domain in isolation, with no LLM
and no infrastructure. Invariant enforcement, domain-event recording, and value-object
replacement semantics are the things being verified.
"""

from pydantic import ValidationError
import pytest

from vespagent.domain.exceptions import ModelNotFoundError
from vespagent.domain.model import (
    DomainModel,
    DuplicateEventError,
    EventAdded,
    EventDescribed,
    EventName,
    EventNotFoundError,
    ModeledEvent,
)


def _name(value: str = "OrderPlaced") -> EventName:
    return EventName(value=value)


def _model(subject: str = "order fulfilment") -> DomainModel:
    return DomainModel(subject=subject)


class TestEventName:
    def test_stores_value(self):
        assert _name("OrderPlaced").value == "OrderPlaced"

    def test_trims_whitespace(self):
        assert EventName(value="  OrderPlaced  ").value == "OrderPlaced"

    def test_rejects_blank(self):
        with pytest.raises(ValidationError):
            EventName(value="   ")

    def test_rejects_empty(self):
        with pytest.raises(ValidationError):
            EventName(value="")

    def test_is_frozen(self):
        name = _name()
        with pytest.raises(ValidationError):
            name.value = "mutated"  # type: ignore[misc]

    def test_equality_by_value(self):
        assert _name("OrderPlaced") == _name("OrderPlaced")
        assert _name("OrderPlaced") != _name("PaymentReceived")

    def test_hashable(self):
        assert {_name("A"), _name("A")} == {_name("A")}


class TestDomainModelCreation:
    def test_assigns_a_uuid_id(self):
        assert _model().id is not None

    def test_each_model_gets_a_unique_id(self):
        assert _model().id != _model().id

    def test_stores_subject(self):
        assert DomainModel(subject="returns processing").subject == "returns processing"

    def test_starts_with_no_events(self):
        assert _model().event_count == 0

    def test_starts_with_empty_domain_event_buffer(self):
        assert _model().collect_events() == []


class TestAddEvent:
    def test_returns_a_modeled_event(self):
        event = _model().add_event(_name())
        assert isinstance(event, ModeledEvent)

    def test_returned_event_has_the_given_name(self):
        name = _name("OrderPlaced")
        assert _model().add_event(name).name == name

    def test_new_event_has_no_description(self):
        assert _model().add_event(_name()).description is None

    def test_increments_event_count(self):
        model = _model()
        model.add_event(_name("OrderPlaced"))
        model.add_event(_name("PaymentReceived"))
        assert model.event_count == 2

    def test_event_is_retrievable_after_add(self):
        model = _model()
        name = _name("OrderPlaced")
        model.add_event(name)
        assert model.get_event(name).name == name

    def test_raises_on_duplicate_name(self):
        model = _model()
        name = _name()
        model.add_event(name)
        with pytest.raises(DuplicateEventError) as exc_info:
            model.add_event(name)
        assert exc_info.value.name == name

    def test_duplicate_error_message_contains_name(self):
        model = _model()
        name = _name("OrderPlaced")
        model.add_event(name)
        with pytest.raises(DuplicateEventError, match="OrderPlaced"):
            model.add_event(name)

    def test_records_event_added_domain_event(self):
        model = _model()
        name = _name("OrderPlaced")
        model.add_event(name)
        (recorded,) = model.collect_events()
        assert isinstance(recorded, EventAdded)
        assert recorded.event_name == name
        assert recorded.model_id == model.id


class TestDescribeEvent:
    def test_returns_updated_event(self):
        model = _model()
        name = _name()
        model.add_event(name)
        updated = model.describe_event(name, "The order was placed by the customer.")
        assert updated.description == "The order was placed by the customer."

    def test_get_event_reflects_new_description(self):
        model = _model()
        name = _name()
        model.add_event(name)
        model.describe_event(name, "Something happened.")
        assert model.get_event(name).description == "Something happened."

    def test_overwrites_existing_description(self):
        model = _model()
        name = _name()
        model.add_event(name)
        model.describe_event(name, "First.")
        model.describe_event(name, "Revised.")
        assert model.get_event(name).description == "Revised."

    def test_does_not_mutate_the_original_value_object(self):
        """ModeledEvent is a frozen value object; describe_event must replace, not mutate."""
        model = _model()
        name = _name()
        original = model.add_event(name)
        model.describe_event(name, "New description.")
        assert original.description is None

    def test_raises_for_unknown_event(self):
        with pytest.raises(EventNotFoundError) as exc_info:
            _model().describe_event(_name("Ghost"), "Doesn't matter.")
        assert exc_info.value.name == _name("Ghost")

    def test_not_found_error_message_contains_name(self):
        with pytest.raises(EventNotFoundError, match="Ghost"):
            _model().describe_event(_name("Ghost"), "Doesn't matter.")

    def test_records_event_described_domain_event(self):
        model = _model()
        name = _name()
        model.add_event(name)
        model.collect_events()
        model.describe_event(name, "It happened.")
        (recorded,) = model.collect_events()
        assert isinstance(recorded, EventDescribed)
        assert recorded.event_name == name
        assert recorded.description == "It happened."
        assert recorded.model_id == model.id


class TestGetEvent:
    def test_returns_the_stored_event(self):
        model = _model()
        name = _name("ShipmentDispatched")
        model.add_event(name)
        assert model.get_event(name).name == name

    def test_raises_for_unknown_event(self):
        with pytest.raises(EventNotFoundError):
            _model().get_event(_name("Ghost"))


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
        from uuid import uuid4

        model_id = uuid4()
        exc = ModelNotFoundError(model_id)
        assert exc.model_id == model_id

    def test_model_not_found_error_message_contains_id(self):
        from uuid import uuid4

        model_id = uuid4()
        assert str(model_id) in str(ModelNotFoundError(model_id))
