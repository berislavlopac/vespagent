"""Domain events and their names, within the DomainModel aggregate (CLAUDE.md §4).

In event storming you start from the *domain events* — what happened, named in the past
tense (`OrderPlaced`) — and discover everything else by asking what caused them. These are
value objects: the mutable aggregate root (`DomainModel`) holds them and replaces them
wholesale on change.
"""

from pydantic import field_validator

from vespagent.domain.base import ValueObject


class EventName(ValueObject):
    """The past-tense name of a `ModeledEvent`, e.g. `OrderPlaced`.

    A type of its own rather than a bare `str`, so the type checker stops a name meant for
    one concept being passed where another belongs (avoiding primitive obsession).
    Validation is *structural only* — non-empty, trimmed; the past-tense convention is the
    Modeler's job and an eval assertion (CLAUDE.md §5 L3), not something code can reliably
    enforce.
    """

    value: str
    """The event name itself, e.g. `OrderPlaced`."""

    @field_validator("value")
    @classmethod
    def _require_non_blank(cls, value: str) -> str:  # noqa: F841
        """Strip surrounding whitespace and reject blank names.

        Args:
            value: The raw name supplied to the field.

        Returns:
            The trimmed name.

        Raises:
            ValueError: If the name is empty or only whitespace.
        """
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("event name must not be blank")
        return cleaned


class ModeledEvent(ValueObject):
    """A domain event in the event-storming sense, named in the past tense (`OrderPlaced`).

    Something noteworthy that happened in the domain. Called `ModeledEvent` rather than
    `DomainEvent` to avoid collision with the messaging-sense `DomainEvent` our own entities
    raise (CLAUDE.md §4). A *value object* with no identity of its own: within a
    `DomainModel` it is keyed by its `name`, and a change (e.g. supplying the description)
    replaces it wholesale rather than mutating it.
    """

    name: EventName
    """The event's past-tense name; its key within the owning `DomainModel`."""

    description: str | None = None
    """What the event means, in the expert's own words. `None` until explained — the model
    is a legitimately incomplete draft mid-interview, so a description is not required."""
