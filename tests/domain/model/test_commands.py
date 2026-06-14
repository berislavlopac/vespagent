"""Layer-1 tests for CommandName, Command, and DomainModel command operations."""

from pydantic import ValidationError
import pytest

from vespagent.domain.model import (
    Command,
    CommandAdded,
    CommandDescribed,
    CommandName,
    CommandNotFoundError,
    DomainModel,
    DuplicateCommandError,
)


def _name(value: str = "PlaceOrder") -> CommandName:
    return CommandName(value=value)


def _model() -> DomainModel:
    return DomainModel(subject="order fulfilment")


class TestCommandName:
    def test_stores_value(self):
        assert _name("PlaceOrder").value == "PlaceOrder"

    def test_trims_whitespace(self):
        assert CommandName(value="  PlaceOrder  ").value == "PlaceOrder"

    def test_rejects_blank(self):
        with pytest.raises(ValidationError):
            CommandName(value="   ")

    def test_rejects_empty(self):
        with pytest.raises(ValidationError):
            CommandName(value="")

    def test_is_frozen(self):
        with pytest.raises(ValidationError):
            _name().value = "mutated"  # type: ignore[misc]

    def test_equality_by_value(self):
        assert _name("PlaceOrder") == _name("PlaceOrder")
        assert _name("PlaceOrder") != _name("CancelOrder")

    def test_hashable(self):
        assert {_name("A"), _name("A")} == {_name("A")}


class TestAddCommand:
    def test_returns_a_command(self):
        assert isinstance(_model().add_command(_name()), Command)

    def test_returned_command_has_the_given_name(self):
        name = _name("PlaceOrder")
        assert _model().add_command(name).name == name

    def test_new_command_has_no_description(self):
        assert _model().add_command(_name()).description is None

    def test_increments_command_count(self):
        model = _model()
        model.add_command(_name("PlaceOrder"))
        model.add_command(_name("CancelOrder"))
        assert model.command_count == 2

    def test_command_is_retrievable_after_add(self):
        model = _model()
        name = _name("PlaceOrder")
        model.add_command(name)
        assert model.get_command(name).name == name

    def test_raises_on_duplicate_name(self):
        model = _model()
        name = _name()
        model.add_command(name)
        with pytest.raises(DuplicateCommandError) as exc_info:
            model.add_command(name)
        assert exc_info.value.name == name

    def test_duplicate_error_message_contains_name(self):
        model = _model()
        name = _name("PlaceOrder")
        model.add_command(name)
        with pytest.raises(DuplicateCommandError, match="PlaceOrder"):
            model.add_command(name)

    def test_records_command_added_domain_event(self):
        model = _model()
        name = _name("PlaceOrder")
        model.add_command(name)
        (recorded,) = model.collect_events()
        assert isinstance(recorded, CommandAdded)
        assert recorded.command_name == name
        assert recorded.model_id == model.id


class TestDescribeCommand:
    def test_returns_updated_command(self):
        model = _model()
        name = _name()
        model.add_command(name)
        updated = model.describe_command(name, "Issued by the customer to start checkout.")
        assert updated.description == "Issued by the customer to start checkout."

    def test_get_command_reflects_new_description(self):
        model = _model()
        name = _name()
        model.add_command(name)
        model.describe_command(name, "Something.")
        assert model.get_command(name).description == "Something."

    def test_overwrites_existing_description(self):
        model = _model()
        name = _name()
        model.add_command(name)
        model.describe_command(name, "First.")
        model.describe_command(name, "Revised.")
        assert model.get_command(name).description == "Revised."

    def test_does_not_mutate_the_original_value_object(self):
        """Command is frozen; describe_command must replace, not mutate."""
        model = _model()
        name = _name()
        original = model.add_command(name)
        model.describe_command(name, "New description.")
        assert original.description is None

    def test_raises_for_unknown_command(self):
        with pytest.raises(CommandNotFoundError) as exc_info:
            _model().describe_command(_name("Ghost"), "Doesn't matter.")
        assert exc_info.value.name == _name("Ghost")

    def test_not_found_error_message_contains_name(self):
        with pytest.raises(CommandNotFoundError, match="Ghost"):
            _model().describe_command(_name("Ghost"), "Doesn't matter.")

    def test_records_command_described_domain_event(self):
        model = _model()
        name = _name()
        model.add_command(name)
        model.collect_events()
        model.describe_command(name, "It was issued.")
        (recorded,) = model.collect_events()
        assert isinstance(recorded, CommandDescribed)
        assert recorded.command_name == name
        assert recorded.description == "It was issued."
        assert recorded.model_id == model.id


class TestGetCommand:
    def test_returns_the_stored_command(self):
        model = _model()
        name = _name("CancelOrder")
        model.add_command(name)
        assert model.get_command(name).name == name

    def test_raises_for_unknown_command(self):
        with pytest.raises(CommandNotFoundError):
            _model().get_command(_name("Ghost"))
