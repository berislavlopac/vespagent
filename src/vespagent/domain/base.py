"""Base hierarchy for the domain (CLAUDE.md §4, §7).

Every domain type builds on these: `DomainObject` (shared config) → `ValueObject`
(immutable, equality by value) and `Entity` (mutable, with identity and the ability to
record internal `DomainEvent`s). Entities must carry behaviour, never be anemic
(CLAUDE.md §7, §11). Kept separate from the aggregate packages so the parent classes have
one obvious home.
"""

from pydantic import BaseModel, ConfigDict, PrivateAttr


class DomainObject(BaseModel):
    """Shared base for every domain type in the event-storming vocabulary.

    Centralises model configuration so the whole domain behaves consistently; the
    value-object and entity bases below inherit and extend this config (Pydantic v2 merges
    `model_config` along the inheritance chain, so subclasses only state what they add).
    """

    model_config = ConfigDict(
        use_attribute_docstrings=True,
        extra="forbid",
    )
    """`use_attribute_docstrings` turns the string written under each field into that
    field's description — surfaced to humans *and*, via Pydantic AI, to the LLM as part of
    its output schema (CLAUDE.md §5, Layer 2). `extra="forbid"` makes a hallucinated extra
    key from a role fail validation loudly instead of being silently dropped."""


class ValueObject(DomainObject):
    """Base for value objects — immutable, with equality defined by their attributes.

    A value object has no identity of its own: two with equal attributes *are* the same
    value (Pydantic's field-based `__eq__` already gives us this). `frozen=True` makes them
    hashable and prevents in-place mutation, so they can be shared freely and only ever
    replaced wholesale.
    """

    model_config = ConfigDict(frozen=True)


class DomainEvent(ValueObject):
    """A real (messaging-sense) domain event raised by an `Entity`.

    Something significant that happened inside *our* application, raised so the application
    layer can react to it. Deliberately distinct from `ModeledEvent` — this is the §4
    naming collision made concrete: `DomainEvent` is an event in our own code, while
    `ModeledEvent` is an event the agent is modelling in the expert's domain. Concrete
    events subclass this and add their payload.
    """


class Entity(DomainObject):
    """Base for entities and aggregate roots — mutable, with a lifecycle and identity.

    Unlike a value object, an entity is defined by its identity rather than its attributes,
    and its state changes over time. Entities can record internal `DomainEvent`s as their
    behaviour runs; the application layer later collects (drains) them and decides on side
    effects, keeping the domain pure (CLAUDE.md §4, §7). Identity-based equality is added by
    each concrete entity once it has an id field.
    """

    _domain_events: list[DomainEvent] = PrivateAttr(default_factory=list)
    """Internal events raised but not yet collected. A `PrivateAttr` so it never appears in
    the entity's schema or serialisation — it is bookkeeping, not domain data."""

    def record_event(self, event: DomainEvent) -> None:
        """Record a domain event raised by this entity's behaviour.

        Called from inside the entity's own methods (e.g. when an aggregate root accepts a
        change), never by outside code reaching in.

        Args:
            event: The domain event to buffer until the next `collect_events` call.
        """
        self._domain_events.append(event)

    def collect_events(self) -> list[DomainEvent]:
        """Return the recorded domain events and clear the buffer.

        Drained by the application layer once a use case completes, so the same events are
        never dispatched twice.

        Returns:
            The events recorded since the last collection, in the order they were raised.
        """
        collected = list(self._domain_events)
        self._domain_events.clear()
        return collected

    @property
    def domain_events(self) -> tuple[DomainEvent, ...]:
        """The currently-recorded, not-yet-collected events, as an immutable read-only peek.

        Returns:
            The buffered events as a tuple; use `collect_events` to drain them.
        """
        return tuple(self._domain_events)
