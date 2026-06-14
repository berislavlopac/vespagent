"""The DomainModel aggregate root (CLAUDE.md §4, §9 step 1).

`DomainModel` is the central evolving artifact of a VESPA session: it grows as the
Modeler extracts events, commands, actors, and other constructs from the interview
transcript. All mutations go through this root so invariants are enforced and
`DomainEvent`s are recorded for the application layer to act on.
"""

from uuid import UUID, uuid4

from pydantic import Field

from vespagent.domain.base import DomainEvent, Entity
from vespagent.domain.model.events import EventName, ModeledEvent
from vespagent.domain.model.exceptions import DuplicateEventError, EventNotFoundError


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


class DomainModel(Entity):
    """Aggregate root for an event-storming session's evolving domain model.

    Holds the growing collection of `ModeledEvent`s (and, later, commands, actors,
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
