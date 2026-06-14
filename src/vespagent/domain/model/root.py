"""The DomainModel aggregate root (CLAUDE.md §4, §9 step 1).

`DomainModel` is the central evolving artifact of a VESPA session: it grows as the
Modeler extracts events, commands, actors, and other constructs from the interview
transcript. All mutations go through this root so invariants are enforced and
`DomainEvent`s are recorded for the application layer to act on.
"""

from uuid import UUID, uuid4

from pydantic import Field

from vespagent.domain.base import DomainEvent, Entity
from vespagent.domain.model.commands import Command, CommandName
from vespagent.domain.model.events import EventName, ModeledEvent
from vespagent.domain.model.exceptions import (
    CommandNotFoundError,
    DuplicateCommandError,
    DuplicateEventError,
    EventNotFoundError,
)


class EventAdded(DomainEvent):
    """Raised when a new `ModeledEvent` is added to the model."""

    model_id: UUID
    """The id of the `DomainModel` that received the event."""

    event_name: EventName
    """The name of the newly-added event."""


class EventDescribed(DomainEvent):
    """Raised when a `ModeledEvent`'s description is set or updated."""

    model_id: UUID
    """The id of the owning `DomainModel`."""

    event_name: EventName
    """The event that was described."""

    description: str
    """The description that was applied."""


class CommandAdded(DomainEvent):
    """Raised when a new `Command` is added to the model."""

    model_id: UUID
    """The id of the `DomainModel` that received the command."""

    command_name: CommandName
    """The name of the newly-added command."""


class CommandDescribed(DomainEvent):
    """Raised when a `Command`'s description is set or updated."""

    model_id: UUID
    """The id of the owning `DomainModel`."""

    command_name: CommandName
    """The command that was described."""

    description: str
    """The description that was applied."""


class DomainModel(Entity):
    """Aggregate root for an event-storming session's evolving domain model.

    Holds the growing collections of `ModeledEvent`s, `Command`s (and, later, actors,
    aggregates, etc.) discovered during the interview. All mutations go through this
    root so invariants are enforced centrally and domain events are recorded.

    Identity is `id`; two `DomainModel` instances with the same `id` are the same
    model regardless of their current field values.
    """

    id: UUID = Field(default_factory=uuid4)
    """Stable identity, generated on creation and never changed."""

    subject: str
    """The domain area being mapped, e.g. `'order fulfilment'`. Free text supplied
    by the expert at the start of the session; not validated beyond non-blank."""

    events: dict[str, ModeledEvent] = Field(default_factory=dict)
    """Events discovered so far, keyed by name string for O(1) lookup. Mutated only
    through `add_event` and `describe_event` so invariants are always enforced."""

    commands: dict[str, Command] = Field(default_factory=dict)
    """Commands discovered so far, keyed by name string for O(1) lookup. Mutated only
    through `add_command` and `describe_command` so invariants are always enforced."""

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DomainModel):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def add_event(self, name: EventName) -> ModeledEvent:
        """Add a newly-discovered domain event to the model.

        Args:
            name: The past-tense event name, e.g. `OrderPlaced`.

        Returns:
            The new `ModeledEvent` (description is `None` until `describe_event` is called).

        Raises:
            DuplicateEventError: If an event with that name already exists.
        """
        if name.value in self.events:
            raise DuplicateEventError(name)
        event = ModeledEvent(name=name)
        self.events[name.value] = event
        self.record_event(EventAdded(model_id=self.id, event_name=name))
        return event

    def describe_event(self, name: EventName, description: str) -> ModeledEvent:
        """Set or update the description of an existing event.

        Args:
            name: The event to describe.
            description: The expert's explanation, in their own words.

        Returns:
            The updated `ModeledEvent`.

        Raises:
            EventNotFoundError: If no event with that name exists.
        """
        if name.value not in self.events:
            raise EventNotFoundError(name)
        updated = self.events[name.value].model_copy(update={"description": description})
        self.events[name.value] = updated
        self.record_event(
            EventDescribed(model_id=self.id, event_name=name, description=description)
        )
        return updated

    def get_event(self, name: EventName) -> ModeledEvent:
        """Retrieve an event by name.

        Args:
            name: The event name to look up.

        Returns:
            The matching `ModeledEvent`.

        Raises:
            EventNotFoundError: If no event with that name exists.
        """
        if name.value not in self.events:
            raise EventNotFoundError(name)
        return self.events[name.value]

    @property
    def event_count(self) -> int:
        """The number of events discovered so far."""
        return len(self.events)

    def add_command(self, name: CommandName) -> Command:
        """Add a newly-discovered command to the model.

        Args:
            name: The imperative-form command name, e.g. `PlaceOrder`.

        Returns:
            The new `Command` (description is `None` until `describe_command` is called).

        Raises:
            DuplicateCommandError: If a command with that name already exists.
        """
        if name.value in self.commands:
            raise DuplicateCommandError(name)
        command = Command(name=name)
        self.commands[name.value] = command
        self.record_event(CommandAdded(model_id=self.id, command_name=name))
        return command

    def describe_command(self, name: CommandName, description: str) -> Command:
        """Set or update the description of an existing command.

        Args:
            name: The command to describe.
            description: The expert's explanation, in their own words.

        Returns:
            The updated `Command`.

        Raises:
            CommandNotFoundError: If no command with that name exists.
        """
        if name.value not in self.commands:
            raise CommandNotFoundError(name)
        updated = self.commands[name.value].model_copy(update={"description": description})
        self.commands[name.value] = updated
        self.record_event(
            CommandDescribed(model_id=self.id, command_name=name, description=description)
        )
        return updated

    def get_command(self, name: CommandName) -> Command:
        """Retrieve a command by name.

        Args:
            name: The command name to look up.

        Returns:
            The matching `Command`.

        Raises:
            CommandNotFoundError: If no command with that name exists.
        """
        if name.value not in self.commands:
            raise CommandNotFoundError(name)
        return self.commands[name.value]

    @property
    def command_count(self) -> int:
        """The number of commands discovered so far."""
        return len(self.commands)
