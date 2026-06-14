"""Layer-1 tests for EventName, ModeledEvent, and DomainModel event operations."""

from pydantic import ValidationError
import pytest

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


def _model() -> DomainModel:
    return DomainModel(subject="order fulfilment")


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
        with pytest.raises(ValidationError):
            _name().value = "mutated"  # type: ignore[misc]

    def test_equality_by_value(self):
        assert _name("OrderPlaced") == _name("OrderPlaced")
        assert _name("OrderPlaced") != _name("PaymentReceived")

    def test_hashable(self):
        assert {_name("A"), _name("A")} == {_name("A")}


class TestAddEvent:
    def test_returns_a_modeled_event(self):
        assert isinstance(_model().add_event(_name()), ModeledEvent)

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
        """ModeledEvent is frozen; describe_event must replace, not mutate."""
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
